from django.contrib import admin

from organization.models import Department, Position, OrganizationSafetyInfo


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


@admin.register(OrganizationSafetyInfo)
class OrganizationSafetyInfoAdmin(admin.ModelAdmin):
    list_display = ('name_full', 'director', 'safety_specialist')

    fields = (
        ('name_full', 'inn', 'ogrn'),
        ('address_legal', 'contact_phone'),
        ('director', 'director_position', 'safety_specialist'),
        'safety_committee_members',
    )
