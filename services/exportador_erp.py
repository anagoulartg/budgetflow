from datetime import datetime
from pathlib import Path

import pandas as pd

from services.orcamentos import listar_orcamentos


BASE_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE_DIR / "exports"
COLUNAS_ERP = [
    "empresa",
    "ano",
    "centro_custo",
    "conta_contabil",
    "mes",
    "valor_aprovado",
    "historico",
    "tipo",
]


def dados_erp(empresa: str = "001") -> pd.DataFrame:
    df = listar_orcamentos("Aprovado Final")
    if df.empty:
        return pd.DataFrame(columns=COLUNAS_ERP)

    final = pd.DataFrame(
        {
            "empresa": empresa,
            "ano": df["ano"],
            "centro_custo": df["centro_custo"],
            "conta_contabil": df["conta_contabil"],
            "mes": df["mes"],
            "valor_aprovado": df["valor_final"].fillna(df["valor_aprovado"]).fillna(df["valor_solicitado"]),
            "historico": "Orcamento aprovado " + df["area"].astype(str),
            "tipo": df["tipo"],
        }
    )
    return final[COLUNAS_ERP]


def exportar_csv(empresa: str = "001") -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = dados_erp(empresa)
    caminho = EXPORTS_DIR / f"budgetflow_erp_{timestamp()}.csv"
    df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
    return caminho


def exportar_excel(empresa: str = "001") -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = dados_erp(empresa)
    caminho = EXPORTS_DIR / f"budgetflow_erp_{timestamp()}.xlsx"
    df.to_excel(caminho, index=False, engine="openpyxl")
    return caminho


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
