from django.db import models
import uuid
from sqlite3 import Binary

class UUIDVersionError(Exception):
    pass

class UUIDField(models.Field):
    
    __metaclass__ = models.SubfieldBase
    empty_strings_allowed = False

    def __init__(self, primary_key=False, verbose_name=None, name=None, auto=True, version=1, node=None, clock_seq=None, namespace=None, **kwargs):
        if primary_key and not auto:
            auto = True
        if auto:
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)
        self.auto = auto
        self.version = version
        if version == 1:
            self.node, self.clock_seq = node, clock_seq
        elif version == 3 or version == 5:
            self.namespace, self.name = namespace, name
        kwargs['max_length'] = 36
        super(UUIDField,self).__init__(verbose_name, name, primary_key, **kwargs)

    def contribute_to_class(self, cls, name):
        if self.primary_key:
            assert not cls._meta.has_auto_field, \
              "A model can't have more than one AutoField: %s %s %s; have %s" % \
               (self, cls, name, cls._meta.auto_field)
            super(UUIDField, self).contribute_to_class(cls, name)
            cls._meta.has_auto_field = True
            cls._meta.auto_field = self
        else:
            super(UUIDField, self).contribute_to_class(cls, name)

    def create_uuid(self):
        if not self.version or self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)
    
    def db_type(self, connection):
        """
            Returns the database column data type for the Field, 
            taking into account the connection object, and the 
            settings associated with it.
        """
        return 'Binary(16)'
    
    def to_python(self, value):
        """
            Converts a value as returned by your database 
            (or a serializer) to a Python object.
        """
        if isinstance(value,models.Model):
            # This happens with related fields 
            # when the relation uses a UUIDField
            # as the primary key.
            value = value.pk
        if isinstance(value,buffer):
            value = "%s" % value
        if value is None:
            value = ''
        if isinstance(value,basestring) and not value:
            pass
        elif not isinstance(value,uuid.UUID):
            try:
                value = uuid.UUID(value)
            except ValueError:
                value = uuid.UUID(bytes=value)
        return unicode(value)
    
    def get_prep_value(self, value):
        """
            New in Django 1.2
            This is the reverse of to_python() when working with 
            the database backends (as opposed to serialization).
        """
        if isinstance(value,buffer):
            value = "%s" % value
        if value is None:
            value = ''
        if isinstance(value,basestring) and not value:
            pass
        elif not isinstance(value,uuid.UUID):
            try:
                value = uuid.UUID(value).bytes
            except ValueError:
                value = uuid.UUID(bytes=value).bytes
        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super(UUIDField,self).get_db_prep_value(value, connection=connection, prepared=prepared)
        if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            value = Binary(value)
        return value

    def pre_save(self, model_instance, add):
        """
            This method is called just prior to get_db_prep_save() 
            and should return the value of the appropriate attribute 
            from model_instance for this field. If the model is 
            being saved to the database for the first time, the add 
            parameter will be True, otherwise it will be False.
        """
        if self.auto and add:
            value = unicode(self.create_uuid())
            setattr(model_instance, self.attname, value)
        else:
            value = super(UUIDField, self).pre_save(model_instance, add)
            if self.auto and not value:
                value = unicode(self.create_uuid())
                setattr(model_instance, self.attname, value)
        return value
    
    def formfield(self, **kwargs):
        if self.primary_key:
            return None
        else:
            return super(UUIDField,self).formfield(**kwargs)
    
    def value_to_string(self, obj):
        """
            This method is used by the serializers to convert the 
            field into a string for output.
        """
        value = self._get_val_from_obj(obj)
        return self.to_python(value)