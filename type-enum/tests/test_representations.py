from typing import Literal, Union

from type_enum import TypeEnum

from .common import CustomTestCase


class RepresentationsTest(CustomTestCase):
    def test_repr(self) -> None:
        class T(TypeEnum):
            A = (int,)
            B = (int, str)
            C = ()
            D = {"x": int, "y": str}
            E = {"val": bool}
            F = {}  # type: ignore[var-annotated]

        self.assertEqual(repr(T.A(3)), "T.A(3)")
        self.assertEqual(repr(T.B(0, "foo")), "T.B(0, 'foo')")
        self.assertEqual(repr(T.C()), "T.C()")
        self.assertEqual(repr(T.D(3, "bar")), "D(x=3, y='bar')")
        self.assertEqual(repr(T.E(True)), "E(val=True)")
        self.assertEqual(repr(T.F()), "F()")

    def test_docstring(self) -> None:
        class T(TypeEnum):
            A = (Union[Literal[1], dict[int, list[str]]],)

        self.assertEqual(T.A.__doc__, "T.A(Union[int, dict[int, list[str]]])")
