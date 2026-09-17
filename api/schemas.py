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
    meta_revisao_diaria: int


class TemaIn(BaseModel):
    tema: str = Field(pattern="^(light|dark)$")


class MetaRevisaoIn(BaseModel):
    # Casos por dia na tela de Revisão (repeticao_espacada.plano_revisao).
    meta: int = Field(ge=5, le=200)


# --- Praticar / respostas ---------------------------------------------------

class RespostaIn(BaseModel):
    questao_id: int
    alternativa: str
    confianca: Optional[str] = Field(default=None, pattern="^(seguro|chute)$")
    tempo_ms: Optional[int] = None


class MarcarRevisaoIn(BaseModel):
    qualidade: int = Field(ge=0, le=5)
    # A Revisão responde de novo: com a alternativa, o gabarito decide se foi
    # erro (repeticao_espacada.avaliar_revisao), não a nota enviada.
    alternativa: Optional[str] = Field(default=None, pattern="^[A-E]$")
    tempo_ms: Optional[int] = Field(default=None, ge=0)


# --- Simulados ----------------------------------------------------------

class SimuladoIn(BaseModel):
    area_id: Optional[int] = None
    banca: Optional[str] = None
    num_questoes: int = Field(ge=1, le=200)
    tempo_limite_min: int = Field(ge=1, le=600)


class SimuladoOficialIn(BaseModel):
    banca: str
    edicao: str


class RespostaSimuladoIn(BaseModel):
    questao_id: int
    alternativa: str


class TempoSimuladoIn(BaseModel):
    questao_id: int
    # Uma passagem pela questão: no máximo o simulado mais longo (600 min).
    tempo_ms: int = Field(ge=0, le=600 * 60_000)


# --- Relato de erro em questão ----------------------------------------------

class RelatoIn(BaseModel):
    # `parte` é validado contra db.PARTES_RELATO no router, para a lista viver
    # num lugar só (db.py) e não ser duplicada aqui como um pattern.
    parte: str
    comentario: Optional[str] = Field(default=None, max_length=1000)
