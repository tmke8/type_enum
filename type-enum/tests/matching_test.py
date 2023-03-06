from type_enum import TypeEnum


def test_tuple_matching() -> None:
    class T(TypeEnum):
        A = (int,)
        B = (int, str)
        C = ()

    a = T.A(3)
    match a:
        case T.A(x):
            assert x == 3
        case _:
            assert False

    b = T.B(0, "foo")
    match b:
        case T.B(x, y):
            assert x == 0 and y == "foo"
        case _:
            assert False

    c = T.C()
    match c:
        case T.C():
            pass
        case _:
            assert False


def test_namedtuple_matching() -> None:
    class T(TypeEnum):
        A = {"x": int, "y": str}
        B = {"val": bool}
        C = {}  # type: ignore[var-annotated]

    a = T.A(x=3, y="foo")
    match a:
        case T.A(x, y):
            assert x == 3 and y == "foo"
        case _:
            assert False

    b = T.B(False)
    match b:
        case T.B(k):
            assert not k
        case _:
            assert False

    c = T.C()
    match c:
        case T.C():
            pass
        case _:
            assert False
