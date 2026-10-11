from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import reminders
from .forms import InvoiceForm, PaymentForm, ProfileForm
from .models import Debtor, Invoice, Profile, Reminder


def _profile(user):
    return Profile.objects.get_or_create(user=user)[0]


@login_required
def dashboard(request):
    invoices = [i for i in Invoice.objects.filter(debtor__owner=request.user)
                .select_related('debtor') if not i.is_settled]
    today = date.today()
    overdue = sorted((i for i in invoices if i.due_date < today),
                     key=lambda i: -i.days_overdue)
    week = [i for i in invoices if today <= i.due_date <= today + timedelta(days=7)]
    later = [i for i in invoices if i.due_date > today + timedelta(days=7)]

    def total(xs):
        return sum((i.balance for i in xs), Decimal('0'))

    return render(request, 'dashboard.html', {
        'overdue': overdue, 'week': week, 'later': later,
        'total_owed': total(invoices), 'total_overdue': total(overdue),
        'total_week': total(week),
    })


@login_required
def add_invoice(request):
    form = InvoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        name = cd['debtor_name'].strip()
        debtor = Debtor.objects.filter(owner=request.user, name__iexact=name).first()
        if debtor is None:
            debtor = Debtor.objects.create(owner=request.user, name=name, phone=cd['phone'])
        elif cd['phone'] and not debtor.phone:
            debtor.phone = cd['phone']
            debtor.save()
        inv = Invoice.objects.create(debtor=debtor, description=cd['description'],
                                     amount=cd['amount'], due_date=cd['due_date'])
        return redirect('invoice', pk=inv.pk)
    names = Debtor.objects.filter(owner=request.user).values_list('name', flat=True)
    return render(request, 'add.html', {'form': form, 'names': names})


@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, debtor__owner=request.user)
    pform = PaymentForm(request.POST or None, initial={'amount': inv.balance})
    if request.method == 'POST' and pform.is_valid():
        p = pform.save(commit=False)
        p.invoice = inv
        p.save()
        return redirect('invoice', pk=inv.pk)
    tone, text = reminders.draft(inv, _profile(request.user))
    return render(request, 'invoice.html', {
        'inv': inv, 'pform': pform, 'tone': tone, 'text': text,
        'wa': reminders.whatsapp_link(inv.debtor.phone, text),
    })


@login_required
@require_POST
def mark_sent(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, debtor__owner=request.user)
    Reminder.objects.create(invoice=inv, tone=reminders.pick_tone(inv.days_overdue))
    return redirect('invoice', pk=inv.pk)


@login_required
def debtors(request):
    rows = [(d, d.outstanding(), d.avg_days_late())
            for d in Debtor.objects.filter(owner=request.user)
            .prefetch_related('invoices__payments')]
    rows.sort(key=lambda r: -r[1])
    return render(request, 'debtors.html', {'rows': rows})


@login_required
def settings_view(request):
    form = ProfileForm(request.POST or None, instance=_profile(request.user))
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'settings.html', {'form': form})
