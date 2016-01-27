from django import forms
from django.forms.widgets import CheckboxSelectMultiple

from .models import UserInfo


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = 'name', 'exchange_offices'
        widgets = {
            'exchange_offices': CheckboxSelectMultiple,
        }