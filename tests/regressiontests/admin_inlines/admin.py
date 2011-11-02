from django.contrib import admin
from django import forms

from . import models

site = admin.AdminSite(name="admin")


class BookInline(admin.TabularInline):
    model = models.Author.books.through


class AuthorAdmin(admin.ModelAdmin):
    inlines = [BookInline]


class InnerInline(admin.StackedInline):
    model = models.Inner
    can_delete = False
    readonly_fields = ('readonly',)   # For bug #13174 tests.


class HolderAdmin(admin.ModelAdmin):

    class Media:
        js = ('my_awesome_admin_scripts.js',)


class InnerInline2(admin.StackedInline):
    model = models.Inner2

    class Media:
        js = ('my_awesome_inline_scripts.js',)


class InnerInline3(admin.StackedInline):
    model = models.Inner3

    class Media:
        js = ('my_awesome_inline_scripts.js',)


class TitleForm(forms.ModelForm):

    def clean(self):
        cleaned_data = self.cleaned_data
        title1 = cleaned_data.get("title1")
        title2 = cleaned_data.get("title2")
        if title1 != title2:
            raise forms.ValidationError("The two titles must be the same")
        return cleaned_data


class TitleInline(admin.TabularInline):
    model = models.Title
    form = TitleForm
    extra = 1


class Inner4StackedInline(admin.StackedInline):
    model = models.Inner4Stacked


class Inner4TabularInline(admin.TabularInline):
    model = models.Inner4Tabular


class Holder4Admin(admin.ModelAdmin):
    inlines = [Inner4StackedInline, Inner4TabularInline]


class InlineWeakness(admin.TabularInline):
    model = models.ShoppingWeakness
    extra = 1


class QuestionInline(admin.TabularInline):
    model = models.Question
    readonly_fields = ['call_me']

    def call_me(self, obj):
        return 'Callable in QuestionInline'


class PollAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]

    def call_me(self, obj):
        return 'Callable in PollAdmin'


class ChapterInline(admin.TabularInline):
    model = models.Chapter
    readonly_fields = ['call_me']

    def call_me(self, obj):
        return 'Callable in ChapterInline'


class NovelAdmin(admin.ModelAdmin):
    inlines = [ChapterInline]


class ConsigliereInline(admin.TabularInline):
    model = models.Consigliere


class SottoCapoInline(admin.TabularInline):
    model = models.SottoCapo


class FAdminInline(admin.TabularInline):
    model = models.F
    fk_name = 'fk1'
    extra = 0


class EAdmin(admin.ModelAdmin):
    inlines = (FAdminInline,)


class GAdmin(admin.ModelAdmin):
    raw_id_fields = ("relation",)


class HAdmin(admin.ModelAdmin):
    raw_id_fields = ("relation",)

site.register(models.TitleCollection, inlines=[TitleInline])
# Test bug #12561 and #12778
# only ModelAdmin media
site.register(models.Holder, HolderAdmin, inlines=[InnerInline])
# ModelAdmin and Inline media
site.register(models.Holder2, HolderAdmin, inlines=[InnerInline2])
# only Inline media
site.register(models.Holder3, inlines=[InnerInline3])

site.register(models.Poll, PollAdmin)
site.register(models.Novel, NovelAdmin)
site.register(models.Fashionista, inlines=[InlineWeakness])
site.register(models.Holder4, Holder4Admin)
site.register(models.Author, AuthorAdmin)
site.register(models.CapoFamiglia, inlines=[ConsigliereInline, SottoCapoInline])

site.register(models.A)
site.register(models.B)
site.register(models.C)
site.register(models.D)
site.register(models.E, EAdmin)
site.register(models.G, GAdmin)
site.register(models.H, HAdmin)
