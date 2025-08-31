from django import forms
from .models import Department, Position, OrganizationSafetyInfo, Site


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'head']


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'description', 'department']


class OrganizationSafetyInfoForm(forms.ModelForm):
    class Meta:
        model = OrganizationSafetyInfo
        fields = [
            'school_name',
            'director_name',
            'ot_specialist_name']


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            'name',
            'address',
            'ot_responsible_name']
