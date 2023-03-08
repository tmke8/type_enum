from type_enum import TypeEnum

from .common import CustomTestCase


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
            case T.B(x, y):
                self.assertEqual(x, 0)
                self.assertEqual(y, "foo")
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
            case T.A(x, y):
                self.assertEqual(x, 3)
                self.assertEqual(y, "foo")
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
