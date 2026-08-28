import urllib.request
import json
import random
from datetime import datetime, timedelta

def create_customer(name, guardian, phone, amount, metal_type, item_type, weight, purity):
    url = "http://127.0.0.1:8000/api/customers/"
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
        "address": f"{random.randint(1, 99)} Block, City Center",
        "item_type": item_type,
        "metal_type": metal_type,
        "purity": purity,
        "weight": str(weight),
        "num_stones": random.randint(0, 5),
        "remark": "Dummy transaction seeded for testing",
        "interest_rate": "2.5",
        "tenure": "12"
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req)
        print(f"Created Customer: {name} | Amount: {amount} | Status: {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} for {name}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")

customers = [
    ("Rajesh Kumar", "Surendra Kumar", "9876543210", 15000, "Gold", "Necklace", 25.5, "916 Hallmark"),
    ("Priya Sharma", "Ramesh Sharma", "9876543211", 5000, "Silver", "Anklets", 150.0, "92.5 Sterling"),
    ("Amit Singh", "Vijay Singh", "9876543212", 25000, "Gold", "Bangles", 40.2, "916 Hallmark"),
    ("Sneha Reddy", "Prakash Reddy", "9876543213", 12000, "Gold", "Ring", 10.5, "22K"),
    ("Karthik Iyer", "Venkat Iyer", "9876543214", 8000, "Silver", "Silver Items", 50.0, "999 Fine")
]

print("Starting to seed 5 dummy transactions via API...")
for c in customers:
    create_customer(*c)
print("Finished seeding.")
