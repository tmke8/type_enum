from type_enum import TypeEnum


def test_subclass() -> None:
    class T(TypeEnum):
        A = (int,)
        B = ()
        C = {"x": int, "y": str}
        D = {}  # type: ignore[var-annotated]

    TA: type[T] = T.A
    a: T = T.A(3)
    assert issubclass(T.A, T)
    assert isinstance(T.A(3), T)
    assert isinstance(T.A(3), T.A)

    assert issubclass(T.B, T)
    assert isinstance(T.B(), T)
    assert isinstance(T.B(), T.B)

    assert issubclass(T.C, T)
    assert isinstance(T.C(3, y="foo"), T)
    assert isinstance(T.C(3, y="foo"), T.C)

    assert issubclass(T.D, T)
    assert isinstance(T.D(), T)
    assert isinstance(T.D(), T.D)


def test_not_subclass() -> None:
    class T(TypeEnum):
        A = (int,)
        B = ()

    assert not isinstance((3,), T)
    assert not isinstance((3,), T.A)

    assert not isinstance((), T)
    assert not isinstance((), T.B)
