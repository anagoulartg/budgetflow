import plotly.express as px
import streamlit as st

from database.db import init_db
from services.aprovacoes import analisar_cenarios, listar_historico, resumo_executivo
from services.auth import exigir_login
from services.metas import meta_total, metas_por_area, salvar_metas, template_metas
from services.orcamentos import filtrar_orcamentos, listar_orcamentos
from services.ui import CHART_COLORS, aplicar_tema_grafico, configurar_pagina, kpi_card, moeda


configurar_pagina("Controladoria")
init_db()
usuario = exigir_login(["Controladoria"])

st.title("4. Controladoria")
st.caption("Metas, consistencia e consolidacao financeira do ciclo.")

df_base = listar_orcamentos()
ano_default = int(df_base["ano"].max()) if not df_base.empty else 2026

tab_metas, tab_consolidado, tab_consistencia = st.tabs(["Metas por area", "Consolidado", "Consistencia"])

with tab_metas:
    st.subheader("Cadastro de metas")
    st.caption("Defina metas por area e tipo. Diretoria usa essas metas para sugerir cortes e ajustes.")
    ano_meta = st.number_input("Ano da meta", min_value=2024, max_value=2035, value=ano_default)
    metas_edit = st.data_editor(
        template_metas(int(ano_meta)),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        height=360,
        column_config={
            "area": st.column_config.SelectboxColumn("Area", options=["Administrativo", "Comercial", "Industrial", "RH", "TI", "Financeiro", "Operacoes", "Marketing", "Produto"]),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["Despesa", "Investimento"]),
            "valor_meta": st.column_config.NumberColumn("Meta anual", format="R$ %.2f", min_value=0.0),
            "observacao": st.column_config.TextColumn("Observacao"),
        },
        key="metas_editor",
    )
    if st.button("Salvar metas", type="primary"):
        try:
            total = salvar_metas(metas_edit, int(ano_meta))
            st.success(f"{total} metas salvas para {int(ano_meta)}.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

if df_base.empty:
    with tab_consolidado:
        st.info("Nenhum orcamento cadastrado ainda.")
    st.stop()

with st.sidebar:
    st.divider()
    st.header("Filtros")
    anos = st.multiselect("Ano", sorted(df_base["ano"].unique()), default=sorted(df_base["ano"].unique()))
    areas = st.multiselect("Area", sorted(df_base["area"].unique()))
    centros = st.multiselect("Centro de custo", sorted(df_base["centro_custo"].unique()))
    tipos = st.multiselect("Tipo", sorted(df_base["tipo"].unique()))
    statuses = st.multiselect("Status", sorted(df_base["status"].unique()))

df = filtrar_orcamentos(df_base, anos=anos, areas=areas, centros=centros, tipos=tipos, statuses=statuses)

with tab_consolidado:
    if df.empty:
        st.warning("Nenhum item encontrado para os filtros.")
    else:
        df["valor_decidido"] = df["valor_final"].fillna(df["valor_aprovado"]).fillna(0)
        resumo = resumo_executivo(df)
        ano_ref = int(df["ano"].max())
        metas = metas_por_area(ano_ref)
        meta_gastos = meta_total(metas[metas["tipo"].isin(["Despesa", "Investimento"])]) if not metas.empty else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            kpi_card("Total solicitado", moeda(resumo["solicitado"]), "#2563eb", "R$")
        with col2:
            kpi_card("Valor decidido", moeda(resumo["aprovado"]), "#22a06b", "OK")
        with col3:
            kpi_card("Meta de gastos", moeda(meta_gastos), "#14b8a6", "MT")
        with col4:
            kpi_card("Itens com ajuste", str(df[df["status"] == "Ajuste Solicitado"].shape[0]), "#f59e0b", "AJ")

        area = df.groupby("area", as_index=False).agg(
            solicitado=("valor_solicitado", "sum"),
            decidido=("valor_decidido", "sum"),
            itens=("id", "count"),
        )
        if not metas.empty:
            metas_area = metas.groupby("area", as_index=False)["valor_meta"].sum().rename(columns={"valor_meta": "meta"})
            area = area.merge(metas_area, on="area", how="left").fillna({"meta": 0})
        else:
            area["meta"] = 0
        area["gap_meta"] = area["solicitado"] - area["meta"]

        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                aplicar_tema_grafico(
                    px.bar(area, x="area", y=["solicitado", "meta"], barmode="group", title="Solicitado x meta por area"),
                    340,
                ),
                use_container_width=True,
            )
        with right:
            st.plotly_chart(
                aplicar_tema_grafico(
                    px.scatter(area, x="itens", y="solicitado", size="solicitado", color="area", title="Volume x quantidade de itens", color_discrete_sequence=CHART_COLORS),
                    340,
                ),
                use_container_width=True,
            )

        st.subheader("Resumo por area")
        st.dataframe(area, use_container_width=True, hide_index=True, height=280)

with tab_consistencia:
    if df.empty:
        st.warning("Nenhum item encontrado para os filtros.")
    else:
        st.subheader("Analise de consistencia")
        duplicados = df.duplicated(subset=["ano", "area", "centro_custo", "conta_contabil", "descricao", "mes"], keep=False)
        sem_justificativa = df[df["justificativa"].str.len() < 15]
        outliers = df[df["valor_solicitado"] > df["valor_solicitado"].quantile(0.9)]

        c1, c2, c3 = st.columns(3)
        c1.metric("Possiveis duplicidades", int(duplicados.sum()))
        c2.metric("Justificativas curtas", len(sem_justificativa))
        c3.metric("Itens acima do P90", len(outliers))

        with st.expander("Possiveis duplicidades"):
            st.dataframe(df[duplicados], use_container_width=True, hide_index=True)
        with st.expander("Justificativas curtas"):
            st.dataframe(sem_justificativa, use_container_width=True, hide_index=True)
        with st.expander("Itens de maior materialidade"):
            st.dataframe(outliers.sort_values("valor_solicitado", ascending=False), use_container_width=True, hide_index=True)

        st.subheader("Cenario de eficiencia")
        cenario = analisar_cenarios(df, 10)
        if cenario.empty:
            st.info("Nao ha despesas ou investimentos para simular.")
        else:
            st.dataframe(cenario, use_container_width=True, hide_index=True)

        with st.expander("Historico recente"):
            historico = listar_historico()
            if historico.empty:
                st.info("Nenhum evento registrado.")
            else:
                st.dataframe(historico.head(50), use_container_width=True, hide_index=True)
