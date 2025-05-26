from mangum import Mangum

# Pull in the single FastAPI “app” you defined at the package root
from . import app

# Enable api_gateway mode so Vercel passes the full /api/... path through
handler = Mangum(app, api_gateway=True)