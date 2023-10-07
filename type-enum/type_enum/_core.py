import functools
from operator import itemgetter, or_
from re import sub
import sys
from typing import (
    Any,
    Generic,
    Iterator,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from typing_extensions import NamedTuple, TypeVarTuple, Unpack

from ._utils import is_dunder, type_to_str

__all__ = ["Field", "TypeEnum"]

try:
    from collections import _tuplegetter  # undocumented implementation in C
except ImportError:

    def _tuplegetter(index: int, doc: str) -> property:
        return property(itemgetter(index), doc=doc)


class Entry(NamedTuple):
    typ: type
    typevars: tuple[type, ...]


class TypeEnumMeta(type):
    """Metaclass for TypeEnum."""

    def __new__(cls, name: str, bases: tuple[type, ...], ns: dict[str, Any]):
        for base in bases:
            if base is not TypeEnum and base is not Generic:
                raise TypeError(
                    "TypeEnum classes cannot be subclassed further "
                    "and may only have Generic as an additional base class"
                )
        member_map: dict[str, Entry] = {}
        cls.__annotations__ = ns.get("__annotations__", {})
        typ_anns = get_type_hints(cls, localns=ns)
        for attr_name in typ_anns:
            if is_dunder(attr_name):
                continue
            if attr_name == "T":
                continue
            # types = ns[attr_name]
            wrapped_types = typ_anns[attr_name]
            if get_origin(wrapped_types) is not type:
                raise TypeError(
                    f"Expected type annotation for '{attr_name}' to be a Type[Tuple[...]], "
                    f"but found '{wrapped_types}'"
                )
            inner = get_args(wrapped_types)[0]
            if len(inner) == 1 and inner[0] == ():
                inner = ()
            if get_origin(inner) is not tuple:
                raise TypeError(
                    f"Expected type annotation for '{attr_name}' to be a Type[Tuple[...]], "
                    f"but found '{wrapped_types}'"
                )
            types = get_args(inner)
            # subtype = _create_tuple_class(name, attr_name, types)
            subtype = _create_subclass(name, attr_name, types)
            # elif isinstance(types, dict):
            #     if not types:
            #         raise TypeError(
            #             f"Dictionaries in TypeEnum may not be empty. Found empty '{attr_name}' in '{name}'."
            #         )
            #     for k in types:
            #         if k in ns:
            #             raise TypeError(
            #                 f"'{k}' appears in namespace and in '{attr_name}'"
            #             )
            #     subtype = NamedTuple(attr_name, [(k, v) for k, v in types.items()])
            # else:
            #     raise TypeError(
            #         "A TypeEnum may only contain variables of tuples or dictionaries."
            #     )
            ns[attr_name] = subtype
            member_map[attr_name] = Entry(
                subtype, tuple(typ for typ in types if isinstance(typ, TypeVar))
            )

        for attr_name in ns:
            if not is_dunder(attr_name) and attr_name not in typ_anns:
                raise TypeError(
                    f"A TypeEnum may only contain fields: `{attr_name}` is not a field."
                )

        if not member_map and name != "TypeEnum":
            raise TypeError(f"Empty TypeEnum.")

        for subtype, _ in member_map.values():
            for subname_, (subtype_, _) in member_map.items():
                setattr(subtype, subname_, subtype_)
        ns["_member_map"] = member_map

        def _init(self, *args: Any, **kwargs: Any) -> None:
            raise TypeError("TypeEnum cannot be instantiated")

        ns["__init__"] = _init
        if name != "TypeEnum":
            subtypes = [
                (typ.__class_getitem__(typevars) if typevars else typ)
                for typ, typevars in member_map.values()
            ]
            ns["T"] = functools.reduce(or_, subtypes[1:], Union[subtypes[0]])
        try:
            exc = None
            enum_class = super().__new__(cls, name, bases, ns)
        except RuntimeError as e:
            # any exceptions raised by member.__new__ will get converted to a
            # RuntimeError, so get that original exception back and raise it instead
            exc = e.__cause__ or e
        if exc is not None:
            raise exc
        return enum_class

    def __subclasscheck__(cls, subclass: type) -> bool:
        return any(subclass == typ for typ, _ in cls._member_map.values())

    def __instancecheck__(cls, instance: object) -> bool:
        return any(isinstance(instance, typ) for typ, _ in cls._member_map.values())

    def __iter__(cls) -> Iterator[type]:
        return (typ for typ, _ in cls._member_map.values())


def _create_subclass(basename: str, typename: str, types: tuple[type, ...]):
    subtype = NamedTuple(typename, [(f"field{i}", typ) for i, typ in enumerate(types)])
    subtype.__doc__ = (
        f"{basename}.{typename}(" + ", ".join(type_to_str(typ) for typ in types) + ")"
    )
    num_values = len(types)
    repr_fmt = "(" + ", ".join("%r" for _ in range(num_values)) + ")"

    def __repr__(self) -> str:
        "Return a nicely formatted representation string"
        return basename + "." + self.__class__.__name__ + repr_fmt % tuple(self)

    subtype.__repr__ = __repr__
    return subtype


def _create_tuple_class(basename: str, typename: str, types: tuple[type, ...]) -> type:
    """Create a new subclass of ``tuple``."""
    num_values = len(types)
    _tuple: type = tuple

    # ==================== methods for the new class ====================
    def __new__(cls, *args: type) -> tuple:
        if (num_args := len(args)) != num_values:
            raise TypeError(
                f"{typename}.__new__() takes {num_values} positional arguments but {num_args} were given"
            )
        return _tuple.__new__(cls, args)

    __new__.__doc__ = f"Create a new instance of {basename}.{typename}."

    repr_fmt = "(" + ", ".join("%r" for _ in range(num_values)) + ")"

    def __repr__(self) -> str:
        "Return a nicely formatted representation string"
        return basename + "." + self.__class__.__name__ + repr_fmt % self

    def __getnewargs__(self) -> tuple:
        "Return self as a plain tuple.  Used by copy and pickle."
        return _tuple(self)

    # ==================== fix `__qualname__` ====================
    for method in (__new__, __repr__, __getnewargs__):
        method.__qualname__ = f"{typename}.{method.__name__}"

    # ==================== construct the namespace of the class ====================
    field_names = tuple(f"_{i}" for i in range(num_values))

    class_namespace: dict[str, Any] = {
        "__doc__": f"{basename}.{typename}("
        + ", ".join(type_to_str(typ) for typ in types)
        + ")",
        "__slots__": (),
        "__new__": __new__,
        "__repr__": __repr__,
        "__getnewargs__": __getnewargs__,
        "__match_args__": field_names,
    }

    # ==================== add aliases for the tuple fields ====================
    # this is needed for pattern matching
    for index, name in enumerate(field_names):
        doc = sys.intern(f"Alias for field number {index}")
        class_namespace[name] = _tuplegetter(index, doc)
    return type(typename, (_tuple,), class_namespace)


class TypeEnum(metaclass=TypeEnumMeta):
    T: Any

    def __init_subclass__(cls, *args: Any, **kwargs: Any):
        super().__init_subclass__(*args, **kwargs)


_Ts = TypeVarTuple("_Ts")

Field: TypeAlias = Type[Tuple[Unpack[_Ts]]]
