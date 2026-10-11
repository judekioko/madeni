"""Daily digest: what is overdue, what falls due soon, and who to message first."""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail

from .models import Invoice


def build(user, today=None):
    """Returns (subject, body) or None when there is nothing to report."""
    today = today or date.today()
    open_ = [i for i in Invoice.objects.filter(debtor__owner=user).select_related('debtor')
             if not i.is_settled]
    overdue = sorted((i for i in open_ if i.due_date < today), key=lambda i: -i.days_overdue)
    soon = sorted((i for i in open_ if today <= i.due_date <= today + timedelta(days=2)),
                  key=lambda i: i.due_date)
    if not overdue and not soon:
        return None
    total = sum((i.balance for i in open_), Decimal('0'))
    lines = [f'You are owed KES {int(total):,} in total.', '']
    if overdue:
        lines.append(f'OVERDUE ({len(overdue)}) - message these today:')
        for i in overdue:
            lines.append(f'  {i.debtor.name}: KES {int(i.balance):,}, {i.days_overdue} days late'
                         f' -> {settings.SITE_URL}/invoice/{i.pk}/')
        lines.append('')
    if soon:
        lines.append(f'DUE IN THE NEXT 2 DAYS ({len(soon)}):')
        for i in soon:
            lines.append(f'  {i.debtor.name}: KES {int(i.balance):,}, due {i.due_date:%a %d %b}'
                         f' -> {settings.SITE_URL}/invoice/{i.pk}/')
    subject = f'Madeni: {len(overdue)} overdue, KES {int(total):,} owed'
    return subject, '\n'.join(lines).rstrip() + '\n'


def send(user, today=None):
    msg = build(user, today)
    if not msg or not user.email:
        return False
    send_mail(msg[0], msg[1], None, [user.email])
    return True
