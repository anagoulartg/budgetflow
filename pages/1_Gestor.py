import pandas as pd
import streamlit as st

from database.db import init_db
from services.aprovacoes import listar_mensagens_gestor
from services.auth import exigir_login
from services.orcamentos import (
    AREAS_ORCAMENTO,
    TIPOS_ORCAMENTO,
    atualizar_orcamento_gestor,
    criar_orcamento,
    criar_orcamentos_recorrentes,
    excluir_orcamento_gestor,
    importar_arquivo,
    listar_orcamentos,
)
from services.ui import configurar_pagina, kpi_card, moeda


configurar_pagina("Gestor")
init_db()
usuario = exigir_login(["Gestor"])

st.title("1. Gestor - Orcamentos da Area")
st.caption("Cadastre, acompanhe o status e corrija rapidamente o que voltar para ajuste.")

df_todos = listar_orcamentos()
gestor_visualizado = usuario["nome"]
if usuario["perfil"] == "Admin":
    gestores_disponiveis = sorted(df_todos["gestor"].dropna().unique()) if not df_todos.empty else ["gestor.demo"]
    if "gestor.demo" not in gestores_disponiveis:
        gestores_disponiveis.insert(0, "gestor.demo")
    gestor_visualizado = st.selectbox("Visualizar como gestor", gestores_disponiveis)
df_meus = df_todos[df_todos["gestor"] == gestor_visualizado] if not df_todos.empty else pd.DataFrame()

tab_painel, tab_novo, tab_ajustes, tab_upload = st.tabs(["Minha fila", "Novo item", "Ajustes", "Upload"])

with tab_painel:
    if df_meus.empty:
        st.info("Voce ainda nao enviou itens de orcamento.")
    else:
        pendentes = df_meus[df_meus["status"] == "Pendente"]
        ajustes = df_meus[df_meus["status"] == "Ajuste Solicitado"]
        aprovados = df_meus[df_meus["status"].str.contains("Aprovado", na=False)]
        reprovados = df_meus[df_meus["status"].str.contains("Reprovado", na=False)]
        if not ajustes.empty:
            st.error(f"Voce tem {len(ajustes)} item(ns) aguardando ajuste. Abra a aba Ajustes para corrigir e reenviar.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            kpi_card("Total enviado", moeda(df_meus["valor_solicitado"].sum()), "#2563eb", "R$")
        with col2:
            kpi_card("Pendentes", str(len(pendentes)), "#f59e0b", "PD")
        with col3:
            kpi_card("Ajustes", str(len(ajustes)), "#ef4444", "AJ")
        with col4:
            kpi_card("Aprovados", str(len(aprovados)), "#22a06b", "OK")

        st.subheader("Acompanhar envios")
        st.dataframe(
            df_meus[["id", "ano", "area", "centro_custo", "descricao", "mes", "tipo", "valor_solicitado", "prioridade", "status", "justificativa"]].sort_values(
                ["status", "area", "mes"]
            ),
            use_container_width=True,
            hide_index=True,
            height=430,
        )

        editaveis = df_meus[df_meus["status"].isin(["Pendente", "Ajuste Solicitado"])]
        if not editaveis.empty:
            st.subheader("Editar item pendente ou com ajuste")
            selecionado = st.selectbox("Item para editar", editaveis["id"].tolist())
            item = editaveis[editaveis["id"] == selecionado].iloc[0]
            if item["status"] == "Ajuste Solicitado":
                mensagens_item = listar_mensagens_gestor(gestor_visualizado)
                if not mensagens_item.empty:
                    mensagens_item = mensagens_item[mensagens_item["orcamento_id"] == selecionado]
                if not mensagens_item.empty:
                    ultima = mensagens_item.iloc[0]
                    st.warning(f"Ajuste solicitado por {ultima['de']}: {ultima['mensagem']}")
            with st.form("editar_item_gestor"):
                c1, c2, c3 = st.columns(3)
                ano_e = c1.number_input("Ano", min_value=2024, max_value=2035, value=int(item["ano"]))
                area_e = c2.selectbox("Area", AREAS_ORCAMENTO, index=AREAS_ORCAMENTO.index(item["area"]) if item["area"] in AREAS_ORCAMENTO else 0)
                centro_e = c3.text_input("Centro de custo", value=item["centro_custo"])

                c4, c5, c6 = st.columns(3)
                conta_e = c4.text_input("Conta contabil", value=item["conta_contabil"])
                mes_e = c5.selectbox("Mes", [str(i).zfill(2) for i in range(1, 13)], index=int(item["mes"]) - 1)
                tipo_e = c6.selectbox("Tipo", TIPOS_ORCAMENTO, index=TIPOS_ORCAMENTO.index(item["tipo"]) if item["tipo"] in TIPOS_ORCAMENTO else 0)

                descricao_e = st.text_input("Descricao", value=item["descricao"])
                valor_e = st.number_input("Valor solicitado", min_value=0.0, value=float(item["valor_solicitado"]), step=100.0, format="%.2f")
                prioridade_e = st.selectbox("Prioridade", ["Baixa", "Media", "Alta"], index=["Baixa", "Media", "Alta"].index(item["prioridade"]))
                justificativa_e = st.text_area("Justificativa", value=item["justificativa"])
                comentario_e = st.text_area("Comentario da alteracao", value="Ajuste reenviado pelo gestor.")
                salvar_e = st.form_submit_button("Salvar alteracao e reenviar", type="primary")

            if salvar_e:
                try:
                    atualizar_orcamento_gestor(
                        int(selecionado),
                        {
                            "ano": ano_e,
                            "gestor": gestor_visualizado,
                            "area": area_e,
                            "centro_custo": centro_e,
                            "conta_contabil": conta_e,
                            "descricao": descricao_e,
                            "mes": mes_e,
                            "tipo": tipo_e,
                            "valor_solicitado": valor_e,
                            "justificativa": justificativa_e,
                            "prioridade": prioridade_e,
                        },
                        comentario_e,
                    )
                    st.success("Item atualizado e enviado para Diretoria.")
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))

            with st.expander("Excluir solicitacao"):
                st.write("Use apenas se o item foi cadastrado errado. Itens ja aprovados ou reprovados nao podem ser excluidos.")
                confirmar = st.checkbox(f"Confirmo excluir o item #{int(selecionado)}")
                if st.button("Excluir item", disabled=not confirmar):
                    try:
                        excluir_orcamento_gestor(int(selecionado), gestor_visualizado)
                        st.success("Solicitacao excluida.")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        st.error(str(exc))

