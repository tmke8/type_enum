from typing import Tuple, Type

from type_enum import Field, TypeEnum

from .common import CustomTestCase


class MiscTest(CustomTestCase):
    def test_subclass(self) -> None:
        class E(TypeEnum):
            # A: Type[Tuple[int]]
            A: Field[int]
            B: Type[Tuple[()]]
            # C = {"x": int, "y": str}

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

        # self.assertIsSubclass(E.C, E)
        # self.assertIsInstance(E.C(3, y="foo"), E)
        # self.assertIsInstance(E.C(3, y="foo"), E.C)

    def test_not_subclass(self) -> None:
        class E(TypeEnum):
            A: Type[Tuple[int]]
            B: Type[Tuple[()]]

        self.assertNotIsInstance((3,), E)
        self.assertNotIsInstance((3,), E.A)

        self.assertNotIsInstance((), E)
        self.assertNotIsInstance((), E.B)
