from types import NoneType, UnionType
from typing import Any, Literal, Union, get_args, get_origin


def type_to_str(type_: Any) -> str:
    """Convert a type to a nice string."""
    is_optional, type_ = _resolve_optional(type_)
    if type_ is None:
        return type(type_).__name__
    if type_ is Any:
        return "Any"
    if type_ is ...:
        return "..."

    if _is_literal_type(type_):
        type_ = _resolve_literal(type_)

    if hasattr(type_, "__name__"):
        name = str(type_.__name__)
    elif type_._name is None and (get_origin(type_) is not None):
        name = type_to_str(type_.__origin__)
    else:
        name = str(type_._name)

    args = get_args(type_) if hasattr(type_, "__args__") else None
    if args is None:
        ret = name
    elif name == "Callable":
        in_args_str = ", ".join(type_to_str(inner_type) for inner_type in args[0])
        out_args_str = type_to_str(args[1])
        ret = f"{name}[[{in_args_str}], {out_args_str}]"
    else:
        args_str = ", ".join(type_to_str(inner_type) for inner_type in (list(args)))
        ret = f"{name}[{args_str}]"
    if is_optional:
        return f"Optional[{ret}]"
    else:
        return ret


def _resolve_optional(type_: Any) -> tuple[bool, Any]:
    """Check whether `type_` is equivalent to `typing.Optional[T]` for some T."""
    if _is_union_type(type_):
        args = get_args(type_)
        if NoneType in args:
            optional = True
            args = tuple(a for a in args if a is not NoneType)
        else:
            optional = False
        if len(args) == 1:
            return optional, args[0]
        elif len(args) >= 2:
            return optional, Union[args]
        else:
            assert False

    if type_ is Any:
        return True, Any

    if type_ in (None, NoneType):
        return True, NoneType

    return False, type_


def _is_union_type(tp: type) -> bool:
    return tp is Union or get_origin(tp) is Union or isinstance(tp, UnionType)


def _is_literal_type(tp: type) -> bool:
    return tp is Literal or get_origin(tp) is Literal


def _resolve_literal(type_: type) -> type:
    values = get_args(type_)
    assert values
    value_types = set(type(value) for value in values)
    if len(value_types) == 1:
        return value_types.pop()
    # Constructing a Union type dynamically using a tuple is perfectly valid.
    return Union[tuple(value_types)]  # type: ignore


def is_dunder(name: str) -> bool:
    """
    Returns True if a __dunder__ name, False otherwise.
    """
    return (
        len(name) > 4
        and name[:2] == name[-2:] == "__"
        and name[2] != "_"
        and name[-3] != "_"
    )
