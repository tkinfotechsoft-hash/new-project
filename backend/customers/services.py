from decimal import Decimal
from django.db import transaction
from django.contrib.auth.models import User
from .models import CustomerTransaction

class CustomerService:
    @staticmethod
    def create_transaction_and_jewel(customer, transaction_serializer, jewel_serializer):
        with transaction.atomic():
            customer_transaction = transaction_serializer.save(
                customer=customer,
                interest_amount=transaction_serializer.validated_data['amount'] * Decimal('0.025'),
            )
            jewel_serializer.save(transaction=customer_transaction)
            return customer_transaction

class AuthService:
    @staticmethod
    def get_system_user():
        return User.objects.first()

    @staticmethod
    def update_password(user, new_password):
        user.set_password(new_password)
        user.save()

    @staticmethod
    def verify_password(user, password):
        return user.check_password(password)
