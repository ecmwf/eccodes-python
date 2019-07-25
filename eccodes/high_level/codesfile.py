"""
``CodesFile`` class that implements a file that is readable by ecCodes and
closes itself and its messages when it is no longer needed.

Author: Daniel Lee, DWD, 2016
"""

from .. import eccodes
import io

class CodesFile(io.FileIO):

    """
    An abstract class to specify and/or implement common behaviour that files
    read by ecCodes should implement.

    A {prod_type} file handle meant for use in a context manager.

    Individual messages can be accessed using the ``next`` method. Of course,
    it is also possible to iterate over each message in the file::

        >>> with {classname}(filename) as {alias}:
        ...     # Print number of messages in file
        ...     len({alias})
        ...     # Open all messages in file
        ...     for msg in {alias}:
        ...         print(msg[key_name])
        ...     len({alias}.open_messages)
        >>> # When the file is closed, any open messages are closed
        >>> len({alias}.open_messages)
    """

    #: Type of messages belonging to this file
    MessageClass = None

    def __init__(self, filename, mode="rb"):
        """Open file and receive codes file handle."""

        if hasattr(filename, 'read'):
            self.file_handle = filename
        elif filename.startswith('https://') or filename.startswith('http://'):
            try:
                import requests
                from io import BytesIO

                self.file_handle = BytesIO(requests(filename).content)
            except ModuleNotFoundError as e:
                print("It seems you are trying to load a file from the internet. This package relies on the requests package, which are not automatically "
                      "loaded for performance issues. Please, install requests package with `pip install requests`")
                raise e
        else:
            #: File handle for working with actual file on disc
            #: The class holds the file it works with because ecCodes'
            # typechecking does not allow using inherited classes.
            self.file_handle = open(filename, mode)

        #: Number of message in file currently being read
        self.message = 0
        #: Open messages
        self.open_messages = []
        self.name = filename

    def __exit__(self, exception_type, exception_value, traceback):
        """Close all open messages, release file handle and close file."""
        while self.open_messages:
            self.open_messages.pop().close()
        eccodes.codes_close_file(self.file_handle)
        #self.file_handle.close()

    def __len__(self):
        """Return total number of messages in file."""
        return eccodes.codes_count_in_file(self.file_handle)

    def __enter__(self):
        return self

    def close(self):
        """Possibility to manually close file."""
        self.__exit__(None, None, None)

    def __iter__(self):
        return self

    def next(self):
        try:
            return self.MessageClass(self)
        except IOError:
            raise StopIteration()
