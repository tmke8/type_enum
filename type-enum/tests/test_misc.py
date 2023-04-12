from type_enum import TypeEnum

from .common import CustomTestCase


class MiscTest(CustomTestCase):
    def test_subclass(self) -> None:
        class E(TypeEnum):
            A = (int,)
            B = ()
            C = {"x": int, "y": str}
            D = {}  # type: ignore[var-annotated]

        TA: type[E] = E.A
        a: E = E.A(3)
        self.assertIsSubclass(E.A, E)
        self.assertIsSubclass(E.A, E.T)  # type: ignore[arg-type]
        self.assertIsInstance(E.A(3), E)
        self.assertIsInstance(E.A(3), E.T)  # type: ignore[arg-type]
        self.assertIsInstance(E.A(3), E.A)
        self.assertIsInstance(E.A(3), E.A.A)
        self.assertIsInstance(E.A(3), E.A.A.A)

        self.assertIsSubclass(E.B, E)
        self.assertIsInstance(E.B(), E)
        self.assertIsInstance(E.B(), E.B)

        self.assertIsSubclass(E.C, E)
        self.assertIsInstance(E.C(3, y="foo"), E)
        self.assertIsInstance(E.C(3, y="foo"), E.C)

        self.assertIsSubclass(E.D, E)
        self.assertIsInstance(E.D(), E)
        self.assertIsInstance(E.D(), E.D)

    def test_not_subclass(self) -> None:
        class E(TypeEnum):
            A = (int,)
            B = ()

        self.assertNotIsInstance((3,), E)
        self.assertNotIsInstance((3,), E.A)

        self.assertNotIsInstance((), E)
        self.assertNotIsInstance((), E.B)
