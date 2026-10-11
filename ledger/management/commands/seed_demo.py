from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ledger.models import Debtor, Invoice, Payment, Profile

DEMO_USER, DEMO_PASSWORD = 'demo', 'demo-pass-123'  # local dev only


class Command(BaseCommand):
    help = 'Create a demo supplier account with sample debts (local use only).'

    def handle(self, *args, **opts):
        user, created = User.objects.get_or_create(username=DEMO_USER)
        if not created:
            self.stdout.write('Demo user already exists; nothing changed.')
            return
        user.set_password(DEMO_PASSWORD)
        user.save()
        Profile.objects.create(user=user, business_name='Wanjiku Fresh Supplies',
                               pay_instructions='M-Pesa Till 123456')
        today = date.today()
        rows = [('Kamau Hotel', '0722000111', 'Milk, 3 weeks', 18500, -26),
                ('Mama Njeri Kiosk', '0711222333', 'Eggs, 20 trays', 7200, -9),
                ('Greenview School', '0733444555', 'Vegetables, term 3', 42000, 5),
                ('Baraka Butchery', '0700111222', 'Cooking oil', 9600, -3)]
        for name, phone, desc, amt, offset in rows:
            d = Debtor.objects.create(owner=user, name=name, phone=phone)
            inv = Invoice.objects.create(debtor=d, description=desc, amount=amt,
                                         due_date=today + timedelta(days=offset))
        old = Invoice.objects.filter(debtor__name='Baraka Butchery').first()
        Payment.objects.create(invoice=old, amount=old.amount, date=today)
        self.stdout.write(f'Created demo user "{DEMO_USER}" (password in seed_demo.py).')
