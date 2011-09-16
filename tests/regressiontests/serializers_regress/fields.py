import uuid

from django.db import models
from django.utils.encoding import force_unicode


class UUIDField(models.Field):
    """
    A field which stores a UUID value in hex format.
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 32
        super(UUIDField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'char(%s)' % self.max_length

    def to_python(self, value):
        """
        Return a uuid.UUID instance from the value returned by the database.
        """
        if not value:
            return None
        if isinstance(value, uuid.UUID):
            return value
        value = force_unicode(value)
        if not len(value) == 32:
            # This is kind of a silly check, for a real field. It is here to
            # ensure that the serializer isn't just doing a unicode of the
            # value but is instead using value_to_string like it should.
            raise TypeError('Expected a UUID hash.')
        return uuid.UUID(value)

    def get_prep_value(self, value):
        value = self.to_python(value)
        if isinstance(value, uuid.UUID):
            value = value.hex
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.hex
