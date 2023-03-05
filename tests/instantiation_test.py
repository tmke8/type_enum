from typing import Generic, TypeVar
import pytest

from type_enum import TypeEnum


def test_num_args() -> None:
    class T(TypeEnum):
        A = (int,)
        B = (int, str)
        C = ()

    T.A(3)
    T.B(0, "foo")
    T.C()

    with pytest.raises(TypeError):
        T.A()
    with pytest.raises(TypeError):
        T.C(0)
    with pytest.raises(TypeError):
        T.B("foo")


def test_field_name() -> None:
    class T(TypeEnum):
        A = {"x": int, "y": str}
        B = {"val": bool}
        C = {}

    T.A(x=3, y="foo")
    T.A(3, y="foo")
    T.A(3, "foo")
    T.B(False)
    T.C()

    with pytest.raises(TypeError):
        T.A()
    with pytest.raises(TypeError):
        T.C(0)
    with pytest.raises(TypeError):
        T.B("foo", 3)


def test_generic() -> None:
    U = TypeVar("U")

    class T(TypeEnum, Generic[U]):
        A = (int,)
        B = (int, str)
        C = ()

    T[int]
    T[int].A(3)


def test_invalid_body() -> None:
    with pytest.raises(TypeError):
        class T(TypeEnum):
            A = 0

    with pytest.raises(TypeError):
        class U(TypeEnum):
            def f(self) -> int:
                return 0
