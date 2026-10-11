"""Reminder wording. Tone escalates with how overdue the invoice is."""
from urllib.parse import quote



def pick_tone(days_overdue):
    if days_overdue <= 0:
        return 'heads-up'
    if days_overdue <= 7:
        return 'gentle'
    if days_overdue <= 21:
        return 'firm'
    return 'final'


def draft(invoice, profile):
    d = invoice.debtor
    amt = f'KES {int(invoice.balance):,}'
    sender = profile.business_name or 'us'
    pay = f' You can pay via {profile.pay_instructions}.' if profile.pay_instructions else ''
    tone = pick_tone(invoice.days_overdue)
    what = invoice.description
    if tone == 'heads-up':
        body = (f'Hello {d.name}, a friendly reminder from {sender}: {amt} for {what} '
                f'is due on {invoice.due_date:%d %b}.{pay} Thank you!')
    elif tone == 'gentle':
        body = (f'Hello {d.name}, hope you are well. {amt} for {what} was due on '
                f'{invoice.due_date:%d %b}.{pay} Kindly let me know when to expect it. Thank you.')
    elif tone == 'firm':
        body = (f'Hello {d.name}, {amt} for {what} is now {invoice.days_overdue} days overdue.{pay} '
                f'Please confirm the date you will pay today so I can update my records.')
    else:
        body = (f'{d.name}, {amt} for {what} is {invoice.days_overdue} days overdue. '
                f'I need payment or a firm payment date within 48 hours.{pay} '
                f'Let us settle this so we can keep working together.')
    return tone, body


def whatsapp_link(phone, text):
    return f'https://wa.me/{phone}?text={quote(text)}' if phone else ''
