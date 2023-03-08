from type_enum import TypeEnum

from .common import CustomTestCase


class MiscTest(CustomTestCase):
    def test_subclass(self) -> None:
        class T(TypeEnum):
            A = (int,)
            B = ()
            C = {"x": int, "y": str}
            D = {}  # type: ignore[var-annotated]

        TA: type[T] = T.A
        a: T = T.A(3)
        self.assertIsSubclass(T.A, T)
        self.assertIsInstance(T.A(3), T)
        self.assertIsInstance(T.A(3), T.A)

        self.assertIsSubclass(T.B, T)
        self.assertIsInstance(T.B(), T)
        self.assertIsInstance(T.B(), T.B)

        self.assertIsSubclass(T.C, T)
        self.assertIsInstance(T.C(3, y="foo"), T)
        self.assertIsInstance(T.C(3, y="foo"), T.C)

        self.assertIsSubclass(T.D, T)
        self.assertIsInstance(T.D(), T)
        self.assertIsInstance(T.D(), T.D)

    def test_not_subclass(self) -> None:
        class T(TypeEnum):
            A = (int,)
            B = ()

        self.assertNotIsInstance((3,), T)
        self.assertNotIsInstance((3,), T.A)

        self.assertNotIsInstance((), T)
        self.assertNotIsInstance((), T.B)
