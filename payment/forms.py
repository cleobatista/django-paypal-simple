from django import forms

from .models import (
    Purchase
)

from pycpfcnpj import cpfcnpj


class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase
        fields = ['first_name', 'last_name', 'id_cpf', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = True

    def clean(self, *args, **kwargs):
        if not cpfcnpj.validate(self['id_cpf'].value()):
            self._errors['id_cpf'] = ["Informe um cpf válido"]
        super().clean(*args, **kwargs)
