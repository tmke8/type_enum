from __future__ import annotations

from type_enum import TypeEnum

from .common import CustomTestCase

# the following forces mypy to evaluate the file twice
c: C


class C: ...


class MatchingTest(CustomTestCase):
    def test_tuple_matching(self) -> None:
        class E(TypeEnum):
            A: type[tuple[int]]
            B: type[tuple[int, str]]
            C: type[tuple[()]]

        a = E.A(3)
        match a:
            case E.A(x):
                self.assertEqual(x, 3)
            case _:
                self.fail(f"not matched: {a}")

        b = E.B(0, "foo")
        match b:
            case E.B(y, z):
                self.assertEqual(y, 0)
                self.assertEqual(z, "foo")
            case _:
                self.fail(f"not matched: {b}")

        c = E.C()
        match c:
            case E.C():
                pass
            case _:
                self.fail(f"not matched: {c}")

    # def test_namedtuple_matching(self) -> None:
    #     class E(TypeEnum):
    #         A = {"x": int, "y": str}
    #         B = {"val": bool}

    #     a = E.A(x=3, y="foo")
    #     match a:
    #         case E.A(x=x_, y=y_):
    #             self.assertEqual(x_, 3)
    #             self.assertEqual(y_, "foo")
    #             assert_type(x_, int)
    #             assert_type(y_, str)
    #         case _:
    #             self.fail(f"not matched: {a}")

    #     b = E.B(False)
    #     match b:
    #         case E.B(k):
    #             self.assertFalse(k)
    #         case _:
    #             self.fail(f"not matched: {b}")

    def test_exhaustiveness(self) -> None:
        class Color(TypeEnum):
            transparent: type[tuple[()]]
            name: type[tuple[str]]

        def f(color: Color.T) -> int:
            match color:
                case Color.transparent():
                    return 0
                case Color.name(color_name):
                    print(f"color name: {color_name}")
                    return 0

        self.assertEqual(f(Color.transparent()), 0)
