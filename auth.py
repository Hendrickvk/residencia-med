"""
Autenticação simples por e-mail/senha (bcrypt) para a plataforma
multiusuário. Não usa cookies/tokens — o login vive em
st.session_state, então não sobrevive a um refresh completo do
navegador (limitação conhecida e aceita nesta fase; o progresso em si
fica seguro no Postgres independente disso).
"""

import streamlit as st
import bcrypt

import db
import ui


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))


def render_login_signup():
    _, col_c, _ = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:3rem; margin-bottom:1.5rem;">
                <div style="display:inline-flex; align-items:center; justify-content:center;
                            width:3.5rem; height:3.5rem; border-radius:10px;
                            background: var(--action-soft); color: var(--action);">
                    {ui.icon_svg("stethoscope", size=28)}
                </div>
                <div style="font-size:24px; font-weight:600; margin-top:0.6rem; color:var(--ink-700);">
                    Residência Med
                </div>
                <div style="color:var(--ink-500); font-size:0.9rem; margin-top:0.3rem;">
                    Sua plataforma de estudos para residência médica
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])

            with aba_entrar:
                email = st.text_input("E-mail", key="login_email")
                senha = st.text_input("Senha", type="password", key="login_senha")
                if st.button("Entrar", key="btn_entrar", type="primary", use_container_width=True):
                    usuario = db.obter_usuario_por_email(email) if email.strip() else None
                    if usuario and verificar_senha(senha, usuario["senha_hash"]):
                        st.session_state.usuario_id = usuario["id"]
                        st.session_state.usuario_email = usuario["email"]
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")

            with aba_criar:
                novo_email = st.text_input("E-mail", key="signup_email")
                nova_senha = st.text_input("Senha", type="password", key="signup_senha")
                confirmar = st.text_input("Confirmar senha", type="password", key="signup_confirma")
                if st.button("Criar conta", key="btn_criar_conta", type="primary", use_container_width=True):
                    if not novo_email.strip() or "@" not in novo_email:
                        st.error("Informe um e-mail válido.")
                    elif len(nova_senha) < 6:
                        st.error("A senha deve ter ao menos 6 caracteres.")
                    elif nova_senha != confirmar:
                        st.error("As senhas não coincidem.")
                    else:
                        usuario_id = db.criar_usuario(novo_email, hash_senha(nova_senha))
                        if usuario_id is None:
                            st.error("Já existe uma conta com esse e-mail.")
                        else:
                            st.session_state.usuario_id = usuario_id
                            st.session_state.usuario_email = novo_email.strip().lower()
                            st.success("Conta criada com sucesso!")
                            st.rerun()
