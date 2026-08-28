from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta
from .models import Customer, CustomerTransaction, UserProfile, Installment, Payment
from .serializers import CustomerSerializer, CustomerTransactionSerializer, JewelDetailSerializer, UserProfileSerializer
from .services import CustomerService, AuthService

class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def perform_create(self, serializer):
        customer = serializer.save()
        
        principal = Decimal(customer.amount)
        rate = Decimal(customer.interest_rate)
        tenure = int(customer.tenure)
        
        monthly_interest = round(principal * rate / Decimal('100.0'), 2)
        total_interest = monthly_interest * tenure
        customer.total_interest = total_interest
        customer.total_payable = principal + total_interest
        customer.save()

        base_principal_due = round(principal / Decimal(tenure), 2)
        accumulated_principal = Decimal('0.00')

        for i in range(1, tenure + 1):
            # Due date is exactly that many months ahead minus 1 day
            due_date = customer.date + relativedelta(months=i) - relativedelta(days=1)
            
            if i == tenure:
                principal_due = principal - accumulated_principal
            else:
                principal_due = base_principal_due
                
            accumulated_principal += principal_due
            total_due = principal_due + monthly_interest
            
            # For the first month, the interest is collected upfront per business rules
            if i == 1:
                inst_amount_paid = monthly_interest
                inst_status = 'Partially Paid' if principal_due > 0 else 'Paid'
            else:
                inst_amount_paid = Decimal('0.00')
                inst_status = 'Pending'
            
            Installment.objects.create(
                customer=customer,
                month_number=i,
                due_date=due_date,
                principal_due=principal_due,
                interest_due=monthly_interest,
                total_due=total_due,
                amount_paid=inst_amount_paid,
                status=inst_status
            )

        # Create the upfront payment record for Month 1 Interest Deduction
        Payment.objects.create(
            customer=customer,
            payment_amount=monthly_interest,
            principal_portion=Decimal('0.00'),
            interest_portion=monthly_interest,
            payment_date=customer.date,
            payment_mode="Upfront Deduction",
            remarks="First month interest deducted at loan disbursement"
        )
        
        customer.amount_paid = monthly_interest
        customer.save()

class CustomerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class PaymentCreateAPIView(APIView):
    @transaction.atomic
    def post(self, request, customer_pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=customer_pk)
        payment_amount = Decimal(str(request.data.get('payment_amount', '0')))
        
        if payment_amount <= 0:
            return Response({"error": "Payment amount must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
            
        payment_date = request.data.get('payment_date')
        
        outstanding_balance = customer.total_payable - customer.amount_paid
        if payment_amount > outstanding_balance:
            return Response({"error": "Payment exceeds outstanding balance"}, status=status.HTTP_400_BAD_REQUEST)

        # Allocate payment strictly sequentially across unpaid installments (Interest -> Principal)
        remaining_payment = payment_amount
        total_principal_paid = Decimal('0.00')
        total_interest_paid = Decimal('0.00')
        
        installments = customer.installments.exclude(status='Paid').order_by('month_number')
        
        for inst in installments:
            if remaining_payment <= 0:
                break
                
            inst_interest_unpaid = inst.interest_due - (inst.amount_paid - (inst.total_due - inst.interest_due)) # Simplified allocation below
            
            # Since tracking explicitly interest vs principal at installment level requires tracking what we paid so far per installment:
            # Let's cleanly separate what was paid towards interest vs principal on this installment.
            # Assuming previous payments allocated correctly, we recalculate unpaid portion:
            # Paid so far on this installment:
            prev_paid = inst.amount_paid
            
            # Allocation rule: Interest First
            prev_interest_paid = min(prev_paid, inst.interest_due)
            prev_principal_paid = prev_paid - prev_interest_paid
            
            unpaid_interest = inst.interest_due - prev_interest_paid
            unpaid_principal = inst.principal_due - prev_principal_paid
            
            # 1. Pay Interest
            paying_interest = min(unpaid_interest, remaining_payment)
            remaining_payment -= paying_interest
            total_interest_paid += paying_interest
            
            # 2. Pay Principal
            paying_principal = min(unpaid_principal, remaining_payment)
            remaining_payment -= paying_principal
            total_principal_paid += paying_principal
            
            # Update installment
            inst.amount_paid += (paying_interest + paying_principal)
            
            if inst.amount_paid >= inst.total_due:
                inst.status = 'Paid'
            elif inst.amount_paid > 0:
                inst.status = 'Partially Paid'
            
            inst.save()

        # Create payment record
        Payment.objects.create(
            customer=customer,
            payment_amount=payment_amount,
            principal_portion=total_principal_paid,
            interest_portion=total_interest_paid,
            payment_date=payment_date,
            payment_mode=request.data.get('payment_mode', 'Cash'),
            reference_number=request.data.get('reference_number', ''),
            remarks=request.data.get('remarks', '')
        )
        
        customer.amount_paid += payment_amount
        if customer.amount_paid >= customer.total_payable:
            customer.status = 'Completed'
        customer.save()
        
        return Response({"message": "Payment recorded successfully", "outstanding_balance": outstanding_balance - payment_amount}, status=status.HTTP_201_CREATED)


class CustomerTransactionListCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, customer_pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=customer_pk)
        transaction_serializer = CustomerTransactionSerializer(data=request.data)
        jewel_serializer = JewelDetailSerializer(data=request.data)

        transaction_is_valid = transaction_serializer.is_valid()
        jewel_is_valid = jewel_serializer.is_valid()
        if not transaction_is_valid or not jewel_is_valid:
            return Response(
                {
                    'transaction': transaction_serializer.errors,
                    'jewel': jewel_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer_transaction = CustomerService.create_transaction_and_jewel(
            customer=customer,
            transaction_serializer=transaction_serializer,
            jewel_serializer=jewel_serializer
        )

        return Response(CustomerTransactionSerializer(customer_transaction).data, status=status.HTTP_201_CREATED)


class CustomerTransactionDestroyView(generics.DestroyAPIView):
    queryset = CustomerTransaction.objects.all()
    serializer_class = CustomerTransactionSerializer


class UserProfileView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(id=1)
        return profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ChangePasswordView(APIView):
    def post(self, request, *args, **kwargs):
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"error": "New password is required"}, status=400)
            
        # For a single-tenant admin dashboard, we just update the first superuser or user
        user = AuthService.get_system_user()
        if not user:
            return Response({"error": "No user found in the system"}, status=404)
            
        AuthService.update_password(user, new_password)
        return Response({"message": "Password updated successfully"})

class VerifyPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        old_password = request.data.get("old_password")
        if not old_password:
            return Response({"error": "Old password is required"}, status=400)
            
        user = AuthService.get_system_user()
        if not user:
            return Response({"error": "No user found in the system"}, status=404)
            
        if AuthService.verify_password(user, old_password):
            return Response({"valid": True})
        else:
            return Response({"valid": False})
