"""const-utils: Utilities for working with constants"""

from .const_class import BaseConstClass, ConstClassMeta
from .utility_funcs import access_namespace_consts, is_const

__all__ = [
    'access_namespace_consts',
    'BaseConstClass',
    'ConstClassMeta',
    'is_const'
]