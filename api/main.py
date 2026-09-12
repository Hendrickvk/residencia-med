import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from api.routers import areas, auth, busca, materiais, me, painel, praticar, questoes, revisao, simulados, sincronizacao


@asynccontextmanager
async def _lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Residência Med API", lifespan=_lifespan)

_origens = [o.strip() for o in os.environ.get("CORS_ORIGENS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens,
    allow_credentials=True,  # necessário para o cookie httpOnly de sessão
    allow_methods=["*"],
    allow_headers=["*"],
)


for router in (auth.router, me.router, painel.router, praticar.router, questoes.router,
               revisao.router, areas.router, materiais.router, simulados.router,
               sincronizacao.router, busca.router):
    app.include_router(router)


@app.get("/health")
def health():
    return {"ok": True}
