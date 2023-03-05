from operator import itemgetter
import sys
from typing import Any, Iterator, NamedTuple

from type_enum.utils import is_dunder, type_to_str

__all__ = ["TypeEnum"]

try:
    from collections import _tuplegetter  # undocumented implementation in C
except ImportError:

    def _tuplegetter(index: int, doc: str) -> property:
        return property(itemgetter(index), doc=doc)


class TypeEnumMeta(type):
    """Metaclass for TypeEnum."""

    def __new__(metacls, cls: str, bases: tuple[type, ...], classdict: dict[str, Any]):
        member_map: dict[str, type] = {}
        for name in classdict:
            if is_dunder(name):
                continue
            types = classdict[name]
            if isinstance(types, tuple):
                subtype = _create_tuple_class(cls, name, types)
            elif isinstance(types, dict):
                subtype = NamedTuple(name, [(k, v) for k, v in types.items()])
            else:
                raise TypeError(
                    "A TypeEnum may only contain variables of tuples or dictionaries."
                )
            classdict[name] = subtype
            member_map[name] = subtype
        classdict["_member_map"] = member_map
        try:
            exc = None
            enum_class = super().__new__(metacls, cls, bases, classdict)
        except RuntimeError as e:
            # any exceptions raised by member.__new__ will get converted to a
            # RuntimeError, so get that original exception back and raise it instead
            exc = e.__cause__ or e
        if exc is not None:
            raise exc
        return enum_class

    def __subclasscheck__(cls, subclass: type) -> bool:
        return subclass in cls._member_map.values()

    def __instancecheck__(cls, instance: object) -> bool:
        return any(isinstance(instance, typ) for typ in cls._member_map.values())

    def __iter__(cls) -> Iterator[type]:
        return cls._member_map.values()


def _create_tuple_class(basename: str, typename: str, types: tuple[type, ...]) -> type:
    """Create a new subclass of ``tuple``."""
    num_values = len(types)
    _tuple = tuple

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
    return type(typename, (tuple,), class_namespace)


class TypeEnum(metaclass=TypeEnumMeta):
    pass
