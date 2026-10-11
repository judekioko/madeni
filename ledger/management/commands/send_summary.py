from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ledger import summary


class Command(BaseCommand):
    help = 'Email each user their daily summary of overdue and upcoming payments. Run from cron.'

    def handle(self, *args, **opts):
        sent = sum(summary.send(u) for u in User.objects.exclude(email=''))
        self.stdout.write(f'Sent {sent} summary email(s).')
