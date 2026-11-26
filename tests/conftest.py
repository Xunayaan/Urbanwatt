import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """Client HTTP de test : appelle l'API en mémoire, sans lancer uvicorn.

    ATTENTION : les tests utilisent la base définie par DATABASE_URL.
    Ils créent leurs propres données (suffixe aléatoire) et les suppriment à la fin.
    """
    with TestClient(app) as c:
        yield c
