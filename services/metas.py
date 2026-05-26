import pandas as pd
from sqlalchemy import delete, select

from database.db import get_session
from database.models import MetaOrcamentaria


AREAS_PADRAO = ["Administrativo", "Comercial", "Industrial"]
TIPOS_META = ["Despesa", "Investimento"]


def listar_metas(ano: int | None = None) -> pd.DataFrame:
    with get_session() as session:
        query = select(MetaOrcamentaria)
        if ano:
            query = query.where(MetaOrcamentaria.ano == int(ano))
        rows = session.execute(query.order_by(MetaOrcamentaria.ano.desc(), MetaOrcamentaria.area, MetaOrcamentaria.tipo)).scalars().all()
        return pd.DataFrame(
            [
                {
                    "id": row.id,
                    "ano": row.ano,
                    "area": row.area,
                    "tipo": row.tipo,
                    "valor_meta": row.valor_meta,
                    "observacao": row.observacao or "",
                    "atualizado_em": row.atualizado_em,
                }
                for row in rows
            ]
        )


def salvar_metas(df: pd.DataFrame, ano: int) -> int:
    obrigatorias = {"area", "tipo", "valor_meta"}
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(f"Colunas ausentes: {', '.join(sorted(faltantes))}")

    with get_session() as session:
        session.execute(delete(MetaOrcamentaria).where(MetaOrcamentaria.ano == int(ano)))
        total = 0
        for _, row in df.iterrows():
            area = str(row["area"]).strip()
            tipo = str(row["tipo"]).strip().title()
            if not area or tipo not in TIPOS_META:
                continue
            valor = float(row["valor_meta"] or 0)
            session.add(
                MetaOrcamentaria(
                    ano=int(ano),
                    area=area,
                    tipo=tipo,
                    valor_meta=valor,
                    observacao=str(row.get("observacao", "") or "").strip(),
                )
            )
            total += 1
        session.commit()
        return total


def template_metas(ano: int) -> pd.DataFrame:
    atual = listar_metas(ano)
    if not atual.empty:
        return atual[["area", "tipo", "valor_meta", "observacao"]]
    return pd.DataFrame(
        [
            {"area": area, "tipo": tipo, "valor_meta": 0.0, "observacao": ""}
            for area in AREAS_PADRAO
            for tipo in TIPOS_META
        ]
    )


def metas_por_area(ano: int, area: str | None = None) -> pd.DataFrame:
    metas = listar_metas(ano)
    if area and not metas.empty:
        metas = metas[metas["area"] == area]
    return metas


def meta_total(metas: pd.DataFrame, tipo: str | None = None) -> float:
    if metas.empty:
        return 0.0
    base = metas
    if tipo:
        base = base[base["tipo"] == tipo]
    return float(base["valor_meta"].sum())
