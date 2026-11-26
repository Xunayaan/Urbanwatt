from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

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
