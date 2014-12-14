from django import forms


class DeleteItemForm(forms.Form):
    pk = forms.IntegerField()


class UpdateQuantityForm(forms.Form):
    pk = forms.IntegerField()
    quantity = forms.IntegerField()
