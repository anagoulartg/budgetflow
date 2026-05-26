from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Iterable

import pandas as pd
from sqlalchemy import select

from database.db import get_session
from database.models import Orcamento


CAMPOS_OBRIGATORIOS = [
    "ano",
    "gestor",
    "area",
    "centro_custo",
    "conta_contabil",
    "descricao",
    "mes",
    "tipo",
    "valor_solicitado",
    "justificativa",
    "prioridade",
]

TIPOS_VALIDOS = {"Receita", "Despesa", "Investimento"}
PRIORIDADES_VALIDAS = {"Baixa", "Media", "Alta"}
AREAS_ORCAMENTO = ["Administrativo", "Comercial", "Industrial"]
TIPOS_ORCAMENTO = ["Despesa", "Investimento"]


def normalizar_mes(valor) -> str:
    mes = str(valor).strip().replace(".0", "")
    if mes.isdigit():
        mes = mes.zfill(2)
    if mes not in {str(i).zfill(2) for i in range(1, 13)}:
        raise ValueError("Mes deve estar entre 01 e 12.")
    return mes


def validar_orcamento(dados: dict) -> dict:
    erros = []
    normalizado = {}

    for campo in CAMPOS_OBRIGATORIOS:
        valor = dados.get(campo)
        if valor is None or pd.isna(valor) or str(valor).strip() == "":
            erros.append(f"Campo obrigatorio ausente: {campo}")
        normalizado[campo] = valor

    if erros:
        raise ValueError("; ".join(erros))

    try:
        normalizado["ano"] = int(normalizado["ano"])
    except ValueError as exc:
        raise ValueError("Ano deve ser numerico.") from exc

    normalizado["mes"] = normalizar_mes(normalizado["mes"])

    tipo = str(normalizado["tipo"]).strip().title()
    if tipo not in TIPOS_VALIDOS:
        raise ValueError("Tipo deve ser Receita, Despesa ou Investimento.")
    normalizado["tipo"] = tipo

    prioridade = str(normalizado["prioridade"]).strip().title()
    if prioridade in {"Média", "MÃ©dia"}:
        prioridade = "Media"
    if prioridade not in PRIORIDADES_VALIDAS:
        raise ValueError("Prioridade deve ser Baixa, Media ou Alta.")
    normalizado["prioridade"] = prioridade

    try:
        normalizado["valor_solicitado"] = float(normalizado["valor_solicitado"])
    except ValueError as exc:
        raise ValueError("Valor solicitado deve ser numerico.") from exc

    for campo in ["gestor", "area", "centro_custo", "conta_contabil", "descricao", "justificativa"]:
        normalizado[campo] = str(normalizado[campo]).strip()

    normalizado["status"] = "Pendente"
    normalizado["valor_aprovado"] = None
    normalizado["valor_final"] = None
    return normalizado


def criar_orcamento(dados: dict) -> Orcamento:
    payload = validar_orcamento(dados)
    with get_session() as session:
        orcamento = Orcamento(**payload)
        session.add(orcamento)
        session.commit()
        session.refresh(orcamento)
        return orcamento


def criar_orcamentos_recorrentes(dados: dict, mes_inicial: str, mes_final: str) -> list[int]:
    inicio = int(normalizar_mes(mes_inicial))
    fim = int(normalizar_mes(mes_final))
    if fim < inicio:
        raise ValueError("Mes final deve ser maior ou igual ao mes inicial.")

    ids = []
    for mes in range(inicio, fim + 1):
        payload = dict(dados)
        payload["mes"] = str(mes).zfill(2)
        orcamento = criar_orcamento(payload)
        ids.append(orcamento.id)
    return ids


def atualizar_orcamento_gestor(orcamento_id: int, dados: dict, comentario: str) -> None:
    from database.models import HistoricoAprovacao

    if not comentario.strip():
        raise ValueError("Informe um comentario explicando o ajuste enviado.")

    payload = validar_orcamento(dados)
    with get_session() as session:
        orcamento = session.get(Orcamento, orcamento_id)
        if not orcamento:
            raise ValueError("Orcamento nao encontrado.")
        if orcamento.status not in ["Pendente", "Ajuste Solicitado"]:
            raise ValueError("Apenas itens pendentes ou com ajuste solicitado podem ser alterados pelo gestor.")

        status_anterior = orcamento.status
        valor_anterior = orcamento.valor_solicitado
        for campo, valor in payload.items():
            if hasattr(orcamento, campo):
                setattr(orcamento, campo, valor)

        orcamento.status = "Pendente"
        orcamento.valor_aprovado = None
        orcamento.valor_final = None
        orcamento.atualizado_em = datetime.utcnow()
        session.add(
            HistoricoAprovacao(
                orcamento_id=orcamento.id,
                usuario_decisor=orcamento.gestor,
                perfil_decisor="Gestor",
                status_anterior=status_anterior,
                novo_status="Pendente",
                valor_anterior=valor_anterior,
                novo_valor=orcamento.valor_solicitado,
                comentario=comentario.strip(),
            )
        )
        session.commit()


