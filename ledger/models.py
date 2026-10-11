from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum


def normalize_phone(raw):
    digits = ''.join(c for c in raw if c.isdigit())
    if digits.startswith('0'):
        digits = '254' + digits[1:]
    elif digits.startswith(('7', '1')) and len(digits) == 9:
        digits = '254' + digits
    return digits


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=120, blank=True)
    pay_instructions = models.CharField(
        max_length=200, blank=True,
        help_text='e.g. "M-Pesa Paybill 123456, Account: your name"')

    def __str__(self):
        return self.business_name or self.user.get_username()


class Debtor(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    def outstanding(self):
        return sum((i.balance for i in self.invoices.all()), Decimal('0'))

    def avg_days_late(self):
        """Average days paid after due date, over fully paid invoices."""
        lates = [i.days_late_when_paid for i in self.invoices.all()
                 if i.days_late_when_paid is not None]
        return round(sum(lates) / len(lates)) if lates else None


class Invoice(models.Model):
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, related_name='invoices')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f'{self.debtor} - {self.description}'

    @property
    def paid(self):
        return self.payments.aggregate(t=Sum('amount'))['t'] or Decimal('0')

    @property
    def balance(self):
        return self.amount - self.paid

    @property
    def is_settled(self):
        return self.balance <= 0

    @property
    def days_overdue(self):
        if self.is_settled:
            return 0
        return max((date.today() - self.due_date).days, 0)

    @property
    def days_late_when_paid(self):
        if not self.is_settled:
            return None
        last = self.payments.order_by('-date').first()
        return max((last.date - self.due_date).days, 0) if last else 0


class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=date.today)
    note = models.CharField(max_length=120, blank=True)


class Reminder(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='reminders')
    tone = models.CharField(max_length=10)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
