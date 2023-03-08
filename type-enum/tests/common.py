import types
from typing import Any
from typing_extensions import TypeAlias
from unittest import TestCase

_ClassInfo: TypeAlias = type | tuple[type, ...] | types.UnionType


class CustomTestCase(TestCase):
    def assertIsSubclass(
        self, cls: type, parent_cls: _ClassInfo, msg: Any = None
    ) -> None:
        """Same as self.assertTrue(issubclass(cls, parent_cls))."""
        if not issubclass(cls, parent_cls):
            standardMsg = "%r is not a subclass of %r" % (cls, parent_cls)
            self.fail(self._formatMessage(msg, standardMsg))

    def assertNotIsSubclass(
        self, cls: type, parent_cls: _ClassInfo, msg: Any = None
    ) -> None:
        """Included for symmetry with assertIsSubclass."""
        if issubclass(cls, parent_cls):
            standardMsg = "%r is a subclass of %r" % (cls, parent_cls)
            self.fail(self._formatMessage(msg, standardMsg))
