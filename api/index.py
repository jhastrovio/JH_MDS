from __future__ import annotations

from mangum import Mangum

from .auth import app   # ← import the FastAPI instance you actually created
handler = Mangum(app)


