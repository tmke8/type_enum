from dataclasses import dataclass
from functools import cached_property
from typing import Callable

from mypy.exprtotype import TypeTranslationError, expr_to_unanalyzed_type
from mypy.nodes import (
    AssignmentStmt,
    ClassDef,
    DictExpr,
    Expression,
    FuncDef,
    MDEF,
    NameExpr,
    PlaceholderNode,
    Statement,
    StrExpr,
    SymbolTableNode,
    TempNode,
    TupleExpr,
    TypeAlias,
    TypeInfo,
    Var,
)
from mypy.plugin import ClassDefContext, Plugin, SemanticAnalyzerPluginInterface
from mypy.semanal_namedtuple import NamedTupleAnalyzer
from mypy.types import (
    AnyType,
    Instance,
    ProperType,
    TupleType,
    Type,
    TypeOfAny,
    TypeType,
    TypeVarLikeType,
    UnboundType,
    UnionType,
    get_proper_type,
)

__all__ = ["plugin"]


@dataclass(kw_only=True)
class TypeEnumTransform:
    cls: ClassDef
    # Statement must also be accepted since class definition itself may be passed as the
    # reason for subclass/metaclass-based uses of `typing.dataclass_transform`
    reason: Expression | Statement
    # spec: DataclassTransformSpec
    api: SemanticAnalyzerPluginInterface

    def transform(self) -> None:
        """Transform the attributes in a TypeEnum."""
        cls = self.cls
        cls.info.is_final = True
        variants: list[tuple[TypeInfo, list[TypeVarLikeType]]] = []
        error_reported = False

        if len(cls.info.bases) > 1:
            self.api.fail(
                "No other base classes allowed in TypeEnum except 'Generic'", cls
            )

        # if len(cls.info.type_vars) > 0:
        #     self.api.fail("no type vars", cls)

        for stmt in cls.defs.body:
            # Any assignment that doesn't use the new type declaration
            # syntax can be ignored out of hand.
            if not (isinstance(stmt, AssignmentStmt)):
                if isinstance(stmt, FuncDef):
                    self.api.fail("No function definitions allowed in TypeEnum", stmt)
                    error_reported = True
                continue

            # a: int, b: str = 1, 'foo' is not supported syntax so we
            # don't have to worry about it.
            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                self.api.fail("No multiple assignments allowed in TypeEnum", stmt)
                error_reported = True
                continue

            sym = cls.info.names.get(lhs.name)
            if sym is None:
                # There was probably a semantic analysis error.
                continue

            node = sym.node
            assert not isinstance(node, PlaceholderNode)

            if isinstance(node, TypeAlias):
                self.api.fail(
                    ("Type aliases inside TypeEnum are not supported at runtime"),
                    node,
                )
                error_reported = True
                continue

            if isinstance(node, TypeInfo):
                # we'll assume that this has already been analyzed
                variants.append((node, node.defn.type_vars))
                continue

            assert isinstance(node, Var), type(node)

            if node.is_classvar:
                self.api.fail("No ClassVars in TypeEnum.", node)
                error_reported = True
                continue

            if stmt.new_syntax:
                if not isinstance(stmt.rvalue, TempNode):
                    self.api.fail(
                        "No type annotations allowed in the assignment style", stmt
                    )
                    error_reported = True
                    continue

                typ = stmt.type

                if typ is not None:
                    typ = self.api.anal_type(typ)
                    if typ is None:
                        self.api.defer()  # type is not ready -- we defer
                        return
                    typ = get_proper_type(typ)  # resolve type aliases

                if isinstance(typ, TypeType) and isinstance(tup := typ.item, TupleType):
                    types: list[Type] = tup.items
                    tvars = [
                        tvar for tvar in types if isinstance(tvar, TypeVarLikeType)
                    ]
                    info = self.create_namedtuple(
                        lhs.name, [f"_{i}" for i in range(len(types))], types, stmt.line
                    )
                    if tvars:
                        info.type_vars = []
                        info.defn.type_vars = tvars
                        info.add_type_vars()
                        assert info.special_alias is not None
                        info.special_alias.alias_tvars = list(tvars)
                        target = info.special_alias.target
                        assert isinstance(target, ProperType)
                        if isinstance(target, TupleType):
                            target.partial_fallback.args = tuple(tvars)

                    variants.append((info, tvars))
                    continue
                else:
                    self.api.fail(f"Invalid field definition: '{lhs.name}'", stmt)
                    error_reported = True
                    continue

            if isinstance(stmt.rvalue, TupleExpr):
                types: list[Type] = []
                aborted = False
                tvars: list[TypeVarLikeType] = []
                # tvar_defs = self.get_and_bind_all_tvars(stmt.rvalue.items)
                for type_node in stmt.rvalue.items:
                    analyzed = self.get_type_from_expression(type_node)
                    if isinstance(analyzed, TypeVarLikeType):
                        # analyzed = AnyType(TypeOfAny.implementation_artifact)
                        tvars.append(analyzed)
                    if analyzed is None:
                        aborted = True
                        break
                    types.append(analyzed)
                if aborted:
                    continue
                info = self.create_namedtuple(
                    lhs.name, [f"field{i}" for i in range(len(types))], types, stmt.line
                )
                if tvars:
                    info.type_vars = []
                    info.defn.type_vars = tvars
                    info.add_type_vars()
                variants.append((info, tvars))
            elif isinstance(stmt.rvalue, DictExpr):
                if not stmt.rvalue.items:
                    self.api.fail("Dictionaries in a TypeEnum may not be empty", stmt)
                    error_reported = True
                    continue
                fieldnames: list[str] = []
                fieldtypes: list[Type] = []
                aborted = False
                for key, type_node in stmt.rvalue.items:
                    if isinstance(key, StrExpr):
                        fieldnames.append(key.value)
                    else:
                        self.api.fail(
                            "Dictionary keys in a TypeEnum must be strings", stmt
                        )
                        aborted = True
                        break
                    analyzed = self.get_type_from_expression(type_node)
                    if analyzed is None:
                        aborted = True
                        break
                    fieldtypes.append(analyzed)
                if aborted:
                    continue

                info = self.create_namedtuple(
                    lhs.name, fieldnames, fieldtypes, stmt.line
                )
                variants.append((info, []))
            else:
                self.api.fail("Only tuples or dicts are allowed in a TypeEnum", stmt)
                error_reported = True

        if not variants and not error_reported:
            self.api.fail("Empty TypeEnum.", self.cls)

        # NOTE: previously, I had to guard the following,
        # but somehow this became unnecessary

        # existing = self.api.lookup_qualified("T", self.cls)
        # if (
        #     existing is None
        #     or existing.node is None
        #     or not isinstance(existing.node, TypeAlias)
        # ):
        if True:
            typ = UnionType.make_union(
                [Instance(typ, type_vars, typ.line) for typ, type_vars in variants]
            )
            alias = TypeAlias(
                typ,
                self.api.qualified_name("T"),
                self.reason.line,
                self.reason.column,
                alias_tvars=cls.info.defn.type_vars,
            )
            aliasnode = SymbolTableNode(MDEF, alias)
            self.api.add_symbol_table_node("T", aliasnode)

    def get_type_from_expression(self, type_node: Expression) -> Type | None:
        try:
            type = expr_to_unanalyzed_type(
                type_node, self.api.options, self.api.is_stub_file
            )
        except TypeTranslationError:
            self.api.fail(f"Invalid field type", type_node)
            return None
        analyzed = self.api.anal_type(type)
        if isinstance(analyzed, UnboundType):
            analyzed = AnyType(TypeOfAny.from_error)
        return analyzed

    def create_namedtuple(
        self,
        name: str,
        fieldnames: list[str],
        types: list[Type],
        line: int,
        # basename: str,
    ) -> TypeInfo:
        info = self.namedtuple_builder.build_namedtuple_typeinfo(
            # name=f"{name}@{basename}",
            name=name,
            items=fieldnames,
            types=types,
            default_items={},
            line=line,
            existing_info=None,
        )
        info.is_final = True

        # add the surrounding class as a base class
        info.mro.append(self.cls.info)

        node = SymbolTableNode(MDEF, info)
        self.api.add_symbol_table_node(name, node)
        return info

    @cached_property
    def namedtuple_builder(self) -> NamedTupleAnalyzer:
        return NamedTupleAnalyzer(self.api.options, self.api)  # type: ignore


class TypeEnumPlugin(Plugin):
    def get_base_class_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        if fullname == "type_enum._core.TypeEnum":
            return type_enum_callback


def type_enum_callback(ctx: ClassDefContext) -> None:
    transform = TypeEnumTransform(cls=ctx.cls, reason=ctx.reason, api=ctx.api)
    transform.transform()


def plugin(version: str) -> type[TypeEnumPlugin]:
    # ignore version argument if the plugin works with all mypy versions.
    parsed = parse_mypy_version(version)
    if parsed < (1, 5):
        raise RuntimeError("type-enum-plugin requires mypy >= 1.5.0")
    return TypeEnumPlugin


def parse_mypy_version(version: str) -> tuple[int, ...]:
    """Parse mypy string version to tuple of ints.

    This function is included here rather than the mypy plugin file because the mypy
    plugin file cannot be imported outside a mypy run.

    It parses normal version like `0.930` and dev version
    like `0.940+dev.04cac4b5d911c4f9529e6ce86a27b44f28846f5d.dirty`.

    Args:
        version: The mypy version string.

    Returns:
        A tuple of ints. e.g. (0, 930).
    """
    return tuple(map(int, version.partition("+")[0].split(".")))
