from typing import Generic, TypeVar
from typing_extensions import assert_type

from type_enum import TypeEnum

from .common import CustomTestCase


class InstantiationTest(CustomTestCase):
    def test_num_args(self) -> None:
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

        with self.assertRaises(TypeError):
            T.A()  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            T.C(0)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            T.B("foo")  # type: ignore[call-arg,arg-type]

    def test_field_name(self) -> None:
        class T(TypeEnum):
            A = {"x": int, "y": str}
            B = {"val": bool}
            C = {}  # type: ignore[var-annotated]

        T.A(x=3, y="foo")
        T.A(3, y="foo")
        T.A(3, "foo")
        T.B(False)
        T.C()

        with self.assertRaises(TypeError):
            T.A()  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            T.C(0)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            T.B("foo", 3)  # type: ignore[call-arg,arg-type]

    def test_generic(self) -> None:
        U = TypeVar("U")

        class T(TypeEnum, Generic[U]):
            A = (U,)  # type: ignore[misc]
            B = (int, str)
            C = ()

        T[int]
        a = T[int].A(3)  # type: ignore[arg-type]
        assert_type(a[0], int)  # type: ignore[assert-type]

    def test_invalid_body(self) -> None:
        with self.assertRaises(TypeError):

            class T(TypeEnum):
                A = 0  # type: ignore[misc]

        with self.assertRaises(TypeError):

            class U(TypeEnum):
                def f(self) -> int:
                    return 0

    def test_invalid_baseclass(self) -> None:
        with self.assertRaises(TypeError):

            class T(TypeEnum, int):
                pass

    def test_invalid_inheritance(self) -> None:
        class T(TypeEnum):
            A = ()

        with self.assertRaises(TypeError):

            class U(T):  # type: ignore[misc]
                B = ()

    def test_instantiate_type_enum(self) -> None:
        class T(TypeEnum):
            A = (int,)

        with self.assertRaises(TypeError):
            T()
        with self.assertRaises(TypeError):
            TypeEnum()

    def test_name_clash(self) -> None:
        with self.assertRaises(TypeError):

            class T(TypeEnum):
                A = {"B": int}
                B = (int, str)
