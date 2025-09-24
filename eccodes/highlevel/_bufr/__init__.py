"""
A High-level interface for en/decoding of BUFR files.
"""

from .common import change_behaviour, get_behaviour, set_behaviour
from .helpers import missing_of
from .message import BUFRMessage

__all__ = [
    'change_behaviour', 'get_behaviour', 'set_behaviour',
    'missing_of',
    'BUFRMessage',
]
