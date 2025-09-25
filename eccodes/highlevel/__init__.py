import sys

if not sys.platform.startswith("win"):
    from ._bufr import BUFRMessage  # noqa

from .message import GRIBMessage, Message  # noqa
from .reader import FileReader, MemoryReader, StreamReader  # noqa
