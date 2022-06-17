from contextlib import contextmanager
import io

import eccodes


@contextmanager
def raise_keyerror(name):
    """Make operations on a key raise a KeyError if not found"""
    try:
        yield
    except eccodes.KeyValueNotFoundError:
        raise KeyError(name)


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

    def _get(self, name, ktype=None):
        with raise_keyerror(name):
            if eccodes.codes_get_size(self._handle, name) > 1:
                return eccodes.codes_get_array(self._handle, name, ktype=ktype)
            return eccodes.codes_get(self._handle, name, ktype=ktype)

    def get(self, name, default=None, ktype=None):
        try:
            return self._get(name, ktype=ktype)
        except KeyError:
            return default

    def set(self, name, value):
        with raise_keyerror(name):
            return eccodes.codes_set(self._handle, name, value)

    def get_array(self, name):
        with raise_keyerror(name):
            return eccodes.codes_get_array(self._handle, name)

    def get_size(self, name):
        with raise_keyerror(name):
            return eccodes.codes_get_size(self._handle, name)

    def get_data(self):
        raise NotImplementedError

    def set_array(self, name, value):
        with raise_keyerror(name):
            return eccodes.codes_set_array(self._handle, name, value)

    def __getitem__(self, name):
        return self._get(name)

    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, name):
        return bool(eccodes.codes_is_defined(self._handle, name))


    class _KeyIterator:
        def __init__(self, message, namespace=None, iter_keys=True, iter_values=False):
            self._message = message
            self._iterator = eccodes.codes_keys_iterator_new(message._handle, namespace)
            self._iter_keys = iter_keys
            self._iter_values = iter_values

        def __del__(self):
            try:
                eccodes.codes_keys_iterator_delete(self._iterator)
            except Exception:
                pass

        def __iter__(self):
            return self

        def __next__(self):
            if not eccodes.codes_keys_iterator_next(self._iterator):
                raise StopIteration
            if not self._iter_keys and not self._iter_values:
                return
            key = eccodes.codes_keys_iterator_get_name(self._iterator)
            if self._iter_keys and not self._iter_values:
                return key
            value = self._message.get(key) if self._iter_values else None
            if not self._iter_keys:
                return value
            return key, value


    def  __iter__(self):
        return self._KeyIterator(self)

    def keys(self, namespace=None):
        return self._KeyIterator(self, namespace, iter_keys=True, iter_values=False)

    def values(self, namespace=None):
        return self._KeyIterator(self, namespace, iter_keys=False, iter_values=True)

    def items(self, namespace=None):
        return self._KeyIterator(self, namespace, iter_keys=True, iter_values=True)

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
