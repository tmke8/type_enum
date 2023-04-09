from __future__ import annotations
from typing_extensions import assert_type

from type_enum import TypeEnum

from .common import CustomTestCase


# the following forces mypy to evaluate the file twice
c: C


class C:
    ...


class MatchingTest(CustomTestCase):
    def test_tuple_matching(self) -> None:
        class T(TypeEnum):
            A = (int,)
            B = (int, str)
            C = ()

        a = T.A(3)
        match a:
            case T.A(x):
                self.assertEqual(x, 3)
            case _:
                self.fail(f"not matched: {a}")

        b = T.B(0, "foo")
        match b:
            case T.B(y, z):
                self.assertEqual(y, 0)
                self.assertEqual(z, "foo")
            case _:
                self.fail(f"not matched: {b}")

        c = T.C()
        match c:
            case T.C():
                pass
            case _:
                self.fail(f"not matched: {c}")

    def test_namedtuple_matching(self) -> None:
        class T(TypeEnum):
            A = {"x": int, "y": str}
            B = {"val": bool}
            C = {}  # type: ignore[var-annotated]

        a = T.A(x=3, y="foo")
        match a:
            case T.A(x=x_, y=y_):
                self.assertEqual(x_, 3)
                self.assertEqual(y_, "foo")
                assert_type(x_, int)
                assert_type(y_, str)
            case _:
                self.fail(f"not matched: {a}")

        b = T.B(False)
        match b:
            case T.B(k):
                self.assertFalse(k)
            case _:
                self.fail(f"not matched: {b}")

        c = T.C()
        match c:
            case T.C():
                pass
            case _:
                self.fail(f"not matched: {c}")

    def test_exhaustiveness(self) -> None:
        class Color(TypeEnum):
            transparent = ()
            name = (str,)

        def f(color: Color.ALL) -> int:
            match color:
                case Color.transparent():
                    return 0
                case Color.name(color_name):
                    print(f"color name: {color_name}")
                    return 0

        self.assertEqual(f(Color.transparent()), 0)
