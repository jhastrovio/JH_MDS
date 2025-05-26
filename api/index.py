from mangum import Mangum

# Pull in the single FastAPI "app" you defined at the package root
from . import app

# Create handler for Vercel
handler = Mangum(app)