with tab_novo:
    with st.form("form_orcamento", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        ano = col1.number_input("Ano do orcamento", min_value=2024, max_value=2035, value=2026)
        gestor = col2.text_input("Gestor", value=gestor_visualizado, disabled=True)
        area = col3.selectbox("Area", AREAS_ORCAMENTO)

        col4, col5, col6 = st.columns(3)
        centro_custo = col4.text_input("Centro de custo", value={"Administrativo": "ADM", "Comercial": "COM", "Industrial": "IND"}[area])
        conta_contabil = col5.text_input("Conta contabil")
        mes = col6.selectbox("Mes inicial", [str(i).zfill(2) for i in range(1, 13)])

        descricao = st.text_input("Descricao")

        col7, col8, col9 = st.columns(3)
        tipo = col7.selectbox("Tipo", TIPOS_ORCAMENTO)
        valor_solicitado = col8.number_input("Valor mensal solicitado", min_value=0.0, step=100.0, format="%.2f")
        prioridade = col9.selectbox("Prioridade", ["Baixa", "Media", "Alta"])

        justificativa = st.text_area("Justificativa")
        st.divider()
        col_rec1, col_rec2 = st.columns([1.4, 1])
        recorrencia = col_rec1.selectbox("Recorrencia", ["Somente este mes", "Repetir ate mes X", "Repetir todos os meses do ano"])
        mes_final = col_rec2.selectbox("Mes final", [str(i).zfill(2) for i in range(1, 13)], index=11)
        submitted = st.form_submit_button("Enviar para Diretoria", type="primary")

    if submitted:
        dados = {
            "ano": ano,
            "gestor": gestor_visualizado,
            "area": area,
            "centro_custo": centro_custo,
            "conta_contabil": conta_contabil,
            "descricao": descricao,
            "mes": mes,
            "tipo": tipo,
            "valor_solicitado": valor_solicitado,
            "justificativa": justificativa,
            "prioridade": prioridade,
        }
        try:
            if recorrencia == "Somente este mes":
                orcamento = criar_orcamento(dados)
                st.success(f"Item #{orcamento.id} enviado para a Diretoria da area {area}.")
            elif recorrencia == "Repetir todos os meses do ano":
                ids = criar_orcamentos_recorrentes(dados, "01", "12")
                st.success(f"{len(ids)} itens enviados para a Diretoria da area {area}.")
            else:
                ids = criar_orcamentos_recorrentes(dados, mes, mes_final)
                st.success(f"{len(ids)} itens enviados para a Diretoria da area {area}.")
        except Exception as exc:  # noqa: BLE001
            st.error(str(exc))

with tab_ajustes:
    mensagens = listar_mensagens_gestor(gestor_visualizado)
    df_ajustes = df_meus[df_meus["status"] == "Ajuste Solicitado"] if not df_meus.empty else pd.DataFrame()
    if mensagens.empty and df_ajustes.empty:
        st.info("Nenhuma mensagem de ajuste recebida.")
    else:
        st.subheader("Ajustes solicitados pela Diretoria")
        st.caption("Escolha um item, leia o comentario e corrija aqui mesmo. Ao salvar, ele volta para a fila da Diretoria.")
        if not mensagens.empty:
            st.dataframe(mensagens, use_container_width=True, hide_index=True, height=220)

        if df_ajustes.empty:
            st.info("Nao ha itens em ajuste abertos para edicao.")
        else:
            opcoes = {
                f"#{int(row.id)} | {row.area} | {row.descricao} | {moeda(row.valor_solicitado)}": int(row.id)
                for row in df_ajustes.itertuples()
            }
            escolhido_label = st.selectbox("Item para corrigir", list(opcoes.keys()))
            selecionado_ajuste = opcoes[escolhido_label]
            item = df_ajustes[df_ajustes["id"] == selecionado_ajuste].iloc[0]

            if not mensagens.empty:
                msg_item = mensagens[mensagens["orcamento_id"] == selecionado_ajuste]
                if not msg_item.empty:
                    ultima = msg_item.iloc[0]
                    st.warning(f"Solicitado por {ultima['de']}: {ultima['mensagem']}")

            with st.form("corrigir_ajuste_gestor"):
                c1, c2, c3 = st.columns(3)
                ano_a = c1.number_input("Ano", min_value=2024, max_value=2035, value=int(item["ano"]), key="aj_ano")
                area_a = c2.selectbox("Area", AREAS_ORCAMENTO, index=AREAS_ORCAMENTO.index(item["area"]) if item["area"] in AREAS_ORCAMENTO else 0, key="aj_area")
                centro_a = c3.text_input("Centro de custo", value=item["centro_custo"], key="aj_centro")

                c4, c5, c6 = st.columns(3)
                conta_a = c4.text_input("Conta contabil", value=item["conta_contabil"], key="aj_conta")
                mes_a = c5.selectbox("Mes", [str(i).zfill(2) for i in range(1, 13)], index=int(item["mes"]) - 1, key="aj_mes")
                tipo_a = c6.selectbox("Tipo", TIPOS_ORCAMENTO, index=TIPOS_ORCAMENTO.index(item["tipo"]) if item["tipo"] in TIPOS_ORCAMENTO else 0, key="aj_tipo")

                descricao_a = st.text_input("Descricao", value=item["descricao"], key="aj_desc")
                valor_a = st.number_input("Valor ajustado", min_value=0.0, value=float(item["valor_solicitado"]), step=100.0, format="%.2f", key="aj_valor")
                prioridade_a = st.selectbox("Prioridade", ["Baixa", "Media", "Alta"], index=["Baixa", "Media", "Alta"].index(item["prioridade"]), key="aj_prioridade")
                justificativa_a = st.text_area("Justificativa atualizada", value=item["justificativa"], key="aj_just")
                resposta = st.text_area("Resposta para Diretoria", value="Item ajustado conforme solicitado.", key="aj_resp")
                enviar = st.form_submit_button("Reenviar para Diretoria", type="primary")

            if enviar:
                try:
                    atualizar_orcamento_gestor(
                        int(selecionado_ajuste),
                        {
                            "ano": ano_a,
                            "gestor": gestor_visualizado,
                            "area": area_a,
                            "centro_custo": centro_a,
                            "conta_contabil": conta_a,
                            "descricao": descricao_a,
                            "mes": mes_a,
                            "tipo": tipo_a,
                            "valor_solicitado": valor_a,
                            "justificativa": justificativa_a,
                            "prioridade": prioridade_a,
                        },
                        resposta,
                    )
                    st.success("Ajuste reenviado para Diretoria.")
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))

with tab_upload:
    st.write("O arquivo deve conter as colunas obrigatorias. Use areas padrao: Administrativo, Comercial ou Industrial.")
    exemplo = pd.DataFrame(
        [
            {
                "ano": 2026,
                "gestor": gestor_visualizado,
                "area": "Comercial",
                "centro_custo": "COM",
                "conta_contabil": "3.4.01.003",
                "descricao": "Campanha de geracao de demanda",
                "mes": "01",
                "tipo": "Despesa",
                "valor_solicitado": 50000,
                "justificativa": "Acao prevista para gerar pipeline comercial",
                "prioridade": "Alta",
            }
        ]
    )
    st.dataframe(exemplo, use_container_width=True, hide_index=True)
    arquivo = st.file_uploader("Enviar Excel ou CSV", type=["xlsx", "xls", "csv"])
    if arquivo and st.button("Importar arquivo", type="primary"):
        inseridos, erros = importar_arquivo(arquivo)
        if inseridos:
            st.success(f"{inseridos} linhas importadas com sucesso.")
        if erros:
            st.error("Algumas linhas nao foram importadas.")
            st.write(erros)
