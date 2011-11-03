"""
Testing of admin inline formsets.

"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from .fields import UUIDField


class Parent(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Child(models.Model):
    name = models.CharField(max_length=50)
    teacher = models.ForeignKey(Teacher)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey()

    def __unicode__(self):
        return u'I am %s, a child of %s' % (self.name, self.parent)


class Book(models.Model):
    name = models.CharField(max_length=50)


class Author(models.Model):
    name = models.CharField(max_length=50)
    books = models.ManyToManyField(Book)


class Holder(models.Model):
    dummy = models.IntegerField()


class Inner(models.Model):
    dummy = models.IntegerField()
    holder = models.ForeignKey(Holder)
    readonly = models.CharField("Inner readonly label", max_length=1)


class Holder2(models.Model):
    dummy = models.IntegerField()


class Inner2(models.Model):
    dummy = models.IntegerField()
    holder = models.ForeignKey(Holder2)

class Holder3(models.Model):
    dummy = models.IntegerField()


class Inner3(models.Model):
    dummy = models.IntegerField()
    holder = models.ForeignKey(Holder3)

# Models for ticket #8190

class Holder4(models.Model):
    dummy = models.IntegerField()

class Inner4Stacked(models.Model):
    dummy = models.IntegerField(help_text="Awesome stacked help text is awesome.")
    holder = models.ForeignKey(Holder4)

class Inner4Tabular(models.Model):
    dummy = models.IntegerField(help_text="Awesome tabular help text is awesome.")
    holder = models.ForeignKey(Holder4)


# Models for #12749

class Person(models.Model):
    firstname = models.CharField(max_length=15)

class OutfitItem(models.Model):
    name = models.CharField(max_length=15)

class Fashionista(models.Model):
    person = models.OneToOneField(Person, primary_key=True)
    weaknesses = models.ManyToManyField(OutfitItem, through='ShoppingWeakness', blank=True)

class ShoppingWeakness(models.Model):
    fashionista = models.ForeignKey(Fashionista)
    item = models.ForeignKey(OutfitItem)

# Models for #13510

class TitleCollection(models.Model):
    pass

class Title(models.Model):
    collection = models.ForeignKey(TitleCollection, blank=True, null=True)
    title1 = models.CharField(max_length=100)
    title2 = models.CharField(max_length=100)

# Models for #15424

class Poll(models.Model):
    name = models.CharField(max_length=40)

class Question(models.Model):
    poll = models.ForeignKey(Poll)

class Novel(models.Model):
    name = models.CharField(max_length=40)

class Chapter(models.Model):
    novel = models.ForeignKey(Novel)


# Models for #16838
class CapoFamiglia(models.Model):
    name = models.CharField(max_length=100)


class Consigliere(models.Model):
    name = models.CharField(max_length=100)
    capo_famiglia = models.ForeignKey(CapoFamiglia, related_name='+')


class SottoCapo(models.Model):
    name = models.CharField(max_length=100)
    capo_famiglia = models.ForeignKey(CapoFamiglia, related_name='+')


# Models for non-unicode fields in inlines

class NonUnicodeBase(models.Model):
    class Meta():
        abstract = True

    binary_id = UUIDField(primary_key=True, auto=True)

    def __unicode__(self):
        return u"%s(pk=%r)" % (self.__class__.__name__, self.pk)

    @models.permalink
    def get_change_url(self):
        # {{ app_label }}_{{ model_name }}_change     object_id
        return ('admin:%s_%s_change' % (self._meta.app_label,
            self.__class__.__name__)).lower(), (self.pk,)


class A(NonUnicodeBase):
    pass


class B(NonUnicodeBase):
    relation = models.ForeignKey(A)


class C(NonUnicodeBase):
    relation = models.OneToOneField(A)


class D(NonUnicodeBase):
    relation = models.ManyToManyField(A)


class E(NonUnicodeBase):
    relation = models.ManyToManyField(A, through='F')


class F(NonUnicodeBase):
    fk1 = models.ForeignKey(E)
    fk2 = models.ForeignKey(A, related_name="fa_fk2")
    m2m1 = models.ManyToManyField(A, related_name="fa_m2m1")
    one1 = models.OneToOneField(B)


class G(NonUnicodeBase):
    relation = models.ForeignKey(A)


class H(NonUnicodeBase):
    relation = models.ManyToManyField(A)
