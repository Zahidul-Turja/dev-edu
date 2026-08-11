from django.contrib import admin

from courses.models import Category

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "slug", "name"]
    list_display_links = ["id", "slug", "name"]