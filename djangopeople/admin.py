from django.contrib import admin
from models import Club

class ClubAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
