from typing import Generic, TypeVar
from typing_extensions import assert_type

from type_enum import TypeEnum

from .common import CustomTestCase


class InstantiationTest(CustomTestCase):
    def test_num_args(self) -> None:
        class E(TypeEnum):
            A = (int,)
            B = (int, str)
            C = ()

        a = E.A(3)
        assert_type(a[0], int)
        b = E.B(0, "foo")
        assert_type(b[0], int)
        assert_type(b[1], str)
        E.C()

        with self.assertRaises(TypeError):
            E.A()  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            E.C(0)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            E.B("foo")  # type: ignore[call-arg,arg-type]

    def test_field_name(self) -> None:
        class E(TypeEnum):
            A = {"x": int, "y": str}
            B = {"val": bool}
            C = ()

        E.A(x=3, y="foo")
        E.A(3, y="foo")
        E.A(3, "foo")
        E.B(False)
        E.C()

        with self.assertRaises(TypeError):
            E.A()  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            E.C(0)  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            E.B("foo", 3)  # type: ignore[call-arg,arg-type]

    def test_generic(self) -> None:
        U = TypeVar("U")

        class E(TypeEnum, Generic[U]):
            A = (U,)  # type: ignore[misc]
            B = (int, str)
            C = ()

        E[int]
        a = E[int].A(3)  # type: ignore[arg-type]
        assert_type(a[0], int)  # type: ignore[assert-type]

    def test_invalid_body(self) -> None:
        with self.assertRaises(TypeError):

            class E(TypeEnum):
                A = 0  # type: ignore[misc]

        with self.assertRaises(TypeError):

            class F(TypeEnum):
                A = ()

                def f(self) -> int:  # type: ignore[misc]
                    return 0

    def test_invalid_baseclass(self) -> None:
        with self.assertRaises(TypeError):

            class E(TypeEnum, int):
                A = ()

    def test_invalid_inheritance(self) -> None:
        class E(TypeEnum):
            A = ()

        with self.assertRaises(TypeError):

            class F(E):  # type: ignore[misc]
                B = ()

    def test_instantiate_type_enum(self) -> None:
        class E(TypeEnum):
            A = (int,)

        with self.assertRaises(TypeError):
            E()
        with self.assertRaises(TypeError):
            TypeEnum()

    def test_name_clash(self) -> None:
        with self.assertRaises(TypeError):

            class E(TypeEnum):
                A = {"B": int}
                B = (int, str)

    def test_empty_type_enum(self) -> None:
        with self.assertRaises(TypeError):

            class E(TypeEnum):  # type: ignore[misc]
                pass

    def test_empty_dict(self) -> None:
        with self.assertRaises(TypeError):

            class E(TypeEnum):
                A = {}  # type: ignore[var-annotated,misc]
