"""Minimal API for testing Vercel deployment."""

try:
    from fastapi import FastAPI
    from mangum import Mangum
    
    # Create minimal app
    app = FastAPI(title="Test API")
    
    @app.get("/")
    async def root():
        return {"message": "API is working", "status": "ok"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "Test API"}
    
    # Vercel handler
    handler = Mangum(app)
    
except Exception as e:
    # Fallback if imports fail
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": "Import failed: {str(e)}"}}'
        } 