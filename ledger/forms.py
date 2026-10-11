from datetime import date, timedelta

from django import forms

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
    class Meta:
        model = Profile
        fields = ['business_name', 'pay_instructions']
