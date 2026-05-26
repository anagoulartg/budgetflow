import streamlit as st

from database.db import init_db
from services.auth import exigir_login
from services.metas import salvar_metas, template_metas
from services.ui import configurar_pagina


configurar_pagina("Metas")
init_db()
exigir_login(["Controladoria"])

st.title("4. Metas Orcamentarias")
st.caption("Controladoria define aqui o limite anual por area. Diretoria usa isso para aprovar ou pedir ajustes.")

ano_meta = st.number_input("Ano da meta", min_value=2024, max_value=2035, value=2026)

metas_edit = st.data_editor(
    template_metas(int(ano_meta)),
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    height=520,
    column_config={
        "area": st.column_config.SelectboxColumn("Area", options=["Administrativo", "Comercial", "Industrial"]),
        "tipo": st.column_config.SelectboxColumn("Tipo", options=["Despesa", "Investimento"]),
        "valor_meta": st.column_config.NumberColumn("Meta anual", format="R$ %.2f", min_value=0.0),
        "observacao": st.column_config.TextColumn("Observacao"),
    },
    key="pagina_metas_editor",
)

if st.button("Salvar metas", type="primary"):
    try:
        total = salvar_metas(metas_edit, int(ano_meta))
        st.success(f"{total} metas salvas para {int(ano_meta)}.")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))
