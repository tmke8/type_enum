import functools
from operator import or_
from types import new_class
from typing import (
    Any,
    Generic,
    Iterator,
    NamedTuple,
    TypeAlias,
    TypeVar,
    TypeVarTuple,
    Union,
    Unpack,
    get_args,
    get_origin,
    get_type_hints,
)

from ._utils import is_dunder, type_to_str

__all__ = ["Field", "TypeEnum"]


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
            if get_origin(inner) is not tuple:
                raise TypeError(
                    f"Expected type annotation for '{attr_name}' to be a Type[Tuple[...]], "
                    f"but found '{wrapped_types}'"
                )
            types = get_args(inner)
            if len(types) == 1 and types[0] == ():
                types = ()
            # subtype = _create_tuple_class(name, attr_name, types)
            typevars: tuple[type, ...] = tuple(
                typ for typ in types if isinstance(typ, TypeVar)
            )
            subtype = _create_subclass(
                name, attr_name, types, typevars, ns["__module__"]
            )

            ns[attr_name] = subtype
            member_map[attr_name] = Entry(subtype, typevars)

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


def _create_subclass(
    basename: str,
    typename: str,
    types: tuple[type, ...],
    typevars: tuple[type, ...],
    module: str,
) -> type:
    def body(namespace: dict[str, Any]) -> None:
        namespace["__module__"] = module
        namespace["__annotations__"] = {f"field{i}": typ for i, typ in enumerate(types)}
        num_values = len(types)
        repr_fmt = "(" + ", ".join("%r" for _ in range(num_values)) + ")"

        def __repr__(self) -> str:
            "Return a nicely formatted representation string"
            return basename + "." + self.__class__.__name__ + repr_fmt % tuple(self)

        namespace["__repr__"] = __repr__

    baseclasses = (NamedTuple,)
    if typevars:
        baseclasses += (Generic[*typevars],)
    subtype = new_class(typename, baseclasses, exec_body=body)
    subtype.__doc__ = (
        f"{basename}.{typename}(" + ", ".join(type_to_str(typ) for typ in types) + ")"
    )
    return subtype


class TypeEnum(metaclass=TypeEnumMeta):
    T: Any

    def __init_subclass__(cls, *args: Any, **kwargs: Any):
        super().__init_subclass__(*args, **kwargs)


_Ts = TypeVarTuple("_Ts")

Field: TypeAlias = type[tuple[Unpack[_Ts]]]
