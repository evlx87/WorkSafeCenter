from django.contrib import admin

from assessments.models import SOUTAssessment, RiskAssessment, Workplace


# Register your models here.
class SOUTInline(admin.StackedInline):
    model = SOUTAssessment
    extra = 0


class RiskInline(admin.TabularInline):
    model = RiskAssessment
    extra = 1


@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    list_display = ('number', 'position', 'site', 'get_sout_class')
    inlines = [SOUTInline, RiskInline]

    def get_sout_class(self, obj):
        return obj.sout.class_conditions if hasattr(
            obj, 'sout') else "Не проведена"
    get_sout_class.short_description = "Класс СОУТ"
