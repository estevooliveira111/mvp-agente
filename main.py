from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.config import settings
from routers import auth, users
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(
    title="Authentication API",
    description="A complete REST API for authentication using Python, FastAPI, and JWT.",
    version="1.0.0",
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)

# Custom Exception Handlers for consistent JSON responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"message": "Validation Error", "details": exc.errors()},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"message": "Database Error", "details": "An internal database error occurred."},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc) if settings.ENVIRONMENT == "development" else "Unexpected error occurred."},
    )

@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
