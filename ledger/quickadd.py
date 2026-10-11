"""Parse a one-line debt note like 'Kamau Hotel 18500 milk fri' or 'Njeri 0712345678 7,200 eggs 20/10'."""
import re
from datetime import date, timedelta

DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


def parse_date(token, today):
    t = token.lower()
    if t in ('today', 'leo'):
        return today
    if t in ('tomorrow', 'kesho'):
        return today + timedelta(days=1)
    if t[:3] in DAYS and len(t) <= 9:
        ahead = (DAYS.index(t[:3]) - today.weekday()) % 7 or 7
        return today + timedelta(days=ahead)
    m = re.fullmatch(r'(\d{1,2})[/-](\d{1,2})', t)
    if m:
        day, month = int(m[1]), int(m[2])
        try:
            d = date(today.year, month, day)
        except ValueError:
            return None
        return d if d >= today else date(today.year + 1, month, day)
    return None


def parse(text, today=None):
    """Returns dict(name, phone, amount, description, due_date) or None if no amount found."""
    today = today or date.today()
    tokens = text.split()
    phone, amount, due, name, desc = '', None, None, [], []
    for tok in tokens:
        digits = tok.replace(',', '')
        if not phone and re.fullmatch(r'(\+?254|0)[17]\d{8}', digits):
            phone = digits
        elif amount is None and re.fullmatch(r'\d+(\.\d+)?k?', digits.lower()):
            amount = float(digits.lower().rstrip('k')) * (1000 if digits.lower().endswith('k') else 1)
        elif due is None and parse_date(tok, today):
            due = parse_date(tok, today)
        elif amount is None:
            name.append(tok)
        else:
            desc.append(tok)
    if amount is None or not name:
        return None
    return {'name': ' '.join(name), 'phone': phone, 'amount': amount,
            'description': ' '.join(desc) or 'Goods supplied',
            'due_date': due or today + timedelta(days=7)}
