from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('quick/', views.quick_add, name='quick'),
    path('signup/', views.signup, name='signup'),
    path('add/', views.add_invoice, name='add'),
    path('invoice/<int:pk>/', views.invoice_detail, name='invoice'),
    path('invoice/<int:pk>/sent/', views.mark_sent, name='sent'),
    path('debtors/', views.debtors, name='debtors'),
    path('settings/', views.settings_view, name='settings'),
]
