import uuid

from django.db import models
from django.utils.encoding import smart_unicode


class UUIDField(models.Field):
    """
    A field which stores a UUID value in hex format. This may also have
    the Boolean attribute 'auto' which will set the value on initial save to a
    new UUID value (calculated using the UUID1 method). Note that while all
    UUIDs are expected to be unique we enforce this with a DB constraint.
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, auto=None, *args, **kwargs):
        self.auto = auto
        # Store UUIDs in hex format, which is fixed at 32 characters.
        kwargs['max_length'] = 32
        if auto:
            # Do not let the user edit UUIDs if they are auto-assigned.
            kwargs['editable'] = False
            kwargs['blank'] = True
            kwargs['unique'] = True
            if not callable(auto):
                self.auto = lambda obj: uuid.uuid4()
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
        # attempt to parse a UUID
        return uuid.UUID(smart_unicode(value))

    def pre_save(self, model_instance, add):
        """
        Ensure that value is auto-set if required.
        """
        value = super(UUIDField, self).pre_save(model_instance, add)
        if self.auto and add and not value:
            # Assign a new value for this attribute if required.
            value = self.auto(model_instance)
            setattr(model_instance, self.attname, value)
        return value

    def get_prep_value(self, value):
        value = self.to_python(value)
        if isinstance(value, uuid.UUID):
            value = value.hex
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.hex
