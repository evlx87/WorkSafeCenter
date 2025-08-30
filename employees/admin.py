from django.contrib import admin

from employees.models import Employee


# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'position',
        'department',
        'hire_date',
        'is_active')
    search_fields = (
        'last_name',
        'first_name',
        'position__name',
        'department__name')
    list_filter = ('is_active', 'position', 'department')
    ordering = ('last_name',)
