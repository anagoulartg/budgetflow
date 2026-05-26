import streamlit as st

from database.db import init_db
from services.aprovacoes import listar_historico, listar_mensagens_gestor
from services.auth import exigir_login
from services.ui import configurar_pagina


configurar_pagina("Historico e Mensagens")
init_db()
usuario = exigir_login(["Gestor", "Controladoria", "Diretoria", "Conselho", "Admin"])

st.title("Historico e Mensagens")
st.caption("Trilha de auditoria das decisoes e mensagens enviadas aos gestores.")

tab_historico, tab_mensagens = st.tabs(["Historico geral", "Mensagens de ajuste"])

with tab_historico:
    historico = listar_historico()
    if historico.empty:
        st.info("Nenhum evento registrado ainda.")
    else:
        st.dataframe(historico, use_container_width=True, hide_index=True)

with tab_mensagens:
    gestor = usuario["nome"] if usuario["perfil"] == "Gestor" else None
    mensagens = listar_mensagens_gestor(gestor)
    if mensagens.empty:
        st.info("Nenhuma mensagem de ajuste encontrada.")
    else:
        st.dataframe(mensagens, use_container_width=True, hide_index=True)
