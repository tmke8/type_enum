from typing import Generic, TypeVar
from typing_extensions import assert_type
import pytest

from type_enum import TypeEnum


def test_num_args() -> None:
    class T(TypeEnum):
        A = (int,)
        B = (int, str)
        C = ()

    a = T.A(3)
    assert_type(a[0], int)
    b = T.B(0, "foo")
    assert_type(b[0], int)
    assert_type(b[1], str)
    T.C()

    with pytest.raises(TypeError):
        T.A()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        T.C(0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        T.B("foo")  # type: ignore[call-arg,arg-type]


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
        T.A()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        T.C(0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        T.B("foo", 3)  # type: ignore[call-arg,arg-type]


def test_generic() -> None:
    U = TypeVar("U")

    class T(TypeEnum, Generic[U]):
        A = (U,)
        B = (int, str)
        C = ()

    T[int]
    a = T[int].A(3)
    assert_type(a[0], int)


def test_invalid_body() -> None:
    with pytest.raises(TypeError):

        class T(TypeEnum):
            A = 0  # type: ignore[misc]

    with pytest.raises(TypeError):

        class U(TypeEnum):
            def f(self) -> int:
                return 0
