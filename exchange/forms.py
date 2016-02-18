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

    def __init__(self, *args, **kwargs):
        super(UserInfoForm, self).__init__(*args, **kwargs)
        self.fields['exchange_offices'].queryset = self.fields['exchange_offices'].queryset.filter(is_removed=False)