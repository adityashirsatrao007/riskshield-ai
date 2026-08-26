#!/usr/bin/env python3
"""Seed realistic Indian payment transaction data into RiskShield AI."""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport

BASE_URL = "http://localhost:8000"
API_KEY = "demo-key-123"

MERCHANTS = [
    {"id": "mer_flipkart", "name": "Flipkart"},
    {"id": "mer_amazon", "name": "Amazon India"},
    {"id": "mer_ajio", "name": "AJIO"},
    {"id": "mer_myntra", "name": "Myntra"},
    {"id": "mer_swiggy", "name": "Swiggy"},
]

CATEGORIES = [
    "electronics", "fashion", "groceries", "food_delivery",
    "travel", "healthcare", "education", "entertainment", "utilities",
]

CARD_NETWORKS = ["visa", "mastercard", "rupay", "amex"]
CARD_TYPES = ["credit", "debit", "upi", "netbanking", "wallet"]

COUNTRIES = ["IN", "US", "GB", "AE", "SG", "DE", "FR", "AU", "JP", "CA"]
CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata",
    "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Solapur", "Nagpur", "Indore", "Bhopal", "Chandigarh",
]

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
]


def gen_card_number():
    prefix = random.choice(["4", "5", "6", "8"])
    return "".join([prefix] + [str(random.randint(0, 9)) for _ in range(15)])


def gen_ip(is_suspicious=False):
    if is_suspicious:
        return f"{random.choice([10, 172, 192])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    return f"{random.choice([49, 103, 106, 117, 14, 27, 49, 103])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def gen_normal_txns(base_time, count):
    txns = []
    for _ in range(count):
        merchant = random.choice(MERCHANTS)
        hours_ago = random.uniform(0, 168)
        ts = base_time - timedelta(hours=hours_ago)
        amount = round(random.lognormvariate(7.5, 1.2), 2)
        amount = max(50, min(amount, 50000))

        is_intl = random.random() < 0.05
        country = random.choice(COUNTRIES[1:]) if is_intl else "IN"

        acct_age = random.randint(30, 3650)
        total_txns = random.randint(5, 500)
        device_reuse = random.random() < 0.1
        ship_match = random.random() > 0.1

        txn = {
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "amount": amount,
            "currency": "INR",
            "merchant_id": merchant["id"],
            "customer_id": f"cust_{random.randint(1000, 9999)}",
            "timestamp": ts.isoformat(),
            "card_number": gen_card_number(),
            "card_type": random.choice(CARD_TYPES),
            "card_network": random.choice(CARD_NETWORKS),
            "is_international": is_intl,
            "country_code": country,
            "customer_account_age_days": acct_age,
            "customer_total_transactions": total_txns,
            "merchant_category_code": random.choice(CATEGORIES),
            "merchant_avg_ticket_size": round(random.uniform(200, 5000), 2),
            "shipping_address_match": ship_match,
            "device_fingerprint_reused": device_reuse,
        }
        txns.append(txn)
    return txns


def gen_suspicious_txns(base_time, count):
    txns = []
    for _ in range(count):
        merchant = random.choice(MERCHANTS)
        hours_ago = random.uniform(0, 48)
        ts = base_time - timedelta(hours=hours_ago)

        pattern = random.choice(["high_amount", "new_account", "intl_velocity", "card_stuffing"])

        if pattern == "high_amount":
            amount = round(random.uniform(80000, 950000), 2)
            acct_age = random.randint(1, 15)
            total_txns = random.randint(0, 3)
            is_intl = True
            country = random.choice(["US", "GB", "AE", "SG"])
            ship_match = False
            device_reuse = True
        elif pattern == "new_account":
            amount = round(random.uniform(15000, 80000), 2)
            acct_age = random.randint(0, 5)
            total_txns = random.randint(0, 2)
            is_intl = random.random() < 0.4
            country = random.choice(COUNTRIES)
            ship_match = False
            device_reuse = True
        elif pattern == "intl_velocity":
            amount = round(random.uniform(5000, 40000), 2)
            acct_age = random.randint(10, 200)
            total_txns = random.randint(50, 200)
            is_intl = True
            country = random.choice(["US", "CN", "RU", "NG"])
            ship_match = random.random() < 0.3
            device_reuse = True
        else:
            amount = round(random.uniform(500, 2000), 2)
            acct_age = random.randint(100, 2000)
            total_txns = random.randint(100, 400)
            is_intl = False
            country = "IN"
            ship_match = True
            device_reuse = True

        txn = {
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "amount": amount,
            "currency": "INR",
            "merchant_id": merchant["id"],
            "customer_id": f"cust_{random.randint(1000, 9999)}",
            "timestamp": ts.isoformat(),
            "card_number": gen_card_number(),
            "card_type": random.choice(CARD_TYPES),
            "card_network": random.choice(CARD_NETWORKS),
            "is_international": is_intl,
            "country_code": country,
            "customer_account_age_days": acct_age,
            "customer_total_transactions": total_txns,
            "merchant_category_code": random.choice(CATEGORIES),
            "merchant_avg_ticket_size": round(random.uniform(200, 5000), 2),
            "shipping_address_match": ship_match,
            "device_fingerprint_reused": device_reuse,
        }
        txns.append(txn)
    return txns


async def seed():
    base_time = datetime.now(timezone.utc)
    print("Generating 250 normal + 30 suspicious transactions...")

    all_txns = gen_normal_txns(base_time, 250) + gen_suspicious_txns(base_time, 30)
    random.shuffle(all_txns)

    BATCH_SIZE = 50
    flagged = 0
    total = 0

    async with AsyncClient(base_url=BASE_URL, timeout=60) as client:
        for i in range(0, len(all_txns), BATCH_SIZE):
            batch = all_txns[i : i + BATCH_SIZE]
            resp = await client.post(
                "/api/v1/transactions/batch",
                json={"transactions": batch},
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()["data"]
                scored = data["scored"]
                errors = len(data.get("errors", []))
                batch_flagged = sum(1 for r in data["results"] if r["is_flagged"])
                flagged += batch_flagged
                total += scored
                print(f"  Batch {i // BATCH_SIZE + 1}: {scored} scored, {batch_flagged} flagged, {errors} errors")
            else:
                print(f"  Batch {i // BATCH_SIZE + 1} FAILED: {resp.status_code} {resp.text[:200]}")

    print(f"\nDone! Total: {total} transactions scored, {flagged} flagged as fraud")
    print(f"Frontend: http://localhost:3000")
    print(f"API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
