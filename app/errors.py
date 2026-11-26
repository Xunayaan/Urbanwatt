"""Traduit les erreurs PostgreSQL en réponses HTTP lisibles.

Plutôt que de vérifier à la main chaque contrainte avant chaque écriture, on laisse
PostgreSQL être la source de vérité (UNIQUE, FOREIGN KEY, CHECK...) et on convertit
l'exception obtenue en code HTTP adapté.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

# code SQLSTATE PostgreSQL -> (code HTTP, message)
PG_ERREURS = {
    "23505": (409, "Valeur déjà existante (contrainte d'unicité)"),
    "23503": (409, "Contrainte de clé étrangère violée (référence inexistante ou ligne encore utilisée)"),
    "23502": (422, "Une valeur obligatoire est NULL"),
    "23514": (422, "Une contrainte CHECK de la base est violée"),
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        pgcode = getattr(exc.orig, "pgcode", None)
        http_status, message = PG_ERREURS.get(pgcode, (409, "Violation d'intégrité des données"))
        diag = getattr(exc.orig, "diag", None)
        return JSONResponse(
            status_code=http_status,
            content={
                "detail": message,
                "contrainte": getattr(diag, "constraint_name", None),
                "info": getattr(diag, "message_detail", None),
            },
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError):
        return JSONResponse(status_code=503, content={"detail": "Base de données indisponible"})
