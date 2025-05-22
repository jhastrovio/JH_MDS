from fastapi import APIRouter

from .price import router as price_router
from .ticks import router as ticks_router
from .snapshot import router as snapshot_router

router = APIRouter()
router.include_router(price_router)
router.include_router(ticks_router)
router.include_router(snapshot_router)
