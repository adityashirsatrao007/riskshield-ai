from typing import Optional, Literal
from pydantic import BaseModel, Field, conlist


class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1, max_length=32)
    amount: float = Field(..., gt=0, le=10000000)
    currency: str = Field(default="INR", max_length=3)
    merchant_id: str = Field(..., min_length=1, max_length=16)
    customer_id: str = Field(..., min_length=1, max_length=16)
    timestamp: Optional[str] = None
    card_type: str = Field(default="credit", max_length=16)
    card_network: str = Field(default="visa", max_length=16)
    is_international: bool = False
    country_code: str = Field(default="IN", max_length=2)
    customer_account_age_days: int = Field(default=100, ge=0)
    customer_total_transactions: int = Field(default=10, ge=0)
    merchant_category_code: str = Field(default="electronics", max_length=32)
    merchant_avg_ticket_size: float = Field(default=1000.0, gt=0)
    shipping_address_match: bool = True
    device_fingerprint_reused: bool = False


class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "dismissed", "resolved"]


class BatchTransaction(BaseModel):
    transactions: conlist(TransactionCreate, max_length=100)
