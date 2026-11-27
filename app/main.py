from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import register_error_handlers
from app.routers import (
    bornes,
    clients,
    incidents,
    interventions,
    paiements,
    sessions,
    stats,
    stations,
    techniciens,
    vehicules,
)

app = FastAPI(
    title="API Bornes de recharge",
    description=(
        "API REST au-dessus d'une base PostgreSQL de gestion de bornes de recharge "
        "de véhicules électriques : clients, véhicules, stations, bornes, sessions, "
        "paiements, incidents et interventions."
    ),
    version="1.0.0",
)

register_error_handlers(app)

# CORS : autorise l'interface web (servie sur une autre origine en développement) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    clients,
    vehicules,
    stations,
    bornes,
    sessions,
    paiements,
    incidents,
    techniciens,
    interventions,
    stats,
):
    app.include_router(module.router)


@app.get("/", tags=["Général"])
def accueil():
    return {"message": "API Bornes de recharge", "documentation": "/docs"}


@app.get("/health", tags=["Général"])
def health(db: Session = Depends(get_db)):
    """Vérifie que l'API joint bien la base de données."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
