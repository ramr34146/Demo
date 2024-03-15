from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(ParaphraseData)
admin.site.register(Archive)


class Synonyms_Admin(admin.ModelAdmin):
    list_display = ['id', 'word', 'synonyms_list']


admin.site.register(Synonyms, Synonyms_Admin)


class DataCollectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'words', 'pos']


admin.site.register(DataCollection, DataCollectionAdmin)


class SpinParaphraseAdmin(admin.ModelAdmin):
    list_display = ['id', 'input_text', 'output_text']


admin.site.register(SpinParaphrase, SpinParaphraseAdmin)
