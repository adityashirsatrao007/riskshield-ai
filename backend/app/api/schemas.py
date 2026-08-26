from typing import Optional, Literal
from pydantic import BaseModel, Field, conlist, field_validator
from datetime import datetime


VALID_CARD_TYPES = {"credit", "debit", "upi", "netbanking", "wallet", " prepaid"}
VALID_CARD_NETWORKS = {"visa", "mastercard", "amex", "rupay", "discover", "diners", "other"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}


class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1, max_length=64)
    amount: float = Field(..., gt=0, le=10_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    merchant_id: str = Field(..., min_length=1, max_length=64)
    customer_id: str = Field(..., min_length=1, max_length=64)
    timestamp: Optional[str] = None
    card_type: str = Field(default="credit", max_length=16)
    card_network: str = Field(default="visa", max_length=16)
    is_international: bool = False
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    customer_account_age_days: int = Field(default=100, ge=0, le=36500)
    customer_total_transactions: int = Field(default=10, ge=0, le=1_000_000)
    merchant_category_code: str = Field(default="electronics", max_length=64)
    merchant_avg_ticket_size: float = Field(default=1000.0, gt=0, le=10_000_000)
    shipping_address_match: bool = True
    device_fingerprint_reused: bool = False

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid ISO 8601 timestamp: {v}")
        return v

    @field_validator("card_type")
    @classmethod
    def validate_card_type(cls, v):
        if v.lower() not in VALID_CARD_TYPES:
            raise ValueError(f"card_type must be one of: {VALID_CARD_TYPES}")
        return v.lower()

    @field_validator("card_network")
    @classmethod
    def validate_card_network(cls, v):
        if v.lower() not in VALID_CARD_NETWORKS:
            raise ValueError(f"card_network must be one of: {VALID_CARD_NETWORKS}")
        return v.lower()

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v):
        if not v.isalpha() or not v.isupper():
            raise ValueError("country_code must be a 2-letter ISO 3166 uppercase code")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        if not v.isalpha() or not v.isupper():
            raise ValueError("currency must be a 3-letter ISO 4217 uppercase code")
        return v


class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "dismissed", "resolved"]
    notes: Optional[str] = Field(None, max_length=500)


class BatchTransaction(BaseModel):
    transactions: conlist(TransactionCreate, min_length=1, max_length=100)
