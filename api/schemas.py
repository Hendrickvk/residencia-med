from typing import Optional

from pydantic import BaseModel, Field, field_validator

import db


# --- Auth / usuário -----------------------------------------------------

class CredenciaisIn(BaseModel):
    # `EmailStr` (email-validator) rejeita domínios reservados/especiais
    # (.local, .test, example.com...) por padrão — validação exigente
    # demais para um cadastro real e que barraria até os e-mails de teste.
    # Mesmo critério que `auth.py::render_login_signup` já usa hoje.
    email: str = Field(min_length=3)
    # 8 caracteres, não 6: com o login agora limitado a 10 tentativas por
    # janela, o gargalho volta a ser o tamanho da senha.
    senha: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def _validar_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Informe um e-mail válido.")
        return v.strip().lower()


class EsqueciSenhaIn(BaseModel):
    """Só o e-mail. A resposta do endpoint é a mesma exista ou não a conta,
    então este schema não valida nada além do formato."""

    email: str = Field(min_length=3)

    @field_validator("email")
    @classmethod
    def _validar_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Informe um e-mail válido.")
        return v.strip().lower()


class ConfirmarEmailIn(BaseModel):
    token: str


class RedefinirSenhaIn(BaseModel):
    # Mesmo mínimo do cadastro (CredenciaisIn): trocar a senha não pode ser
    # uma porta para uma senha mais fraca do que a que o signup aceita.
    token: str = Field(min_length=20)
    senha: str = Field(min_length=6)


class MeOut(BaseModel):
    id: int
    email: str
    is_admin: bool
    # NULL no banco vira False aqui: a tela só precisa saber se libera ou não.
    email_confirmado: bool
    tema: str
    prova_alvo: Optional[str] = None
    ofensiva_dias: int
    respondeu_hoje: bool
    respondidas_hoje: int
    total_questoes: int
    meta_revisao_diaria: int
    novidades_vistas: Optional[str] = None
    nome: Optional[str] = None
    cor_perfil: str
    # Muda quando a foto muda: é o que entra na URL da imagem e faz a nova
    # aparecer na hora, sem esperar o cache vencer. NULL = sem foto.
    foto_versao: Optional[str] = None
    # Cartões vencidos somando todos os baralhos: o número da aba, como o da
    # Revisão. Sem ele, a aluna só descobre que tem cartões esperando se
    # lembrar de entrar lá.
    cartoes_hoje: int = 0
    # Roteiro da brincadeira de boas-vindas: só a conta que tem um recebe, as
    # outras recebem None. Vem no /me, que a tela já espera antes de aparecer;
    # numa rota à parte, seria uma ida a mais ao servidor antes de qualquer
    # tela abrir, para todo mundo.
    brincadeira: Optional[dict] = None


class TemaIn(BaseModel):
    tema: str = Field(pattern="^(light|dark)$")


class PastaIn(BaseModel):
    nome: str = Field(default="", max_length=db.LIMITE_NOME_PASTA)
    # Validada contra `db.CORES_PASTA` lá dentro: valor de fora da lista vira
    # CSS na tela, então cai no padrão em vez de passar.
    cor: str = Field(default=db.COR_PASTA_PADRAO, max_length=20)


class BaralhoIn(BaseModel):
    nome: str = Field(default="", max_length=db.LIMITE_NOME_PASTA)
    # Na criação é a pasta onde nasce; no PATCH, para onde vai (mover).
    pasta_id: Optional[int] = None


class CartaoIn(BaseModel):
    frente: str = Field(default="", max_length=db.LIMITE_TEXTO_CARTAO)
    verso: str = Field(default="", max_length=db.LIMITE_TEXTO_CARTAO)
    baralho_id: Optional[int] = None
    # De qual caso o cartão nasceu, quando veio da discussão de um.
    questao_id: Optional[int] = None


class NotaCartaoIn(BaseModel):
    # 1 = errei; 3, 4, 5 = com esforço, lembrei, fácil. A mesma escala da
    # Revisão de casos (repeticao_espacada.NOTAS_ACERTO).
    qualidade: int = Field(ge=0, le=5)


class ProvaAlvoIn(BaseModel):
    # `None` limpa a data e desliga a contagem regressiva.
    data: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class FotoIn(BaseModel):
    # A imagem chega em base64 dentro do JSON, e não como multipart: evita a
    # dependência `python-multipart` e casa com o `canvas.toDataURL()` que o
    # navegador já produz ao redimensionar. O limite aqui é do texto em base64
    # (~4/3 do binário); o limite que vale é o dos bytes decodificados, no
    # endpoint.
    dados: str = Field(max_length=4 * db.FOTO_MAX_BYTES)
    mime: str = Field(max_length=20)


class PerfilIn(BaseModel):
    # Nome vazio é permitido: é como a pessoa volta a não ter nome.
    nome: str = Field(default="", max_length=db.LIMITE_NOME)
    # A cor é validada contra a lista do `db` (e não um hex livre): valor de
    # fora da lista viraria CSS arbitrário vindo do cliente.
    cor: str = Field(default=db.COR_PERFIL_PADRAO, max_length=20)


class NovidadesIn(BaseModel):
    # O id da entrada, não um booleano: "já viu" só faz sentido em relação a
    # uma versão, senão a próxima novidade nunca apareceria.
    visto: str = Field(max_length=40)


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
