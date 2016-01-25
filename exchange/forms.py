from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.db.transaction import atomic
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _

from .models import UserInfo


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = 'name', 'exchange_offices', 'id'
        widgets = {
            'exchange_offices': CheckboxSelectMultiple,
        }

    name = forms.CharField(required=True, max_length=31)

    def __init__(self, data=None, instance=None, initial=None, **kwargs):
        super(UserInfoForm, self).__init__(data=data, instance=instance, initial=initial, **kwargs)
        if instance:
            self.fields['name'].initial = instance.user.username

    @atomic
    def save(self, commit=True):
        if commit and self.instance:
            self.instance.user.username = self.cleaned_data['name']
            try:
                self.instance.user.save()
            except IntegrityError:
                self.add_error('name', _('Duplicate username, enter any another'))
                return None
        return super(UserInfoForm, self).save(commit=commit)
