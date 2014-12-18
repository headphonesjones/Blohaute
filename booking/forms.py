from django import forms
from django.forms.formsets import formset_factory
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
            raise forms.ValidationError('You must select either a package or a \
                                        membership to add to the cart')

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
    first_name = forms.CharField()
    last_name = forms.CharField()
    address = forms.CharField()
    city = forms.CharField()
    state = USStateField(widget=forms.TextInput(attrs={'maxlength': 2}))
    zip_code = USZipCodeField()
    notes = forms.CharField(required=False, label="Other Notes",
                            widget=forms.Textarea(attrs={'rows': 3}))

    #billing Information
    name_on_card = forms.CharField(required=True)
    card_number = CreditCardField(required=True)
    expiry_date = ExpiryDateField(required=True)
    card_code = VerificationValueField(required=True, label="CVV")
    billing_zip_code = USZipCodeField(label="Billing Zip")

    email_address = forms.EmailField()
    phone_number = USPhoneNumberField()
    create_account = forms.BooleanField(initial=False, required=False)

    date = forms.DateField()
    time = forms.CharField()


class SelectAvailableServiceForm(forms.Form):
    series = None
    treatment = None
    treatment_id = forms.HiddenInput()
    quantity = forms.IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        super(SelectAvailableServiceForm, self).__init__(*args, **kwargs)
        self.series = kwargs['initial'].get('series', None)
        self.treatment = self.series.treatment
        self.fields['quantity'] = forms.IntegerField(max_value=self.series.remaining, min_value=0) 

#use the factory to create the base model for us
BaseAvailableServiceFormset = formset_factory(SelectAvailableServiceForm, extra = 0)


class AvailableServiceFormset(BaseAvailableServiceFormset):
    series = None

    def __init__(self, *args, **kwargs):
        self.series = kwargs.pop('series')
        kwargs['initial'] = [{'treatment_id': s.treatment.pk, 'quantity': 0, 'series': s} for s in self.series]
        super(AvailableServiceFormset, self).__init__(*args, **kwargs)   

    def _construct_form(self, *args, **kwargs):
        # inject user in each form on the formset
        #kwargs['user'] = self.user       
        return super(AvailableServiceFormset, self)._construct_form(*args, **kwargs)


class ScheduleServiceForm(forms.Form):
    address = forms.CharField()
    city = forms.CharField()
    state = USStateField(widget=forms.TextInput(attrs={'maxlength': 2}))
    zip_code = USZipCodeField()

    date = forms.DateField()
    time = forms.CharField()


class ContactForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea())
