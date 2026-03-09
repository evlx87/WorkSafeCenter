from django import forms

from .models import TrainingProgram, Training, TrainingCenter, Internship, InstructionType, Instruction
from .validators import validate_pdf_or_image


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


class TrainingCenterForm(forms.ModelForm):
    class Meta:
        model = TrainingCenter
        fields = [
            'name', 'inn', 'address', 'phone', 'email',
            'website', 'license_number', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TrainingForm(forms.ModelForm):
    document_scan = forms.FileField(
        required=False,
        help_text="Разрешены только файлы в формате .pdf, .jpg, .png (макс. 10 МБ)",
        label="Скан документа",
        validators=[validate_pdf_or_image])

    class Meta:
        model = Training
        fields = [
            'program', 'employee', 'training_date', 'training_center',
            'electrical_safety_group', 'previous_electrical_group',
            'document_scan', 'document_type', 'document_number', 'notes'
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'training_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'training_center': forms.Select(attrs={'class': 'form-control'}),
            'electrical_safety_group': forms.Select(attrs={'class': 'form-control'}),
            'previous_electrical_group': forms.Select(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get('program')
        employee = cleaned_data.get('employee')
        electrical_group = cleaned_data.get('electrical_safety_group')
        previous_group = cleaned_data.get('previous_electrical_group')
        training_date = cleaned_data.get('training_date')

        # Если программа по электробезопасности - обязательные проверки
        if program and program.category and program.category.code == 'ELECTRICAL':

            # 1. Группа обязательна
            if not electrical_group:
                self.add_error(
                    'electrical_safety_group',
                    'Для программ по электробезопасности необходимо указать группу (Приказ № 811)')

            # 2. Проверка последовательности групп
            if electrical_group and previous_group and training_date:
                current_level = _get_group_level(electrical_group)
                previous_level = _get_group_level(previous_group)

                # Можно повышать только на 1 группу за раз
                if current_level > previous_level + 1:
                    self.add_error(
                        'electrical_safety_group',
                        f'Нельзя получить {electrical_group} группу сразу после {previous_group}. '
                        f'Требуется промежуточное обучение.'
                    )

                # Нельзя понижать группу
                if current_level < previous_level:
                    self.add_error(
                        'electrical_safety_group',
                        'Нельзя понизить группу по электробезопасности. '
                        'Для подтверждения текущей группы выберите ту же группу.')

            # 3. Проверка требований для ответственного за электрохозяйство
            if employee and employee.is_electrical_responsible:
                if electrical_group and _get_group_level(electrical_group) < 4:
                    self.add_error(
                        'electrical_safety_group',
                        'Для ответственных за электрохозяйство требуется минимум IV группа')

            # 4. Проверка: не обучаться ли выше IV группы для ответственных
            if employee and employee.is_electrical_responsible:
                if electrical_group and _get_group_level(electrical_group) > 4:
                    self.add_error(
                        'electrical_safety_group',
                        'Для ответственных за электрохозяйство максимальная группа - IV. '
                        'Обучение выше IV группы не требуется.')

        return cleaned_data


def _get_group_level(group):
    """Вспомогательная функция для получения уровня группы"""
    level_map = {
        'I': 1,
        'II': 2,
        'III': 3,
        'IV': 4,
        'V': 5
    }
    return level_map.get(group, 0)


class InternshipForm(forms.ModelForm):
    document_scan = forms.FileField(
        required=False,
        help_text="Скан документа о прохождении стажировки",
        validators=[validate_pdf_or_image]
    )

    class Meta:
        model = Internship
        fields = [
            'employee', 'workplace', 'supervisor', 'start_date',
            'end_date', 'duration_days', 'program_description',
            'is_completed', 'final_assessment', 'document_scan'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'workplace': forms.Select(attrs={'class': 'form-control'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'program_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'final_assessment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        duration_days = cleaned_data.get('duration_days')

        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError(
                    'Дата окончания не может быть раньше даты начала'
                )

            # Проверка минимальной продолжительности (по № 2464 - минимум 2
            # дня)
            calculated_days = (end_date - start_date).days + 1
            if calculated_days < 2:
                raise forms.ValidationError(
                    'Минимальная продолжительность стажировки - 2 дня (Постановление № 2464)'
                )

            # Обновляем duration_days если не указано
            if not duration_days:
                cleaned_data['duration_days'] = calculated_days

        return cleaned_data
