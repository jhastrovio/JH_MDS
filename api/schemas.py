from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: datetime


class Tick(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: datetime


class SnapshotRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1)
