from typing import Literal, Union

from type_enum import TypeEnum


def test_repr() -> None:
    class T(TypeEnum):
        A = (int,)
        B = (int, str)
        C = ()
        D = {"x": int, "y": str}
        E = {"val": bool}
        F = {}  # type: ignore[var-annotated]

    assert repr(T.A(3)) == "T.A(3)"
    assert repr(T.B(0, "foo")) == "T.B(0, 'foo')"
    assert repr(T.C()) == "T.C()"
    assert repr(T.D(3, "bar")) == "D(x=3, y='bar')"
    assert repr(T.E(True)) == "E(val=True)"
    assert repr(T.F()) == "F()"


def test_docstring() -> None:
    class T(TypeEnum):
        A = (Union[Literal[1], dict[int, list[str]]],)

    assert T.A.__doc__ == "T.A(Union[int, dict[int, list[str]]])"
