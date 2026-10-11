from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import quickadd, reminders
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


def _create_invoice(user, name, phone, description, amount, due_date):
    debtor = Debtor.objects.filter(owner=user, name__iexact=name).first()
    if debtor is None:
        debtor = Debtor.objects.create(owner=user, name=name, phone=phone)
    elif phone and not debtor.phone:
        debtor.phone = phone
        debtor.save()
    return Invoice.objects.create(debtor=debtor, description=description,
                                  amount=amount, due_date=due_date)


@login_required
def add_invoice(request):
    form = InvoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        inv = _create_invoice(request.user, cd['debtor_name'].strip(), cd['phone'],
                              cd['description'], cd['amount'], cd['due_date'])
        return redirect('invoice', pk=inv.pk)
    names = Debtor.objects.filter(owner=request.user).values_list('name', flat=True)
    return render(request, 'add.html', {'form': form, 'names': names})


@login_required
@require_POST
def quick_add(request):
    parsed = quickadd.parse(request.POST.get('line', ''))
    if not parsed:
        messages.error(request, 'Could not read that. Try: Kamau Hotel 18500 milk fri')
        return redirect('dashboard')
    inv = _create_invoice(request.user, parsed['name'], parsed['phone'],
                          parsed['description'], parsed['amount'], parsed['due_date'])
    return redirect('invoice', pk=inv.pk)


def signup(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('settings')
    return render(request, 'registration/signup.html', {'form': form})


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
