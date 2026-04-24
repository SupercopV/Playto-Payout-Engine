from django.urls import path
from .views import MerchantBalanceView, PayoutCreateView, PayoutListView

urlpatterns = [
    path('merchant/<int:merchant_id>/balance/', MerchantBalanceView.as_view(), name='merchant-balance'),
    path('merchant/<int:merchant_id>/payouts/', PayoutListView.as_view(), name='merchant-payouts'),
    path('payouts/', PayoutCreateView.as_view(), name='payout-create'),
]
