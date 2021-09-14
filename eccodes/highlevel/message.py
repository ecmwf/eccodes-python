
import io

import eccodes

class Message:
    def __init__(self, handle):
        self.handle = handle

    def __del__(self):
        eccodes.codes_release(self.handle)

    def get(self, name):
        return eccodes.codes_get(self.handle, name)

    def set(self, name, value):
        return eccodes.codes_set(self.handle, name, value)

    def get_array(self, name):
        return eccodes.codes_get_array(self.handle, name)

    def set_array(self, name, value):
        return eccodes.codes_set_array(self.handle, name, value)

    def write_to(self, fileobj):
        assert isinstance(fileobj, io.IOBase)
        eccodes.codes_write(self.handle, fileobj)

    def get_buffer(self):
        return eccodes.codes_get_message(self.handle)
