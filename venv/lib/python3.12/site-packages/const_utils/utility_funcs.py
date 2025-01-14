"""Constant-related utility functions."""

from __future__ import annotations

import inspect
from typing import Any, Callable


def is_const(name: str) -> bool:
    """Assures the canonical naming rules for constants within
    this package:
        * The constant name must be completely in uppercase;
        * The constant name must *not* begin with an underscore character;
        * And trivially, the constant name must be a valid Python variable name.
    """
    return name.isidentifier() and name.isupper() and not name.startswith('_')


def access_namespace_consts(
    constant_identifier: Callable[[str], bool] = is_const,
    local: bool = False,
) -> dict[str, Any]:
    """Access all constants within the caller namespace.
    A constant is any attribute name for which
    `constant_identifier(<attribute>)` is True.

    If `local` is True, constants are scanned over `locals()`
    instead of `globals()`.
    """
    current_frame = inspect.currentframe()
    if current_frame is None or current_frame.f_back is None:
        raise RuntimeError('Cannot retrieve stack frames')

    caller_frame = current_frame.f_back
    namespace = caller_frame.f_locals if local else caller_frame.f_globals

    return {
        name: value
        for name, value in namespace.items()
        if constant_identifier(name)
    }
