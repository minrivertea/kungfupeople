from django.contrib import admin
from models import Club, DiaryEntry

class ClubAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


class DiaryEntryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
