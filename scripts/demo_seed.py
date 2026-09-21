#!/usr/bin/env python3
"""
RiskShield AI — Demo Seed Script
Runs against the live API to populate dashboard data for pitch video.
"""
import json
import hmac
import hashlib
import urllib.request

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
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

print("=== RiskShield AI Demo Setup ===\n")

# 1. Register demo merchant
print("1. Registering merchant...")
reg = api("POST", "/api/v1/auth/register", {"name": "Acme Electronics", "email": "demo@acme.com"})
MERCHANT_KEY = reg["api_key"]
print(f"   API Key: {MERCHANT_KEY}")
print(f"   Merchant ID: {reg['merchant_id']}")

# 2. Score safe transactions
print("\n2. Scoring safe transactions...")
safe_txns = [
    {"transaction_id": "SAFE_001", "amount": 499, "currency": "INR", "merchant_id": "m1", "customer_id": "c1"},
    {"transaction_id": "SAFE_002", "amount": 1200, "currency": "INR", "merchant_id": "m1", "customer_id": "c2"},
    {"transaction_id": "SAFE_003", "amount": 350, "currency": "INR", "merchant_id": "m1", "customer_id": "c3"},
    {"transaction_id": "SAFE_004", "amount": 2500, "currency": "INR", "merchant_id": "m1", "customer_id": "c4"},
    {"transaction_id": "SAFE_005", "amount": 899, "currency": "INR", "merchant_id": "m1", "customer_id": "c5"},
]
for t in safe_txns:
    r = api("POST", "/api/v1/transactions", t, {"X-API-Key": MERCHANT_KEY})
    score = r.get("data", {}).get("risk_score", "?")
    print(f"   {t['transaction_id']}: score={score} (safe)")

# 3. Score fraud transactions
print("\n3. Scoring fraud transactions...")
fraud_txns = [
    {"transaction_id": "FRAUD_001", "amount": 99999, "currency": "INR", "merchant_id": "m1", "customer_id": "c6",
     "is_international": True, "customer_account_age_days": 2, "customer_total_transactions": 1,
     "shipping_address_match": False, "device_fingerprint_reused": True},
    {"transaction_id": "FRAUD_002", "amount": 75000, "currency": "USD", "merchant_id": "m1", "customer_id": "c7",
     "is_international": True, "customer_account_age_days": 1, "customer_total_transactions": 1,
     "shipping_address_match": False, "device_fingerprint_reused": True},
    {"transaction_id": "FRAUD_003", "amount": 50000, "currency": "INR", "merchant_id": "m1", "customer_id": "c8",
     "is_international": True, "customer_account_age_days": 3, "customer_total_transactions": 2,
     "shipping_address_match": False, "device_fingerprint_reused": True},
]
for t in fraud_txns:
    r = api("POST", "/api/v1/transactions", t, {"X-API-Key": MERCHANT_KEY})
    score = r.get("data", {}).get("risk_score", "?")
    flagged = r.get("data", {}).get("is_flagged", "?")
    print(f"   {t['transaction_id']}: score={score} flagged={flagged}")

# 4. Send test webhook
print("\n4. Sending test Razorpay webhook...")
secret = "riskshield_test_secret_2026"
payload = json.dumps({
    "event": "payment.captured",
    "payload": {"payment": {"entity": {"id": "pay_demo_001", "order_id": "order_demo", "amount": 49900, "currency": "INR"}}}
}).encode()
sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
wh = api("POST", "/api/v1/webhooks/razorpay", json.loads(payload), {"X-Razorpay-Signature": sig})
print(f"   Webhook: {wh.get('status', 'error')}")

# 5. Dashboard
print("\n5. Dashboard summary:")
dash = api("GET", "/api/v1/analytics/dashboard", headers={"X-API-Key": ADMIN_KEY})
d = dash.get("data", {})
print(f"   Total transactions: {d.get('total_transactions', 0)}")
print(f"   Flagged: {d.get('flagged_transactions', 0)}")
print(f"   Fraud rate: {d.get('fraud_rate', 0)}%")
print(f"   Potential savings: ₹{d.get('potential_savings', 0):,.0f}")

print("\n=== Demo ready! Open http://localhost:5173 ===")
print(f"   Use API key: {MERCHANT_KEY}")
