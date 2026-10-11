from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Debtor, Invoice, Payment, normalize_phone
from .reminders import pick_tone


class LedgerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('amina', password='pw')
        self.client.login(username='amina', password='pw')

    def test_phone_normalised(self):
        self.assertEqual(normalize_phone('0712 345 678'), '254712345678')
        self.assertEqual(normalize_phone('+254712345678'), '254712345678')

    def test_tone_escalates(self):
        self.assertEqual([pick_tone(d) for d in (-2, 3, 10, 40)],
                         ['heads-up', 'gentle', 'firm', 'final'])

    def test_balance_and_lateness(self):
        d = Debtor.objects.create(owner=self.user, name='Mama Njeri', phone='0712345678')
        due = date.today() - timedelta(days=10)
        inv = Invoice.objects.create(debtor=d, description='Eggs', amount=1000, due_date=due)
        self.assertEqual(inv.days_overdue, 10)
        Payment.objects.create(invoice=inv, amount=400, date=date.today())
        self.assertEqual(inv.balance, 600)
        Payment.objects.create(invoice=inv, amount=600, date=date.today())
        self.assertTrue(inv.is_settled)
        self.assertEqual(d.avg_days_late(), 10)

    def test_add_flow_and_isolation(self):
        r = self.client.post(reverse('add'), {
            'debtor_name': 'Kamau Hotel', 'phone': '0722000111',
            'description': 'Milk', 'amount': '5000',
            'due_date': (date.today() - timedelta(days=5)).isoformat()})
        inv = Invoice.objects.get()
        self.assertRedirects(r, reverse('invoice', args=[inv.pk]))
        page = self.client.get(reverse('invoice', args=[inv.pk]))
        self.assertContains(page, 'wa.me/254722000111')
        other = User.objects.create_user('bob', password='pw')
        self.client.login(username='bob', password='pw')
        self.assertEqual(self.client.get(reverse('invoice', args=[inv.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)


class QuickAddTests(TestCase):
    def test_parse(self):
        from .quickadd import parse
        today = date(2026, 10, 11)  # a Sunday
        r = parse('Kamau Hotel 18,500 milk fri', today)
        self.assertEqual((r['name'], r['amount'], r['description']), ('Kamau Hotel', 18500, 'milk'))
        self.assertEqual(r['due_date'], date(2026, 10, 16))
        r = parse('Njeri 0712345678 7k eggs 20/10', today)
        self.assertEqual((r['phone'], r['amount'], r['due_date']),
                         ('0712345678', 7000, date(2026, 10, 20)))
        self.assertIsNone(parse('just words', today))

    def test_signup_and_quick_add(self):
        r = self.client.post(reverse('signup'), {
            'username': 'newsup', 'password1': 'Str0ng-pass-91x', 'password2': 'Str0ng-pass-91x'})
        self.assertRedirects(r, reverse('settings'))
        self.client.post(reverse('quick'), {'line': 'Baraka 9600 oil kesho'})
        self.assertEqual(Invoice.objects.get().debtor.name, 'Baraka')
