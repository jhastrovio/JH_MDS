from __future__ import annotations

from mangum import Mangum
from . import app

# Create handler for Vercel
handler = Mangum(app) 