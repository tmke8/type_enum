from typing import Literal, Union

from type_enum import TypeEnum

from .common import CustomTestCase


class RepresentationsTest(CustomTestCase):
    def test_repr(self) -> None:
        class E(TypeEnum):
            A = (int,)
            B = (int, str)
            C = ()
            D = {"x": int, "y": str}
            E = {"val": bool}
            F = {}  # type: ignore[var-annotated]

        self.assertEqual(repr(E.A(3)), "E.A(3)")
        self.assertEqual(repr(E.B(0, "foo")), "E.B(0, 'foo')")
        self.assertEqual(repr(E.C()), "E.C()")
        self.assertEqual(repr(E.D(3, "bar")), "D(x=3, y='bar')")
        self.assertEqual(repr(E.E(True)), "E(val=True)")
        self.assertEqual(repr(E.F()), "F()")

    def test_docstring(self) -> None:
        class E(TypeEnum):
            A = (Union[Literal[1], dict[int, list[str]]],)

        self.assertEqual(E.A.__doc__, "E.A(Union[int, dict[int, list[str]]])")
