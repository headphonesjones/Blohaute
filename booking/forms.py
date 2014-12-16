from django import forms
from django.template.defaultfilters import floatformat
from localflavor.us.forms import USZipCodeField, USPhoneNumberField, USStateField
from booking.models import Package, Membership, Treatment
from booking.fields import CreditCardField, ExpiryDateField, VerificationValueField


class QuickBookForm(forms.Form):
    treatment = forms.ModelChoiceField(queryset=Treatment.objects.all(),
                                       widget=forms.HiddenInput())


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


class CouponForm(forms.Form):
    coupon_code = forms.CharField()


class CheckoutForm(forms.Form):
    #appointment location
    company_name = forms.CharField(required=False)
    address = forms.CharField()
    city = forms.CharField()
    state = USStateField()
    zip_code = USZipCodeField()
    notes = forms.CharField(widget=forms.Textarea(), required=False)

    #billing Information
    first_name = forms.CharField()
    last_name = forms.CharField()
    billing_address = forms.CharField()
    billing_city = forms.CharField()
    billing_state = USStateField()
    billing_zip_code = USZipCodeField()
    email_address = forms.EmailField()
    phone_number = USPhoneNumberField()
    create_account = forms.BooleanField(initial=False, required=False)

    card_number = CreditCardField(required=True)
    expiry_date = ExpiryDateField(required=True)
    card_code = VerificationValueField(required=True, label="CVV Code")

    date = forms.DateField(widget=forms.HiddenInput())
    time = forms.CharField(widget=forms.Select())


class ContactForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea())