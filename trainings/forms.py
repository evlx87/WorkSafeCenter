from django import forms

from .models import TrainingProgram, Training, Instruction, InstructionType


class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = [
            'category',
            'is_mandatory',
            'name',
            'hours',
            'frequency_months']
        widgets = {
            'category': forms.Select(
                attrs={
                    'class': 'form-control'}),
            'is_mandatory': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input'}),
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'hours': forms.NumberInput(
                attrs={
                    'class': 'form-control'}),
            'frequency_months': forms.NumberInput(
                attrs={
                    'class': 'form-control'}),
        }


class TrainingForm(forms.ModelForm):
    document_scan = forms.FileField(
        required=False,
        help_text="Разрешены только файлы в формате .pdf.",
        label="Скан документа (.pdf)"
    )

    def clean_document_scan(self):
        file = self.cleaned_data.get('document_scan')
        if file:
            # Проверка размера файла (макс. 10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    'Размер файла не должен превышать 10 МБ')
        return file

    class Meta:
        model = Training
        fields = [
            'program',
            'employee',
            'training_date',
            'document_scan',
            'document_type',
            'document_number'
        ]
        widgets = {
            'program': forms.Select(
                attrs={
                    'class': 'form-control'}),
            'employee': forms.Select(
                attrs={
                    'class': 'form-control'}),
            'training_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'}),
            'document_type': forms.Select(
                attrs={
                    'class': 'form-control'}),
            'document_number': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
        }


class InstructionForm(forms.ModelForm):
    instruction_type = forms.ModelChoiceField(
        queryset=InstructionType.objects.all(),
        label="Тип инструктажа",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Instruction
        fields = [
            'instruction_type',
            'employee',
            'training_date',
            'instructor',
            'basis_document',
        ]

        widgets = {
            'employee': forms.Select(
                attrs={
                    'class': 'form-control'}),
            'training_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'}),
            'instructor': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'basis_document': forms.Select(
                attrs={
                    'class': 'form-control'}),
        }
