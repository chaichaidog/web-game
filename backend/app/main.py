from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, SessionLocal, get_db, DATABASE_URL
from .models import Achievement
from .seed import seed_database
from .routers import players, levels, rooms, teacher


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(levels.router)
app.include_router(rooms.router)
app.include_router(teacher.router)


@app.get("/api/health")
def health_check():
    db_engine = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_engine": db_engine,
    }


@app.get("/api/achievements")
def list_achievements(db: Session = Depends(get_db)):
    rows = db.query(Achievement).all()
    return {
        "achievements": [
            {
                "achievement_code": a.achievement_code,
                "name": a.name,
                "description": a.description,
                "category": a.category,
                "reward_type": a.reward_type,
                "reward_value": a.reward_value,
                "xp_reward": a.xp_reward,
            }
            for a in rows
        ]
    }

