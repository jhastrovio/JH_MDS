from __future__ import annotations

from pydantic import BaseModel


class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str


class Tick(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: str
