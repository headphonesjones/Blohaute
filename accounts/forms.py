from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from accounts.models import User


class PasswordValidationMixin(object):
    MIN_LENGTH = 8
    MAX_LENGTH = 25
    password_messages = {
        'password_mismatch': _("The two password fields didn't match."),
        'password_length': _("The new password must be between 8 and 25 characters long."),
    }

    def clean_password1(self):
        # clean the new password to match API requirements
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Between MIN_LENGTH and MAX_LENGTH
            if len(password1) < self.MIN_LENGTH or len(password1) > self.MAX_LENGTH:
                raise forms.ValidationError(
                    self.password_messages['password_length'],
                    code='password_length'
                )

            #At least one letter and one non-letter
            first_isalpha = password1[0].isalpha()
            if all(c.isalpha() == first_isalpha for c in password1):
                raise forms.ValidationError("The new password must contain at least one letter and at "
                                            "least one digit or punctuation character.")

            return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.password_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

class RegistrationForm(forms.ModelForm, PasswordValidationMixin):

    error_messages = {
        'phone_length': _("Phone number must be 10 digits and include the area code."),
        'existing_account': _('An account with this email address already exists.')
    }

    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs={
                                    'placeholder': 'Password Confirmation'}),
                                help_text=_("Enter the same password as above, for verification."))
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))

    class Meta:
        model = User
        fields = ("phone_number", "email", "first_name", "last_name")

    def clean_email(self):
        users = User.objects.filter(email=self.cleaned_data.get('email')).count()
        if users > 0:
            raise forms.ValidationError(
                self.error_messages['existing_account'],
                code='existing_account'
            )
        return self.cleaned_data.get('email')


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        #strip out anything that isn't a number
        phone_number = ''.join(i for i in phone_number if i.isdigit())
        if len(phone_number) != 10:
            raise forms.ValidationError(
                self.error_messages['phone_length'],
                code='phone_length'
            )

        return phone_number

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user


class AuthenticationRememberMeForm(AuthenticationForm):

    """
    Subclass of Django ``AuthenticationForm`` which adds a remember me
    checkbox.

    """
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    remember_me = forms.BooleanField(label=_('Remember Me'), initial=False,
                                     required=False)


class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set their password without entering the old
    password
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email Address'}))
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput)
    key = forms.CharField(widget=forms.HiddenInput)

    def clean_newpassword1(self):
        # clean the new password to match API requirements
        password1 = self.cleaned_data.get('new_password1')

        # Between MIN_LENGTH and MAX_LENGTH
        if len(password1) < self.MIN_LENGTH or len(password1) > self.MAX_LENGTH:
            raise forms.ValidationError(
                self.error_messages['password_length'],
                code='password_length'
            )

        #At least one letter and one non-letter
        first_isalpha = password1[0].isalpha()
        if all(c.isalpha() == first_isalpha for c in password1):
            raise forms.ValidationError("The new password must contain at least one letter and at "
                                        "least one digit or punctuation character.")

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        self.user = User.objects.get(email=self.cleaned_data['email'])
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class PasswordUpdateForm(PasswordChangeForm):
    """
    Subclass of Django ``PasswordChangeForm`` which adds placeholder text.

    """
    old_password = forms.CharField(label=_("Old password"),
                                   widget=forms.PasswordInput(attrs={'placeholder': _('Old Password')}))
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput(attrs={'placeholder': _('New Password')}))
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput(attrs={'placeholder': _('New Password Confirmation')}))

    def clean_newpassword1(self):
        # clean the new password to match API requirements
        password1 = self.cleaned_data.get('new_password1')

        # Between MIN_LENGTH and MAX_LENGTH
        if len(password1) < self.MIN_LENGTH or len(password1) > self.MAX_LENGTH:
            raise forms.ValidationError(
                self.error_messages['password_length'],
                code='password_length'
            )

        #At least one letter and one non-letter
        first_isalpha = password1[0].isalpha()
        if all(c.isalpha() == first_isalpha for c in password1):
            raise forms.ValidationError("The new password must contain at least one letter and at "
                                        "least one digit or punctuation character.")


class EmailUpdateForm(forms.Form):
    error_messages = {
        'existing_account': _('An account with this email address already exists.')
    }

    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'New Email Address'}))

    def clean_email(self):
        users = User.objects.filter(email=self.cleaned_data.get('email')).count()
        if users > 0:
            raise forms.ValidationError(
                self.error_messages['existing_account'],
                code='existing_account'
            )
        return self.cleaned_data.get('email')


class PasswordResetForm(forms.Form):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    email = forms.EmailField(label=_("Email"), max_length=254)
