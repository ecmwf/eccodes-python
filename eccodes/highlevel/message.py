import io

import eccodes


class Message:
    def __init__(self, handle):
        self._handle = handle

    def __del__(self):
        try:
            eccodes.codes_release(self._handle)
        except Exception:
            pass

    def copy(self):
        return Message(eccodes.codes_clone(self._handle))

    def __copy__(self):
        return self.copy()

    def get(self, name, ktype=None):
        if eccodes.codes_get_size(self._handle, name) > 1:
            return eccodes.codes_get_array(self._handle, name, ktype=ktype)
        return eccodes.codes_get(self._handle, name, ktype=ktype)

    def set(self, name, value):
        return eccodes.codes_set(self._handle, name, value)

    def get_array(self, name):
        return eccodes.codes_get_array(self._handle, name)

    def get_size(self, name):
        return eccodes.codes_get_size(self._handle, name)

    def get_data(self):
        raise NotImplementedError

    def set_array(self, name, value):
        return eccodes.codes_set_array(self._handle, name, value)

    def dump(self):
        eccodes.codes_dump(self._handle)

    def write_to(self, fileobj):
        assert isinstance(fileobj, io.IOBase)
        eccodes.codes_write(self._handle, fileobj)

    def get_buffer(self):
        return eccodes.codes_get_message(self._handle)


class GRIBMessage(Message):
    def get_data(self):
        return eccodes.codes_grib_get_data(self._handle)

    @classmethod
    def from_samples(cls, name):
        return cls(eccodes.codes_grib_new_from_samples(name))
