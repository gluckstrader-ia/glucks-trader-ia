from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.routes.analyze import router as analyze_router
from app.api.routes.radar import router as radar_router
from app.core.config import API_V1_PREFIX, APP_NAME, APP_VERSION, FRONTEND_ORIGINS
from app.database import Base, engine
#from app.api.payments import router as payments_router
from app.api.news import router as news_router
from app.api.admin import router as admin_router
from app.api.webhook import router as webhook_router
from app.api.market_data import router as market_data_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(analyze_router, prefix=API_V1_PREFIX)
app.include_router(radar_router, prefix=API_V1_PREFIX)
#app.include_router(payments_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")
app.include_router(market_data_router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": f"{APP_NAME} online",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
    }
