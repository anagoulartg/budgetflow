from datetime import datetime

import pandas as pd
from sqlalchemy import select

from database.db import get_session
from database.models import HistoricoAprovacao, Orcamento


STATUS_DIRETORIA = {
    "Aprovar": "Aprovado Diretoria",
    "Reprovar": "Reprovado Diretoria",
    "Solicitar ajuste": "Ajuste Solicitado",
}

STATUS_CONSELHO = {
    "Aprovar final": "Aprovado Final",
    "Reprovar final": "Reprovado Final",
}


def registrar_decisao(
    orcamento_id: int,
    usuario_decisor: str,
    perfil_decisor: str,
    novo_status: str,
    comentario: str,
    novo_valor: float | None = None,
) -> None:
    if not comentario.strip():
        raise ValueError("Informe um comentario para registrar a decisao.")

    with get_session() as session:
        orcamento = session.get(Orcamento, orcamento_id)
        if not orcamento:
            raise ValueError("Orcamento nao encontrado.")

        status_anterior = orcamento.status
        valor_anterior = orcamento.valor_final if perfil_decisor == "Conselho" else orcamento.valor_aprovado

        if perfil_decisor == "Diretoria":
            orcamento.valor_aprovado = novo_valor if novo_valor is not None else orcamento.valor_solicitado
        elif perfil_decisor == "Conselho":
            base = orcamento.valor_aprovado if orcamento.valor_aprovado is not None else orcamento.valor_solicitado
            orcamento.valor_final = novo_valor if novo_valor is not None else base

        orcamento.status = novo_status
        orcamento.atualizado_em = datetime.utcnow()

        historico = HistoricoAprovacao(
            orcamento_id=orcamento.id,
            usuario_decisor=usuario_decisor,
            perfil_decisor=perfil_decisor,
            status_anterior=status_anterior,
            novo_status=novo_status,
            valor_anterior=valor_anterior,
            novo_valor=novo_valor,
            comentario=comentario.strip(),
        )
        session.add(historico)
        session.commit()


def listar_historico(orcamento_id: int | None = None) -> pd.DataFrame:
    with get_session() as session:
        query = select(HistoricoAprovacao)
        if orcamento_id:
            query = query.where(HistoricoAprovacao.orcamento_id == orcamento_id)
        rows = session.execute(query.order_by(HistoricoAprovacao.data_hora.desc())).scalars().all()
        return pd.DataFrame(
            [
                {
                    "id": row.id,
                    "orcamento_id": row.orcamento_id,
                    "usuario_decisor": row.usuario_decisor,
                    "perfil_decisor": row.perfil_decisor,
                    "data_hora": row.data_hora,
                    "status_anterior": row.status_anterior,
                    "novo_status": row.novo_status,
                    "valor_anterior": row.valor_anterior,
                    "novo_valor": row.novo_valor,
                    "comentario": row.comentario,
                }
                for row in rows
            ]
        )


def listar_mensagens_gestor(gestor: str | None = None) -> pd.DataFrame:
    with get_session() as session:
        query = (
            select(HistoricoAprovacao, Orcamento)
            .join(Orcamento, Orcamento.id == HistoricoAprovacao.orcamento_id)
            .where(HistoricoAprovacao.novo_status == "Ajuste Solicitado")
            .where(Orcamento.status == "Ajuste Solicitado")
        )
        if gestor:
            query = query.where(Orcamento.gestor == gestor)
        rows = session.execute(query.order_by(HistoricoAprovacao.data_hora.desc())).all()
        df = pd.DataFrame(
            [
                {
                    "orcamento_id": historico.orcamento_id,
                    "data_hora": historico.data_hora,
                    "de": historico.usuario_decisor,
                    "perfil": historico.perfil_decisor,
                    "area": orcamento.area,
                    "descricao": orcamento.descricao,
                    "valor_solicitado": orcamento.valor_solicitado,
                    "status": orcamento.status,
                    "mensagem": historico.comentario,
                    "acao_necessaria": "Editar e reenviar",
                }
                for historico, orcamento in rows
            ]
        )
        if df.empty:
            return df
        return df.drop_duplicates(subset=["orcamento_id"], keep="first")


def resumo_executivo(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "solicitado": 0,
            "aprovado": 0,
            "economia": 0,
            "receita": 0,
            "despesa_investimento": 0,
            "itens": 0,
        }
    aprovado = df["valor_final"].fillna(df["valor_aprovado"]).fillna(0).sum()
    solicitado = df["valor_solicitado"].sum()
    receita = df[df["tipo"] == "Receita"]["valor_solicitado"].sum()
    gasto = df[df["tipo"].isin(["Despesa", "Investimento"])]["valor_solicitado"].sum()
    return {
        "solicitado": solicitado,
        "aprovado": aprovado,
        "economia": solicitado - aprovado,
        "receita": receita,
        "despesa_investimento": gasto,
        "itens": len(df),
    }


def analisar_cenarios(df: pd.DataFrame, meta_reducao: float) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["area", "solicitado", "meta", "corte_sugerido"])
    base = df[df["tipo"].isin(["Despesa", "Investimento"])].copy()
    if base.empty:
        return pd.DataFrame(columns=["area", "solicitado", "meta", "corte_sugerido"])
    agrupado = base.groupby("area", as_index=False)["valor_solicitado"].sum().rename(columns={"valor_solicitado": "solicitado"})
    agrupado["meta"] = agrupado["solicitado"] * (1 - meta_reducao / 100)
    agrupado["corte_sugerido"] = agrupado["solicitado"] - agrupado["meta"]
    return agrupado.sort_values("corte_sugerido", ascending=False)
