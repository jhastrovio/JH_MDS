# backend/models/market.py

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: datetime  # ISO 8601 string ↔ datetime

class Tick(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
