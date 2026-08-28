from django.urls import path
from .views import ChangePasswordView, CustomerListCreateView, CustomerRetrieveUpdateDestroyView, CustomerTransactionDestroyView, CustomerTransactionListCreateView, UserProfileView, VerifyPasswordView, PaymentCreateAPIView

urlpatterns = [
    path('customers/', CustomerListCreateView.as_view(), name='customer-list-create'),
    path('customers/<int:pk>/', CustomerRetrieveUpdateDestroyView.as_view(), name='customer-detail'),
    path('customers/<int:customer_pk>/payments/', PaymentCreateAPIView.as_view(), name='customer-payment-create'),
    path('customers/<int:customer_pk>/transactions/', CustomerTransactionListCreateView.as_view(), name='customer-transaction-list-create'),
    path('transactions/<int:pk>/', CustomerTransactionDestroyView.as_view(), name='customer-transaction-delete'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('verify-password/', VerifyPasswordView.as_view(), name='verify-password'),
]
