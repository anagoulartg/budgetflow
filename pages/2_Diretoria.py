import plotly.express as px
import streamlit as st

from database.db import init_db
from services.aprovacoes import STATUS_DIRETORIA, listar_historico, registrar_decisao
from services.auth import exigir_login
from services.metas import metas_por_area
from services.orcamentos import filtrar_orcamentos, listar_orcamentos
from services.ui import aplicar_tema_grafico, configurar_pagina, kpi_card, moeda


configurar_pagina("Diretoria")
init_db()
usuario = exigir_login(["Diretoria"])

area_diretor = usuario.get("area_responsavel")
st.title("2. Diretoria - Analise e Aprovacao")
st.caption(f"Fila da area: {area_diretor or 'todas as areas'} | Selecione itens, escolha uma acao e confirme em lote.")

df_base = listar_orcamentos(["Pendente", "Ajuste Solicitado"])
if area_diretor and not df_base.empty:
    df_base = df_base[df_base["area"] == area_diretor]

with st.sidebar:
    st.divider()
    st.header("Filtros")
    if df_base.empty:
        centros = tipos = prioridades = []
        busca = ""
    else:
        busca = st.text_input("Buscar")
        centros = st.multiselect("Centro de custo", sorted(df_base["centro_custo"].unique()))
        tipos = st.multiselect("Tipo", sorted(df_base["tipo"].unique()))
        prioridades = st.multiselect("Prioridade", sorted(df_base["prioridade"].unique()))

df = filtrar_orcamentos(df_base, centros=centros, tipos=tipos)
if prioridades and not df.empty:
    df = df[df["prioridade"].isin(prioridades)]
if busca and not df.empty:
    texto = busca.lower()
    df = df[
        df["descricao"].str.lower().str.contains(texto, na=False)
        | df["centro_custo"].str.lower().str.contains(texto, na=False)
        | df["justificativa"].str.lower().str.contains(texto, na=False)
    ]

if df.empty:
    st.info("Nao ha orcamentos pendentes para esta diretoria.")
else:
    ano_ref = int(df["ano"].max())
    metas = metas_por_area(ano_ref, area_diretor)
    meta_gasto = metas[metas["tipo"].isin(["Despesa", "Investimento"])]["valor_meta"].sum() if not metas.empty else 0
    gasto = df[df["tipo"].isin(["Despesa", "Investimento"])]["valor_solicitado"].sum()
    gap_gasto = gasto - meta_gasto if meta_gasto else 0
    fator_corte = max(gap_gasto / gasto, 0) if gasto else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Gasto solicitado", moeda(gasto), "#f59e0b", "GS")
    with col2:
        kpi_card("Meta gasto", moeda(meta_gasto), "#14b8a6", "MG")
    with col3:
        kpi_card("Gap vs meta", moeda(gap_gasto), "#ef4444" if gap_gasto > 0 else "#22a06b", "GP")
    with col4:
        kpi_card("Ajuste necessario", moeda(max(gap_gasto, 0)), "#ef4444" if gap_gasto > 0 else "#22a06b", "AJ")

    centro = df.groupby("centro_custo", as_index=False)["valor_solicitado"].sum().sort_values("valor_solicitado", ascending=False)
    tipo = df.groupby("tipo", as_index=False)["valor_solicitado"].sum()
    left, right = st.columns([1.1, 0.9])
    with left:
        st.plotly_chart(
            aplicar_tema_grafico(px.bar(centro, x="centro_custo", y="valor_solicitado", title="Pressao por centro de custo", color_discrete_sequence=["#2563EB"]), 300),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            aplicar_tema_grafico(px.pie(tipo, names="tipo", values="valor_solicitado", title="Composicao da fila", hole=0.45), 300),
            use_container_width=True,
        )

    st.subheader("Decisao em lote")
    if fator_corte > 0:
        st.warning(f"A area esta {moeda(gap_gasto)} acima da meta de gastos. O sistema sugeriu corte proporcional nos itens de despesa/investimento.")
    else:
        st.success("A area esta dentro da meta cadastrada ou nao ha meta de gastos definida.")

    selecionar_tudo = st.checkbox("Selecionar todos os itens filtrados")
    lote = df[
        ["id", "area", "centro_custo", "descricao", "mes", "tipo", "prioridade", "valor_solicitado", "status", "justificativa"]
    ].copy()
    lote["selecionar"] = bool(selecionar_tudo)
    lote["valor_decisao"] = lote.apply(
        lambda row: max(row["valor_solicitado"] * (1 - fator_corte), 0) if row["tipo"] in ["Despesa", "Investimento"] else row["valor_solicitado"],
        axis=1,
    )
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
            "valor_solicitado",
            "valor_decisao",
            "status",
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
            "valor_solicitado": st.column_config.NumberColumn("Solicitado", format="R$ %.2f", disabled=True),
            "valor_decisao": st.column_config.NumberColumn("Valor aprovado/sugerido", format="R$ %.2f", min_value=0.0),
            "comentario": st.column_config.TextColumn("Comentario"),
            "justificativa": st.column_config.TextColumn("Justificativa", disabled=True),
        },
        disabled=["id", "area", "centro_custo", "descricao", "mes", "tipo", "prioridade", "valor_solicitado", "status", "justificativa"],
        key=f"diretoria_lote_{area_diretor}_{selecionar_tudo}",
    )

    selecionadas = editado[editado["selecionar"]]
    col_a, col_b, col_c = st.columns([1, 1, 1.5])
    col_a.metric("Itens selecionados", len(selecionadas))
    col_b.metric("Valor aprovado selecionado", moeda(selecionadas["valor_decisao"].sum() if not selecionadas.empty else 0))
    acao = col_c.selectbox("Acao para os selecionados", ["Aprovar", "Solicitar ajuste", "Reprovar"])
    comentario_padrao = st.text_input("Comentario padrao", value="Decisao registrada pela Diretoria.")

    if st.button("Aplicar acao aos selecionados", type="primary", disabled=selecionadas.empty):
        novo_status = STATUS_DIRETORIA[acao]
        erros = []
        processados = 0
        for _, row in selecionadas.iterrows():
            comentario = str(row["comentario"]).strip() or comentario_padrao
            if acao == "Solicitar ajuste" and comentario == "Decisao registrada pela Diretoria.":
                diferenca = row["valor_solicitado"] - row["valor_decisao"]
                comentario = f"Ajustar item para aderir a meta da area. Corte sugerido: {moeda(diferenca)}."
            try:
                registrar_decisao(
                    orcamento_id=int(row["id"]),
                    usuario_decisor=usuario["nome"],
                    perfil_decisor=usuario["perfil"],
                    novo_status=novo_status,
                    novo_valor=float(row["valor_decisao"]),
                    comentario=comentario,
                )
                processados += 1
            except Exception as exc:  # noqa: BLE001
                erros.append(f"Item {row['id']}: {exc}")
        if processados:
            st.success(f"{processados} itens processados.")
        if erros:
            st.error("Alguns itens nao foram processados.")
            st.write(erros)
        if processados and not erros:
            st.rerun()

st.divider()
st.subheader("Historico recente")
historico = listar_historico()
if historico.empty:
    st.info("Nenhuma decisao registrada ainda.")
else:
    st.dataframe(historico.head(60), use_container_width=True, hide_index=True, height=260)
