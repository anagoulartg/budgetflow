import streamlit as st
from io import BytesIO

from database.db import init_db
from services.auth import exigir_login
from services.exportador_erp import dados_erp, exportar_csv, exportar_excel
from services.orcamentos import listar_orcamentos
from services.ui import configurar_pagina


configurar_pagina("Exportacao ERP")
init_db()
exigir_login(["Controladoria", "Admin"])

st.title("Exportacao ERP")

empresa = st.text_input("Codigo da empresa", value="001", max_chars=10)
df = dados_erp(empresa)

st.subheader("Previa dos dados finais aprovados")
if df.empty:
    st.info("Nao ha orcamentos com status Aprovado Final para exportar.")
    base = listar_orcamentos()
    if not base.empty:
        st.write("Enquanto o ciclo ainda nao foi aprovado no Conselho, baixe a base consolidada de trabalho:")
        csv_base = base.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        excel_buffer = BytesIO()
        base.to_excel(excel_buffer, index=False, engine="openpyxl")
        col1, col2 = st.columns(2)
        col1.download_button("Baixar base consolidada CSV", csv_base, file_name="budgetflow_base_consolidada.csv", mime="text/csv")
        col2.download_button(
            "Baixar base consolidada Excel",
            excel_buffer.getvalue(),
            file_name="budgetflow_base_consolidada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    col1, col2 = st.columns(2)
    col1.download_button("Baixar CSV ERP", csv, file_name="budgetflow_erp.csv", mime="text/csv", type="primary")
    col2.download_button(
        "Baixar Excel ERP",
        excel_buffer.getvalue(),
        file_name="budgetflow_erp.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

    with st.expander("Tambem salvar copia na pasta exports"):
        col3, col4 = st.columns(2)
        if col3.button("Salvar CSV na pasta exports"):
            caminho = exportar_csv(empresa)
            st.success(f"CSV salvo em: {caminho}")
        if col4.button("Salvar Excel na pasta exports"):
            caminho = exportar_excel(empresa)
            st.success(f"Excel salvo em: {caminho}")

st.divider()
st.write("Layout ERP: empresa; ano; centro_custo; conta_contabil; mes; valor_aprovado; historico; tipo")
