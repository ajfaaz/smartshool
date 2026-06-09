from django import forms
from .models import Result

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = [
            'student',
            'subject',
            'ca1',
            'ca2',
            'exam',
            'teacher_comment',
            'principal_comment'
        ]