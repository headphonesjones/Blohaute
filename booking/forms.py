from django import forms
from booking.models import Package, Membership
from django.template.defaultfilters import floatformat


class AddToCartForm(forms.Form):
    package = forms.ChoiceField(required=False)
    membership = forms.ModelChoiceField(queryset=Membership.objects.all(),
                                        required=False,
                                        empty_label="Select a Membership")

    def __init__(self, *args, **kwargs):
        self.treatment = kwargs.pop('treatment', None)
        super(AddToCartForm, self).__init__(*args, **kwargs)

        if self.treatment:
            packages = Package.objects.filter(treatment=self.treatment)
            choices = [('', 'Select a Package'),
                       (0, 'Single %s - $%s' % (self.treatment.name, floatformat(self.treatment.price, -2)))
                       ]

            choices.extend([(package.id, package.__unicode__()) for package in packages])
            self.fields['package'].choices = choices
            self.fields['membership'].queryset = Membership.objects.filter(treatment=self.treatment)

    def clean(self):
        if (self.cleaned_data['package'] is None and self.cleaned_data['membership'] is None):
            print 'raising validation error'
            raise forms.ValidationError('You must select either a package or a membership to add to the cart')

    def clean_package(self):
        package = self.cleaned_data['package']
        if package == '':
            return None
        if package == '0':
            return self.treatment

        return Package.objects.filter(treatment=self.treatment).get(pk=package)
