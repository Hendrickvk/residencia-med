from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --- Auth / usuário -----------------------------------------------------

class CredenciaisIn(BaseModel):
    # `EmailStr` (email-validator) rejeita domínios reservados/especiais
    # (.local, .test, example.com...) por padrão — validação exigente
    # demais para um cadastro real e que barraria até os e-mails de teste.
    # Mesmo critério que `auth.py::render_login_signup` já usa hoje.
    email: str = Field(min_length=3)
    senha: str = Field(min_length=6)

    @field_validator("email")
    @classmethod
    def _validar_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Informe um e-mail válido.")
        return v.strip().lower()


class MeOut(BaseModel):
    id: int
    email: str
    is_admin: bool
    tema: str
    prova_alvo: Optional[str] = None
    ofensiva_dias: int
    respondeu_hoje: bool
    respondidas_hoje: int
    total_questoes: int
    total_materiais: int


class TemaIn(BaseModel):
    tema: str = Field(pattern="^(light|dark)$")


class ProvaAlvoIn(BaseModel):
    data: Optional[date] = None


# --- Áreas / subtópicos ---------------------------------------------------

class AreaIn(BaseModel):
    nome: str = Field(min_length=1)


class SubtopicoIn(BaseModel):
    nome: str = Field(min_length=1)


# --- Questões -------------------------------------------------------------

class QuestaoIn(BaseModel):
    area_id: int
    subtopico_id: Optional[int] = None
    enunciado: str = Field(min_length=1)
    alternativas: dict[str, str]
    resposta_correta: str
    explicacao: str = ""
    banca: str = ""
    ano: Optional[int] = None


# --- Praticar / respostas ---------------------------------------------------

class FiltrosSessaoIn(BaseModel):
    area_id: Optional[int] = None
    subtopico_id: Optional[int] = None
    banca: Optional[str] = None
    ano: Optional[int] = None
    apenas_erros: bool = False
    excluir_respondidas: bool = False
    quantidade: int = Field(default=20, ge=1, le=200)


class RespostaIn(BaseModel):
    questao_id: int
    alternativa: str
    confianca: Optional[str] = Field(default=None, pattern="^(seguro|chute)$")
    tempo_ms: Optional[int] = None


class MarcarRevisaoIn(BaseModel):
    qualidade: int = Field(ge=0, le=5)


# --- Materiais --------------------------------------------------------------

class MaterialIn(BaseModel):
    area_id: int
    subtopico_id: Optional[int] = None
    tipo: str = "Outro"
    titulo: str = Field(min_length=1)
    link: str = Field(min_length=1)


class SincronizacaoIn(BaseModel):
    link_raiz: str = Field(min_length=1)


# --- Simulados ----------------------------------------------------------

class SimuladoIn(BaseModel):
    area_id: Optional[int] = None
    banca: Optional[str] = None
    num_questoes: int = Field(ge=1, le=200)
    tempo_limite_min: int = Field(ge=1, le=600)


class RespostaSimuladoIn(BaseModel):
    questao_id: int
    alternativa: str
