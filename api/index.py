from mangum import Mangum
from app.app import app    # ← grab the FastAPI instance you just created

# ensure the full /api/... path is preserved
handler = Mangum(app)
