#!/usr/bin/env python3
"""
RiskShield AI — Bulk Demo Seed
Generates 100+ realistic transactions for convincing pitch video demo.
"""
import json
import random
import urllib.request
import time

BASE = "http://localhost:8000"
ADMIN_KEY = "riskshield-admin-8KGMzLQdmvfiYcoQ3fTS_Q"

def api(method, path, data=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("=== RiskShield AI — Bulk Demo Seed ===\n")

# Register merchant
reg = api("POST", "/api/v1/auth/register", {"name": "QuickComerce", "email": f"demo{int(time.time())}@quickcommerce.in"})
MERCHANT_KEY = reg.get("api_key")
if not MERCHANT_KEY:
    print(f"Registration failed: {reg}")
    exit(1)
print(f"Merchant: QuickComerce | API Key: {MERCHANT_KEY}\n")

safe_customers = [f"cust_{i:04d}" for i in range(1, 81)]
fraud_customers = [f"fraud_{i:04d}" for i in range(1, 21)]

# --- SAFE TRANSACTIONS (80) ---
print("Scoring 80 SAFE transactions...")
safe_count = 0
for i in range(80):
    amount = round(random.uniform(100, 15000), 2)
    txn = {
        "transaction_id": f"TXN_S{i+1:04d}",
        "amount": amount,
        "currency": "INR",
        "merchant_id": "qm1",
        "customer_id": random.choice(safe_customers),
        "card_number": "4111111111111111",
        "payment_method": "card",
    }
    r = api("POST", "/api/v1/transactions", txn, {"X-API-Key": MERCHANT_KEY})
    if "data" in r:
        safe_count += 1
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/80 done...")
    time.sleep(0.05)

print(f"  {safe_count} safe transactions scored\n")

# --- FRAUD TRANSACTIONS (20) ---
print("Scoring 20 FRAUD transactions...")
fraud_count = 0
for i in range(20):
    amount = round(random.uniform(30000, 150000), 2)
    signals = random.choice([
        {"is_international": True, "customer_account_age_days": 1, "customer_total_transactions": 1,
         "shipping_address_match": False, "device_fingerprint_reused": True},
        {"is_international": True, "customer_account_age_days": 3, "customer_total_transactions": 2,
         "shipping_address_match": False, "device_fingerprint_reused": True},
        {"is_international": True, "customer_account_age_days": 2, "customer_total_transactions": 1,
         "shipping_address_match": False, "device_fingerprint_reused": True, "hour_of_day": 3},
    ])
    txn = {
        "transaction_id": f"TXN_F{i+1:04d}",
        "amount": amount,
        "currency": random.choice(["INR", "USD", "EUR", "GBP"]),
        "merchant_id": "qm1",
        "customer_id": random.choice(fraud_customers),
        "card_number": "4111111111111111",
        "payment_method": "card",
        **signals,
    }
    r = api("POST", "/api/v1/transactions", txn, {"X-API-Key": MERCHANT_KEY})
    if r.get("data", {}).get("is_flagged"):
        fraud_count += 1
    if (i + 1) % 5 == 0:
        print(f"  {i+1}/20 done...")
    time.sleep(0.05)

print(f"  {fraud_count} fraud transactions flagged\n")

# --- DASHBOARD ---
print("=== Final Dashboard ===")
dash = api("GET", "/api/v1/analytics/dashboard", headers={"X-API-Key": ADMIN_KEY})
d = dash.get("data", {})
print(f"  Total transactions: {d.get('total_transactions', 0)}")
print(f"  Flagged (fraud): {d.get('flagged_transactions', 0)}")
print(f"  Fraud rate: {d.get('fraud_rate', 0):.1f}%")
print(f"  Avg risk score: {d.get('avg_risk_score', 0):.4f}")
print(f"  Potential savings: ₹{d.get('potential_savings', 0):,.0f}")

alerts = api("GET", "/api/v1/alerts", headers={"X-API-Key": ADMIN_KEY})
print(f"  Active alerts: {alerts.get('total', 0)}")

print(f"\n=== Demo ready! Open http://localhost:5173 ===")
print(f"   API Key: {MERCHANT_KEY}")
