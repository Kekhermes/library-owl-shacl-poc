from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .core.database import Base, engine
from .routes.views import router as views_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée les tables si la base de données est accessible
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield


app = FastAPI(
    title="Médiathèque Sémantique : Fullstack PostgreSQL + SHACL",
    description="Application d'apprentissage pour la gestion d'une A-Box dans PostgreSQL avec validation SHACL Core et inférence SHACL-AF.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(views_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.src.main:app", host="0.0.0.0", port=8000, reload=True)
