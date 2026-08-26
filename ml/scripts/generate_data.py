import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

np.random.seed(42)

N = 50000
FRAUD_RATE = 0.04

MERCHANT_CATEGORIES = [
    "electronics", "fashion", "food_delivery", "travel", "digital_goods",
    "groceries", "healthcare", "education", "entertainment", "utilities"
]
CARD_TYPES = ["credit", "debit", "upi", "netbanking"]
CARD_NETWORKS = ["visa", "mastercard", "rupay"]
COUNTRIES = ["IN", "US", "GB", "AE", "SG", "DE", "FR", "AU", "CA", "JP"]
DEVICE_IDS = [f"dev_{i:05d}" for i in range(5000)]

def generate_transactions(n: int) -> pd.DataFrame:
    records = []
    fraud_count = int(n * FRAUD_RATE)
    labels = np.zeros(n, dtype=int)
    fraud_indices = np.random.choice(n, fraud_count, replace=False)
    labels[fraud_indices] = 1

    for i in range(n):
        is_fraud = labels[i] == 1
        merchant_id = f"M{np.random.randint(1, 500):04d}"
        customer_id = f"C{np.random.randint(1, 2000):05d}"

        if is_fraud:
            amount = round(np.random.lognormal(mean=7.5, sigma=1.5), 2)
            hour = np.random.choice([0, 1, 2, 3, 4, 5, 23], p=[0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.2])
            day_of_week = np.random.randint(0, 7)
            card_type = np.random.choice(CARD_TYPES, p=[0.4, 0.2, 0.2, 0.2])
            card_network = np.random.choice(CARD_NETWORKS, p=[0.3, 0.35, 0.35])
            is_international = np.random.choice([0, 1], p=[0.3, 0.7])
            country_code = np.random.choice(COUNTRIES, p=[0.15, 0.25, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.1])
            customer_account_age = np.random.randint(1, 90)
            customer_total_txn = np.random.randint(1, 15)
            merchant_avg_ticket = round(np.random.uniform(500, 5000), 2)
            shipping_match = np.random.choice([0, 1], p=[0.6, 0.4])
            device_reused = np.random.choice([0, 1], p=[0.2, 0.8])
            probs = np.array([0.3, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.05])
            merchant_category = np.random.choice(MERCHANT_CATEGORIES, p=probs / probs.sum())
        else:
            amount = round(np.random.lognormal(mean=5.5, sigma=1.2), 2)
            hour = np.random.choice(range(24))
            day_of_week = np.random.randint(0, 7)
            card_type = np.random.choice(CARD_TYPES, p=[0.35, 0.35, 0.2, 0.1])
            card_network = np.random.choice(CARD_NETWORKS, p=[0.4, 0.35, 0.25])
            is_international = np.random.choice([0, 1], p=[0.85, 0.15])
            country_code = "IN" if not is_international else np.random.choice(["US", "GB", "AE", "SG"])
            customer_account_age = np.random.randint(30, 2000)
            customer_total_txn = np.random.randint(5, 500)
            merchant_avg_ticket = round(np.random.uniform(200, 3000), 2)
            shipping_match = np.random.choice([0, 1], p=[0.15, 0.85])
            device_reused = np.random.choice([0, 1], p=[0.7, 0.3])
            merchant_category = np.random.choice(MERCHANT_CATEGORIES)

        amount = min(amount, 500000)
        base_date = datetime(2026, 1, 1)
        txn_date = base_date + timedelta(days=np.random.randint(0, 180), hours=int(hour), minutes=np.random.randint(0, 60))

        records.append({
            "transaction_id": f"TXN{i:08d}",
            "amount": amount,
            "currency": "INR",
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "timestamp": txn_date.isoformat(),
            "hour_of_day": int(hour),
            "day_of_week": int(day_of_week),
            "card_type": card_type,
            "card_network": card_network,
            "is_international": int(is_international),
            "country_code": country_code,
            "customer_account_age_days": int(customer_account_age),
            "customer_total_transactions": int(customer_total_txn),
            "merchant_category_code": merchant_category,
            "merchant_avg_ticket_size": float(merchant_avg_ticket),
            "shipping_address_match": int(shipping_match),
            "device_fingerprint_reused": int(device_reused),
            "is_fraud": int(is_fraud),
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    df = generate_transactions(N)
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "transactions.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} transactions -> {out_path}")
    print(f"Fraud rate: {df['is_fraud'].mean():.2%}")
    print(f"Columns: {list(df.columns)}")
