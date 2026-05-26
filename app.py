import plotly.express as px
import streamlit as st

from database.db import init_db
from services.aprovacoes import analisar_cenarios, resumo_executivo
from services.auth import exigir_login, usuarios_demo
from services.metas import meta_total, metas_por_area
from services.orcamentos import filtrar_orcamentos, listar_orcamentos, popular_dados_exemplo
from services.ui import STATUS_COLORS, TIPO_COLORS, aplicar_tema_grafico, configurar_pagina, kpi_card, moeda, percentual


configurar_pagina("Dashboard Executivo")
init_db()

st.title("BudgetFlow")
st.caption("Central de formacao orcamentaria | Dashboard executivo")

usuario = st.session_state.get("usuario")
if not usuario:
    st.markdown("### Acesse para analisar o ciclo orcamentario")
    st.write("Usuarios de teste:")
    st.dataframe(
        [{"usuario": nome, "senha": senha, "perfil": perfil} for nome, senha, perfil in usuarios_demo()],
        use_container_width=True,
        hide_index=True,
    )
    st.stop()

df_base = listar_orcamentos()
if usuario["perfil"] == "Gestor" and not df_base.empty:
    df_base = df_base[df_base["gestor"] == usuario["nome"]]
elif usuario["perfil"] == "Diretoria" and usuario.get("area_responsavel") and not df_base.empty:
    df_base = df_base[df_base["area"] == usuario["area_responsavel"]]
elif usuario["perfil"] == "Conselho" and not df_base.empty:
    df_base = df_base[df_base["status"].isin(["Aprovado Diretoria", "Aprovado Final", "Reprovado Final"])]

with st.sidebar:
    st.divider()
    st.header("Filtros executivos")
    if df_base.empty:
        anos = areas = centros = tipos = statuses = []
    else:
        anos = st.multiselect("Ano", sorted(df_base["ano"].unique()), default=sorted(df_base["ano"].unique()))
        areas = st.multiselect("Area", sorted(df_base["area"].unique()))
        centros = st.multiselect("Centro de custo", sorted(df_base["centro_custo"].unique()))
        tipos = st.multiselect("Tipo", sorted(df_base["tipo"].unique()))
        statuses = st.multiselect("Status", sorted(df_base["status"].unique()))

    meta_reducao = st.slider("Meta de reducao para despesas/investimentos", 0, 40, 8, 1)
    st.divider()
    if st.button("Popular dados de exemplo"):
        qtd = popular_dados_exemplo()
        st.success(f"{qtd} itens criados.")
        st.rerun()

if df_base.empty:
    st.info("Cadastre orcamentos ou popule dados de exemplo para iniciar a analise.")
    st.stop()

df = filtrar_orcamentos(df_base, anos=anos, areas=areas, centros=centros, tipos=tipos, statuses=statuses)
if df.empty:
    st.warning("Nenhum item encontrado para os filtros selecionados.")
    st.stop()

df_operacional = df[df["tipo"].isin(["Despesa", "Investimento"])].copy()
if df_operacional.empty:
    st.warning("Nao ha despesas ou investimentos para analisar nos filtros atuais.")
    st.stop()

df["valor_decidido"] = df["valor_final"].fillna(df["valor_aprovado"]).fillna(0)
df_operacional["valor_decidido"] = df_operacional["valor_final"].fillna(df_operacional["valor_aprovado"]).fillna(0)
df["gap_decisao"] = df["valor_solicitado"] - df["valor_decidido"]
resumo = resumo_executivo(df_operacional)
gasto = df_operacional["valor_solicitado"].sum()
aprovado_decidido = df_operacional["valor_decidido"].sum()
ano_ref = int(df_operacional["ano"].max())
metas = metas_por_area(ano_ref)
meta_gastos_cadastrada = meta_total(metas[metas["tipo"].isin(["Despesa", "Investimento"])]) if not metas.empty else 0
gap_meta = gasto - meta_gastos_cadastrada if meta_gastos_cadastrada else 0
meta_simulada = gasto * (1 - meta_reducao / 100)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Gasto solicitado", moeda(gasto), "#f59e0b", "GS")
with col2:
    kpi_card("Meta cadastrada", moeda(meta_gastos_cadastrada) if meta_gastos_cadastrada else "Sem meta", "#14b8a6", "MT")
