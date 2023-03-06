from dataclasses import dataclass
from functools import cached_property
from typing import Callable

from mypy.exprtotype import TypeTranslationError, expr_to_unanalyzed_type
from mypy.nodes import (
    AssignmentStmt,
    ClassDef,
    DictExpr,
    Expression,
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
from mypy.types import AnyType, Type, TypeOfAny, UnboundType

__all__ = ["plugin"]


@dataclass(kw_only=True)
class TypeEnumTransform:
    cls: ClassDef
    # Statement must also be accepted since class definition itself may be passed as the reason
    # for subclass/metaclass-based uses of `typing.dataclass_transform`
    reason: Expression | Statement
    # spec: DataclassTransformSpec
    api: SemanticAnalyzerPluginInterface

    def transform(self) -> None:
        """Transform the attributes in a TypeEnum."""
        cls = self.cls
        for stmt in cls.defs.body:
            # Any assignment that doesn't use the new type declaration
            # syntax can be ignored out of hand.
            if not (isinstance(stmt, AssignmentStmt)):
                continue
            elif stmt.new_syntax:
                self.api.fail("No type annotations allowed in TypeEnum", stmt)
                continue

            # a: int, b: str = 1, 'foo' is not supported syntax so we
            # don't have to worry about it.
            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                self.api.fail("No multiple assignments allowed in TypeEnum", stmt)
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
                # Skip processing this node. This doesn't match the runtime behaviour,
                # but the only alternative would be to modify the SymbolTable,
                # and it's a little hairy to do that in a plugin.
                continue

            assert isinstance(node, Var)

            # x: ClassVar[int] is ignored by dataclasses.
            if node.is_classvar:
                self.api.fail("No ClassVars in TypeEnum.", node)
                continue

            # All other assignments are already type checked.
            if isinstance(stmt.rvalue, TempNode):
                self.api.fail("All variables need values.", stmt)
                continue

            if isinstance(stmt.rvalue, TupleExpr):
                types: list[Type] = []
                aborted = False
                # tvar_defs = self.api.get_and_bind_all_tvars(stmt.rvalue.items)
                for type_node in stmt.rvalue.items:
                    analyzed = self.get_type_from_expression(type_node)
                    if analyzed is None:
                        aborted = True
                        break
                    types.append(analyzed)
                if aborted:
                    continue
                self.create_namedtuple(
                    lhs.name, [f"_{i}" for i in range(len(types))], types, stmt.line
                )
            elif isinstance(stmt.rvalue, DictExpr):
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

                self.create_namedtuple(lhs.name, fieldnames, fieldtypes, stmt.line)
            else:
                self.api.fail(f"Only tuples or dicts are allowed in a TypeEnum", stmt)

            # current_attr_names.add(lhs.name)
            # found_attrs[lhs.name] = TypeEnumEntry(
            #     name=lhs.name,
            #     line=stmt.line,
            #     column=stmt.column,
            #     value=stmt.rvalue,
            #     info=cls.info,
            # )

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
    ) -> None:
        info = self.namedtuple_builder.build_namedtuple_typeinfo(
            # name=f"{name}@{basename}",
            name=name,
            items=fieldnames,
            types=types,
            default_items={},
            line=line,
            existing_info=None,
        )
        node = SymbolTableNode(MDEF, info)
        self.api.add_symbol_table_node(name, node)

    @cached_property
    def namedtuple_builder(self) -> NamedTupleAnalyzer:
        return NamedTupleAnalyzer(self.api.options, self.api)  # type: ignore


@dataclass
class TypeEnumEntry:
    name: str
    line: int
    column: int
    value: Expression
    info: TypeInfo


class TypeEnumPlugin(Plugin):
    def get_base_class_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        # if fullname == "type_enum.TypeEnum":
        if fullname == "type_enum._core.TypeEnum":
            return type_enum_callback


def type_enum_callback(ctx: ClassDefContext) -> None:
    transform = TypeEnumTransform(cls=ctx.cls, reason=ctx.reason, api=ctx.api)
    transform.transform()


def plugin(version: str) -> type[TypeEnumPlugin]:
    # ignore version argument if the plugin works with all mypy versions.
    return TypeEnumPlugin
