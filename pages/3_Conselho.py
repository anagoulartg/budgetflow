import plotly.express as px
import streamlit as st

from database.db import init_db
from services.aprovacoes import STATUS_CONSELHO, listar_historico, registrar_decisao
from services.auth import exigir_login
from services.metas import metas_por_area
from services.orcamentos import filtrar_orcamentos, listar_orcamentos
from services.ui import TIPO_COLORS, aplicar_tema_grafico, configurar_pagina, kpi_card, moeda


configurar_pagina("Conselho")
init_db()
usuario = exigir_login(["Conselho"])

st.title("3. Conselho - Aprovacao Final")
st.caption("Deliberacao final em lote, com visao consolidada por area e tipo.")

df_base = listar_orcamentos("Aprovado Diretoria")

with st.sidebar:
    st.divider()
    st.header("Filtros")
    if df_base.empty:
        areas = tipos = centros = []
    else:
        busca = st.text_input("Buscar")
        areas = st.multiselect("Area", sorted(df_base["area"].unique()))
        centros = st.multiselect("Centro de custo", sorted(df_base["centro_custo"].unique()))
        tipos = st.multiselect("Tipo", sorted(df_base["tipo"].unique()))

df = filtrar_orcamentos(df_base, areas=areas, centros=centros, tipos=tipos)
if "busca" in locals() and busca and not df.empty:
    texto = busca.lower()
    df = df[
        df["descricao"].str.lower().str.contains(texto, na=False)
        | df["area"].str.lower().str.contains(texto, na=False)
        | df["centro_custo"].str.lower().str.contains(texto, na=False)
    ]

if df.empty:
    st.info("Nao ha orcamentos aprovados pela diretoria aguardando conselho.")
else:
    df["valor_diretoria"] = df["valor_aprovado"].fillna(df["valor_solicitado"])
    gasto = df[df["tipo"].isin(["Despesa", "Investimento"])]["valor_diretoria"].sum()
    receita = df[df["tipo"] == "Receita"]["valor_diretoria"].sum()
    saldo = receita - gasto

    ano_ref = int(df["ano"].max())
    metas = metas_por_area(ano_ref)
    meta_gastos = metas[metas["tipo"].isin(["Despesa", "Investimento"])]["valor_meta"].sum() if not metas.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Receita aprovada dir.", moeda(receita), "#2563eb", "RC")
    with col2:
        kpi_card("Gasto aprovado dir.", moeda(gasto), "#f59e0b", "GA")
    with col3:
        kpi_card("Saldo projetado", moeda(saldo), "#22a06b" if saldo >= 0 else "#ef4444", "SP")
    with col4:
        kpi_card("Meta gastos", moeda(meta_gastos), "#14b8a6", "MG")

    left, right = st.columns(2)
    with left:
        area = df.groupby("area", as_index=False)["valor_diretoria"].sum().sort_values("valor_diretoria", ascending=False)
        st.plotly_chart(
            aplicar_tema_grafico(
                px.bar(area, x="area", y="valor_diretoria", title="Aprovado pela diretoria por area", color_discrete_sequence=["#2563EB"]),
                320,
            ),
            use_container_width=True,
        )
    with right:
        tipo = df.groupby("tipo", as_index=False)["valor_diretoria"].sum()
        st.plotly_chart(
            aplicar_tema_grafico(
                px.pie(tipo, names="tipo", values="valor_diretoria", title="Composicao do orcamento final", hole=0.45, color="tipo", color_discrete_map=TIPO_COLORS),
                320,
            ),
            use_container_width=True,
        )

    st.subheader("Itens para deliberacao")
    st.caption("Selecione os itens, escolha uma acao unica e confirme. O valor final pode ser ajustado direto na tabela.")

    selecionar_tudo = st.checkbox("Selecionar todos os itens filtrados")
    lote = df[
        ["id", "area", "centro_custo", "descricao", "mes", "tipo", "prioridade", "valor_solicitado", "valor_diretoria", "justificativa"]
    ].copy()
    lote["valor_final"] = lote["valor_diretoria"]
    lote["selecionar"] = bool(selecionar_tudo)
    lote["comentario"] = ""
    lote = lote[
        [
            "selecionar",
            "id",
            "area",
            "centro_custo",
            "descricao",
            "mes",
            "tipo",
            "prioridade",
            "valor_diretoria",
            "valor_final",
            "comentario",
            "justificativa",
        ]
    ]

    editado = st.data_editor(
        lote,
        use_container_width=True,
        hide_index=True,
        height=640,
        column_config={
            "selecionar": st.column_config.CheckboxColumn("Selecionar"),
            "valor_diretoria": st.column_config.NumberColumn("Valor diretoria", format="R$ %.2f", disabled=True),
            "valor_final": st.column_config.NumberColumn("Valor final", format="R$ %.2f"),
            "comentario": st.column_config.TextColumn("Comentario"),
            "justificativa": st.column_config.TextColumn("Justificativa", disabled=True),
        },
        disabled=["id", "area", "centro_custo", "descricao", "mes", "tipo", "prioridade", "valor_diretoria", "justificativa"],
        key=f"conselho_lote_{selecionar_tudo}",
    )

    selecionadas = editado[editado["selecionar"]]
    col_a, col_b, col_c = st.columns([1, 1, 1.5])
    col_a.metric("Itens selecionados", len(selecionadas))
    col_b.metric("Valor final selecionado", moeda(selecionadas["valor_final"].sum() if not selecionadas.empty else 0))
    acao = col_c.selectbox("Acao para os selecionados", ["Aprovar final", "Reprovar final"])
    comentario_padrao = st.text_input("Comentario padrao", value="Deliberacao final registrada pelo Conselho.")

    if st.button("Aplicar deliberacao aos selecionados", type="primary", disabled=selecionadas.empty):
        erros = []
        processados = 0
        novo_status = STATUS_CONSELHO[acao]
        for _, row in selecionadas.iterrows():
            comentario = str(row["comentario"]).strip() or comentario_padrao
            try:
                registrar_decisao(
                    orcamento_id=int(row["id"]),
                    usuario_decisor=usuario["nome"],
                    perfil_decisor="Conselho",
                    novo_status=novo_status,
                    novo_valor=float(row["valor_final"]),
                    comentario=comentario,
                )
                processados += 1
            except Exception as exc:  # noqa: BLE001
                erros.append(f"Item {row['id']}: {exc}")
        if processados:
            st.success(f"{processados} deliberacoes registradas.")
        if erros:
            st.error("Algumas deliberacoes nao foram registradas.")
            st.write(erros)
        if processados and not erros:
            st.rerun()

st.divider()
st.subheader("Historico de aprovacoes")
historico = listar_historico()
if historico.empty:
    st.info("Nenhuma decisao registrada ainda.")
else:
    st.dataframe(historico.head(80), use_container_width=True, hide_index=True)
