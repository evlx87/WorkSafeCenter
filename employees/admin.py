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
        'is_executive',
        'is_pedagogical',
        'on_parental_leave',
        'is_safety_committee_member',
        'is_active')
    search_fields = (
        'last_name',
        'first_name',
        'position__name',
        'department__name')
    list_filter = (
        'is_active',
        'is_pedagogical',
        'on_parental_leave',
        'is_executive',
        'is_safety_committee_member',
        'position',
        'department'
    )
    ordering = ('last_name',)

    def get_readonly_fields(self, request, obj=None):
        # Делаем устаревшие поля только для чтения
        readonly = list(self.readonly_fields or [])
        readonly.extend(['medical_check_date', 'safety_training_date'])
        return readonly
