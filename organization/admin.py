from django.contrib import admin

from organization.models import Department, Position


# Register your models here.
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head')
    search_fields = ('name',)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    search_fields = ('name',)
    list_filter = ('department',)