with col3:
    kpi_card("Gap vs meta", moeda(gap_meta) if meta_gastos_cadastrada else "-", "#ef4444" if gap_meta > 0 else "#22a06b", "GP")
with col4:
    kpi_card("Decidido", moeda(aprovado_decidido), "#22a06b", "OK")

pendentes = df_operacional[df_operacional["status"].isin(["Pendente", "Ajuste Solicitado"])].shape[0]
aprovados = df_operacional[df_operacional["status"].str.contains("Aprovado", na=False)].shape[0]
reprovados = df_operacional[df_operacional["status"].str.contains("Reprovado", na=False)].shape[0]

col6, col7, col8, col9 = st.columns(4)
with col6:
    kpi_card("Itens", str(len(df_operacional)), "#2563eb", "IT")
with col7:
    kpi_card("Pendentes/ajuste", str(pendentes), "#f59e0b", "PD")
with col8:
    kpi_card("Aprovados", str(aprovados), "#22a06b", "OK")
with col9:
    kpi_card("Reprovados", str(reprovados), "#ef4444", "RP")

st.divider()

left, right = st.columns([1.15, 0.85])
with left:
    area = df_operacional.groupby("area", as_index=False).agg(
        solicitado=("valor_solicitado", "sum"),
        decidido=("valor_decidido", "sum"),
    )
    area["gap"] = area["solicitado"] - area["decidido"]
    fig_area = px.bar(
        area.sort_values("solicitado", ascending=False),
        x="area",
        y=["solicitado", "decidido"],
        barmode="group",
        title="Solicitado x decidido por area",
        color_discrete_sequence=["#1E4E8C", "#16877A"],
    )
    st.plotly_chart(aplicar_tema_grafico(fig_area, 390), use_container_width=True)

with right:
    status = df_operacional.groupby("status", as_index=False)["id"].count().rename(columns={"id": "quantidade"})
    st.plotly_chart(
        aplicar_tema_grafico(
            px.pie(status, names="status", values="quantidade", title="Fila de decisao", hole=0.48, color="status", color_discrete_map=STATUS_COLORS),
            390,
        ),
        use_container_width=True,
    )

left, right = st.columns(2)
with left:
    tipo = df_operacional.groupby("tipo", as_index=False)["valor_solicitado"].sum()
    st.plotly_chart(
        aplicar_tema_grafico(
            px.bar(tipo, x="tipo", y="valor_solicitado", title="Mix Receita x Despesa x Investimento", color="tipo", color_discrete_map=TIPO_COLORS),
            350,
        ),
        use_container_width=True,
    )

with right:
    mes = df_operacional.groupby("mes", as_index=False)["valor_solicitado"].sum().sort_values("mes")
    fig_mes = px.line(mes, x="mes", y="valor_solicitado", markers=True, title="Pressao de caixa por mes")
    fig_mes.update_traces(line_color="#1E4E8C", marker_color="#D98C24", line_width=3)
    st.plotly_chart(aplicar_tema_grafico(fig_mes, 350), use_container_width=True)

st.subheader("Cenario de reducao")
cenario = analisar_cenarios(df_operacional, meta_reducao)
if cenario.empty:
    st.info("Nao ha despesas ou investimentos para simular reducao.")
else:
    c1, c2 = st.columns([0.9, 1.1])
    with c1:
        st.dataframe(
            cenario.assign(
                solicitado=cenario["solicitado"].map(moeda),
                meta=cenario["meta"].map(moeda),
                corte_sugerido=cenario["corte_sugerido"].map(moeda),
            ),
            use_container_width=True,
            hide_index=True,
        )
    with c2:
        st.plotly_chart(
            aplicar_tema_grafico(
                px.bar(cenario, x="area", y="corte_sugerido", title="Onde a meta de corte teria maior impacto", color_discrete_sequence=["#C75146"]),
                360,
            ),
            use_container_width=True,
        )

st.subheader("Maiores alavancas de decisao")
oportunidades = df_operacional.copy()
if not oportunidades.empty:
    oportunidades["corte_sugerido"] = oportunidades["valor_solicitado"] * (meta_reducao / 100)
    cols = ["id", "area", "centro_custo", "descricao", "tipo", "prioridade", "status", "valor_solicitado", "corte_sugerido"]
    st.dataframe(
        oportunidades.nlargest(12, "valor_solicitado")[cols],
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Base analitica filtrada"):
    st.dataframe(df, use_container_width=True, hide_index=True)
