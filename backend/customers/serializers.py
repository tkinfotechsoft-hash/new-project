from rest_framework import serializers
from .models import Customer, CustomerTransaction, JewelDetail, UserProfile, Installment, Payment

class InstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class CustomerSerializer(serializers.ModelSerializer):
    installments = InstallmentSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = '__all__'


class JewelDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = JewelDetail
        fields = '__all__'
        read_only_fields = ('id', 'transaction', 'created_at', 'updated_at')


class CustomerTransactionSerializer(serializers.ModelSerializer):
    jewel = JewelDetailSerializer(read_only=True)

    class Meta:
        model = CustomerTransaction
        fields = '__all__'
        read_only_fields = ('id', 'customer', 'interest_amount', 'created_at', 'updated_at')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
