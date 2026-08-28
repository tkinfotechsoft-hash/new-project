import random
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from customers.models import Customer, Installment
from customers.serializers import CustomerSerializer

customers_seed = [
    ("Rahul Sharma", "Suresh Sharma", "9876543210", 15000, "Gold", "Necklace", 25.5, "916 Hallmark"),
    ("Priya Patel", "Ramesh Patel", "9876543211", 5000, "Silver", "Anklets", 150.0, "92.5 Sterling"),
    ("Amit Singh", "Vijay Singh", "9876543212", 25000, "Gold", "Bangles", 40.2, "916 Hallmark"),
    ("Sneha Reddy", "Prakash Reddy", "9876543213", 12000, "Gold", "Ring", 10.5, "22K"),
    ("Karthik Iyer", "Venkat Iyer", "9876543214", 8000, "Silver", "Silver Coins", 50.0, "999 Fine")
]

for name, guardian, phone, amount, metal, item, weight, purity in customers_seed:
    date_str = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
    data = {
        "sno": str(random.randint(100, 999)),
        "ano": str(random.randint(100, 999)),
        "amount": str(amount),
        "date": date_str,
        "customer_name": name,
        "guardian_name": guardian,
        "phone": phone,
        "customer_id_no": f"CUST{random.randint(1000, 9999)}",
        "address": f"{random.randint(1, 99)} Block",
        "item_type": item,
        "metal_type": metal,
        "purity": purity,
        "weight": str(weight),
        "num_stones": random.randint(0, 5),
        "remark": "Dummy ORM data",
        "interest_rate": "2.5",
        "tenure": "12"
    }

    serializer = CustomerSerializer(data=data)
    if serializer.is_valid():
        customer = serializer.save()
        # replicate perform_create logic
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
            due_date = customer.date + relativedelta(months=i)
            
            if i == tenure:
                principal_due = principal - accumulated_principal
            else:
                principal_due = base_principal_due
                
            accumulated_principal += principal_due
            total_due = principal_due + monthly_interest
            
            Installment.objects.create(
                customer=customer,
                month_number=i,
                due_date=due_date,
                principal_due=principal_due,
                interest_due=monthly_interest,
                total_due=total_due,
                status='Pending'
            )
        print(f"Seeded: {name}")
    else:
        print(serializer.errors)
