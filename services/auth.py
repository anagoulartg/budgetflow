import streamlit as st
from sqlalchemy import select

from database.db import get_session
from database.models import Usuario


PERFIS = ["Gestor", "Controladoria", "Diretoria", "Conselho", "Admin"]


def autenticar(nome: str, senha: str) -> dict | None:
    with get_session() as session:
        usuario = session.execute(select(Usuario).where(Usuario.nome == nome.strip())).scalar_one_or_none()
        if usuario and usuario.senha == senha:
            return {"id": usuario.id, "nome": usuario.nome, "perfil": usuario.perfil, "area_responsavel": usuario.area_responsavel}
    return None


def usuario_atual() -> dict | None:
    return st.session_state.get("usuario")


def exigir_login(perfis: list[str] | None = None) -> dict:
    usuario = usuario_atual()
    if not usuario:
        st.warning("Faca login para acessar o BudgetFlow.")
        st.stop()
    if perfis and usuario["perfil"] not in perfis and usuario["perfil"] != "Admin":
        st.error("Seu perfil nao tem acesso a esta area.")
        st.stop()
    return usuario


def bloco_login(pagina_atual: str = "Dashboard Executivo") -> None:
    from database.db import init_db

    init_db()
    _sidebar_menu(pagina_atual)
    if usuario_atual():
        usuario = usuario_atual()
        with st.sidebar:
            st.caption(f"Logado como {usuario['nome']}")
            st.caption(f"Perfil: {usuario['perfil']}")
            if st.button("Sair"):
                st.session_state.pop("usuario", None)
                st.rerun()
        return

    st.sidebar.header("Login")
    with st.sidebar.form("login_budgetflow"):
        nome = st.text_input("Usuario", value="admin.demo")
        senha = st.text_input("Senha", value="123456", type="password")
        entrar = st.form_submit_button("Entrar", type="primary")

    if entrar:
        usuario = autenticar(nome, senha)
        if usuario:
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.sidebar.error("Usuario ou senha invalidos.")


def usuarios_demo() -> list[tuple[str, str, str]]:
    return [
        ("gestor.demo", "123456", "Gestor"),
        ("controladoria.demo", "123456", "Controladoria"),
        ("diretoria.demo", "123456", "Diretoria Comercial"),
        ("diretoria.adm", "123456", "Diretoria Administrativo"),
        ("diretoria.industrial", "123456", "Diretoria Industrial"),
        ("conselho.demo", "123456", "Conselho"),
        ("admin.demo", "123456", "Admin"),
    ]


def _sidebar_menu(pagina_atual: str) -> None:
    st.logo("assets/logo.svg")
    with st.sidebar:
        st.page_link("app.py", label="Inicio")
        st.page_link("pages/1_Gestor.py", label="1. Gestor")
        st.page_link("pages/2_Diretoria.py", label="2. Diretoria")
        st.page_link("pages/3_Conselho.py", label="3. Conselho")
        st.page_link("pages/4_Metas.py", label="4. Metas")
        st.page_link("pages/5_Controladoria.py", label="5. Controladoria")
        st.page_link("pages/6_Exportacao_ERP.py", label="6. Exportacao ERP")
        st.page_link("pages/7_Historico_e_Mensagens.py", label="Historico")
