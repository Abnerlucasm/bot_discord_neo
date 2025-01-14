"""Definition of 'Const Classes'"""

import importlib
import inspect
from typing import Any, Callable

from .utility_funcs import is_const


class ConstClassMeta(type):
    """Metaclass that allows for the creation of a
    `ConstClass`: a class with added utilities
    for handling class-attribute constants.

    Constants are defaultly identified using the
    `is_const` function. This can be modified by
    providing a value to the key-word argument
    `constant_idnetifier`.

    Example:
        >>> class MathConsts(metaclass=ConstClassMeta):
        ...     PI = 3.14159
        ...     E = 2.71828
        ...     NA = 6.0221408e+23
        >>>
        >>>
        >>> MathConsts['PI']  # returns 3.14159
        >>> MathConsts.as_dict()  # returns {'PI': 3.14159, 'E': 2.71828, 'NA': 6.022...}
        >>> MathConsts.apply()  # Apply the constants to the global namespace_callable

    Custom constant identifier:
        >>> class MathConstsWithCustomConsts(
        ...     metaclass=ConstClassMeta,
        ...     constant_identifier=lambda s: s.identifier() and s.islower()
        ... ):
        ...     pi = 3.14159
        ...     e = 2.71828

    For standard creation of Const Classes,
    using `BaseConstClass` is preferred.
    """

    _class_constant_cache: dict['ConstClassMeta', set[str]] = {}
    _class_function_cache: dict['ConstClassMeta', Callable[[str], bool]] = {}

    def __new__(
        cls,
        name: str,
        bases: tuple,
        dct: dict,
        *,
        constant_identifier: Callable[[str], bool] = is_const
    ) -> 'ConstClassMeta':
        """Register an instance of the metaclass and its
        constant attributes to the class constant cache.

        Args:
            constant_identifier: A callable for determining
                                the definition of a constant.
                                Defaultly, `is_const` is used,
                                i.e. constants must be
                                in uppercase and not
                                start with an underscore
                                character.
            allow_constants_only: When true, raises an
                                  `AttributeError` if an
                                  attribute which doe not
                                  suffice `constant_identifier`
                                  is defined under the
                                  class.

        """
        const_class = super().__new__(cls, name, bases, dct)

        cls._class_function_cache[const_class] = constant_identifier

        constants = {
            name
            for name in dir(const_class)
            if constant_identifier(name)
        }
        cls._class_constant_cache[const_class] = constants
        return const_class

    def __getitem__(
            cls,
            item: str
    ) -> Any:
        """Access a constant value by its name."""
        class_constants = ConstClassMeta._class_constant_cache[cls]
        if item in class_constants:
            return getattr(cls, item)
        else:
            available = ', '.join(class_constants)
            raise ValueError(f'Class {cls.__name__} does not '
                             f'contain a constant named {item}. '
                             f'Existing constants are {available}')

    def __setattr__(cls, name: str, value: Any) -> None:
        """Hook the creation of a new class attribute by
        checking if the newly created attribute is a constant.
        If so, add it to the class constant cache.
        """
        super().__setattr__(name, value)
        class_constants = ConstClassMeta._class_constant_cache[cls]
        is_const = ConstClassMeta._class_function_cache[cls]

        if is_const(name) and name not in class_constants:
            class_constants.add(name)

    def __delattr__(cls, name: str) -> None:
        """Hook the deletion of a class attribute by
        checking if the deleted attribute is a constant,
        and if so remove it from the class constant cache.
        """
        super().__delattr__(name)
        class_constants = ConstClassMeta._class_constant_cache[cls]
        if name in class_constants:
            class_constants.remove(name)

    def as_dict(cls) -> dict[str, Any]:
        """Return a dictionary representation of the
        constants within the class.
        """
        class_constants = ConstClassMeta._class_constant_cache[cls]
        return {
            const_name: getattr(cls, const_name)
            for const_name in class_constants
        }

    @property
    def const_names(cls) -> list[str]:
        """Return a list of all constant names."""
        return list(cls.as_dict())

    @property
    def const_values(cls) -> list[Any]:
        """Return a list of all constant values."""
        return list(cls.as_dict().values())

    def __apply(
            cls,
            namespace: Any,
            override: bool,
            f_assign: Callable[[str, Any], None]
    ) -> None:
        for name in ConstClassMeta._class_constant_cache[cls]:
            value = getattr(cls, name)
            if not override and hasattr(namespace, name):
                continue
            f_assign(name, value)

    def apply_to_module(
        cls,
        module_name: str,
        override: bool = False
    ) -> None:
        """Save the constants defined under the class
        to the given module (notated by its name),
        represented as string. To alter the current module,
        use `__name__`. If `override` is set to `True`,
        override already existing attributes within the
        given module name.
        """
        module = importlib.import_module(module_name)
        cls.__apply(module, override, module.__setattr__)

    def apply(
            cls,
            local: bool = False,
            override: bool = False
    ) -> None:
        """Save the constants defined under the class
        to the global namespace of the scope from
        which this method is called.

        If `local` is set to `True`, the values are
        saved to the local namespace instead of the
        global. If `override` is set to `True`,
        constants defined under this class that
        share names with attributes of the calling
        namespace will override the namespace's value.
        """
        current_frame = inspect.currentframe()
        if current_frame is None or current_frame.f_back is None:
            raise RuntimeError('Cannot retrieve current frame')

        caller_frame = current_frame.f_back
        namespace = caller_frame.f_locals if local else caller_frame.f_globals

        cls.__apply(namespace, override, namespace.__setitem__)


class BaseConstClass(metaclass=ConstClassMeta):
    """Helper class that provides a standard way
    to create a Constant Class using inheritance.
    """
    pass