def excluir_orcamento_gestor(orcamento_id: int, gestor: str) -> None:
    with get_session() as session:
        orcamento = session.get(Orcamento, orcamento_id)
        if not orcamento:
            raise ValueError("Orcamento nao encontrado.")
        if orcamento.gestor != gestor:
            raise ValueError("Voce so pode excluir solicitacoes criadas por voce.")
        if orcamento.status not in ["Pendente", "Ajuste Solicitado"]:
            raise ValueError("Apenas solicitacoes pendentes ou em ajuste podem ser excluidas.")
        session.delete(orcamento)
        session.commit()


def importar_arquivo(uploaded_file) -> tuple[int, list[str]]:
    nome = uploaded_file.name.lower()
    conteudo = uploaded_file.read()
    if nome.endswith(".csv"):
        df = pd.read_csv(BytesIO(conteudo), sep=None, engine="python")
    else:
        df = pd.read_excel(BytesIO(conteudo))

    df.columns = [str(col).strip().lower() for col in df.columns]
    faltantes = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in df.columns]
    if faltantes:
        return 0, [f"Colunas obrigatorias ausentes: {', '.join(faltantes)}"]

    inseridos = 0
    erros = []
    for idx, row in df.iterrows():
        try:
            criar_orcamento(row.to_dict())
            inseridos += 1
        except Exception as exc:  # noqa: BLE001
            erros.append(f"Linha {idx + 2}: {exc}")

    return inseridos, erros


def listar_orcamentos(status: str | Iterable[str] | None = None) -> pd.DataFrame:
    with get_session() as session:
        query = select(Orcamento)
        if status:
            if isinstance(status, str):
                query = query.where(Orcamento.status == status)
            else:
                query = query.where(Orcamento.status.in_(list(status)))
        rows = session.execute(query.order_by(Orcamento.ano.desc(), Orcamento.area, Orcamento.mes)).scalars().all()
        return pd.DataFrame([orcamento_para_dict(row) for row in rows])


def filtrar_orcamentos(
    df: pd.DataFrame,
    anos: list[int] | None = None,
    areas: list[str] | None = None,
    centros: list[str] | None = None,
    tipos: list[str] | None = None,
    statuses: list[str] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df
    filtrado = df.copy()
    if anos:
        filtrado = filtrado[filtrado["ano"].isin(anos)]
    if areas:
        filtrado = filtrado[filtrado["area"].isin(areas)]
    if centros:
        filtrado = filtrado[filtrado["centro_custo"].isin(centros)]
    if tipos:
        filtrado = filtrado[filtrado["tipo"].isin(tipos)]
    if statuses:
        filtrado = filtrado[filtrado["status"].isin(statuses)]
    return filtrado


def obter_orcamento(orcamento_id: int) -> Orcamento | None:
    with get_session() as session:
        return session.get(Orcamento, orcamento_id)


def orcamento_para_dict(orcamento: Orcamento) -> dict:
    return {
        "id": orcamento.id,
        "ano": orcamento.ano,
        "gestor": orcamento.gestor,
        "area": orcamento.area,
        "centro_custo": orcamento.centro_custo,
        "conta_contabil": orcamento.conta_contabil,
        "descricao": orcamento.descricao,
        "mes": orcamento.mes,
        "tipo": orcamento.tipo,
        "valor_solicitado": orcamento.valor_solicitado,
        "valor_aprovado": orcamento.valor_aprovado,
        "valor_final": orcamento.valor_final,
        "justificativa": orcamento.justificativa,
        "prioridade": orcamento.prioridade,
        "status": orcamento.status,
        "criado_em": orcamento.criado_em,
        "atualizado_em": orcamento.atualizado_em,
    }


def popular_dados_exemplo() -> int:
    exemplos = [
        [2026, "gestor.demo", "Administrativo", "ADM", "3.1.01.001", "Servicos administrativos", "01", "Despesa", 15000, "Contrato anual de apoio administrativo", "Alta"],
        [2026, "gestor.demo", "Comercial", "COM", "3.4.01.003", "Campanhas digitais", "02", "Despesa", 60000, "Geracao de demanda comercial", "Media"],
        [2026, "gestor.demo", "Industrial", "IND", "3.2.02.010", "Manutencao preventiva", "03", "Despesa", 45000, "Evitar parada de linha", "Alta"],
        [2026, "gestor.demo", "Industrial", "IND", "1.2.03.004", "Equipamento de producao", "04", "Investimento", 90000, "Aumento de capacidade industrial", "Media"],
        [2026, "gestor.demo", "Comercial", "COM", "3.4.01.010", "Evento com clientes", "05", "Despesa", 85000, "Relacionamento e retencao de contas chave", "Alta"],
        [2026, "gestor.demo", "Administrativo", "ADM", "3.1.05.002", "Auditoria externa", "06", "Despesa", 30000, "Obrigacao anual", "Alta"],
    ]
    for item in exemplos:
        criar_orcamento(
            {
                "ano": item[0],
                "gestor": item[1],
                "area": item[2],
                "centro_custo": item[3],
                "conta_contabil": item[4],
                "descricao": item[5],
                "mes": item[6],
                "tipo": item[7],
                "valor_solicitado": item[8],
                "justificativa": item[9],
                "prioridade": item[10],
            }
        )
    return len(exemplos)
