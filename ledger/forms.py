from datetime import date, timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Payment, Profile


class InvoiceForm(forms.Form):
    debtor_name = forms.CharField(max_length=120, label='Who owes you?')
    phone = forms.CharField(max_length=20, required=False, label='Phone (for WhatsApp)')
    description = forms.CharField(max_length=200, label='For what?')
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=1, label='Amount (KES)')
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=lambda: date.today() + timedelta(days=7))


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'date', 'note']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, label='Email for daily summary')

    class Meta:
        model = Profile
        fields = ['business_name', 'pay_instructions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email
        self.order_fields(['business_name', 'pay_instructions', 'email'])

    def save(self, commit=True):
        profile = super().save(commit)
        profile.user.email = self.cleaned_data['email']
        profile.user.save()
        return profile


class SignupForm(UserCreationForm):
    email = forms.EmailField(help_text='For your daily summary of who owes you.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
