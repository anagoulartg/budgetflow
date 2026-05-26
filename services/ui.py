import streamlit as st

from services.auth import bloco_login


CHART_COLORS = ["#1E4E8C", "#16877A", "#D98C24", "#7A5FB5", "#C75146", "#4F6F52", "#557A95"]
STATUS_COLORS = {
    "Pendente": "#D98C24",
    "Ajuste Solicitado": "#B86B00",
    "Aprovado Diretoria": "#2E7D5B",
    "Aprovado Final": "#16877A",
    "Reprovado Diretoria": "#C75146",
    "Reprovado Final": "#A83D38",
}
TIPO_COLORS = {
    "Receita": "#1E4E8C",
    "Despesa": "#C75146",
    "Investimento": "#7A5FB5",
}


def configurar_pagina(titulo: str) -> None:
    st.set_page_config(page_title=f"{titulo} - BudgetFlow", page_icon="BF", layout="wide")
    aplicar_estilo()
    bloco_login(titulo)


def aplicar_estilo() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bf-bg: #f5f7fb;
            --bf-panel: #ffffff;
            --bf-panel-soft: #eef4fb;
            --bf-border: #d9e1ec;
            --bf-border-strong: #9fb0c3;
            --bf-text: #111827;
            --bf-muted: #667085;
            --bf-navy: #06203d;
            --bf-navy-2: #0a2e55;
            --bf-blue: #2563eb;
            --bf-blue-strong: #1d4ed8;
            --bf-green: #22a06b;
            --bf-amber: #f59e0b;
            --bf-red: #ef4444;
            --bf-cyan: #14b8a6;
        }
        .stApp {
            background: var(--bf-bg);
            color: var(--bf-text);
        }
        .main .block-container {
            max-width: 1440px;
            padding-top: 1.4rem;
            padding-bottom: 2.4rem;
        }
        [data-testid="stSidebar"] {
            background: var(--bf-navy);
            border-right: 0;
        }
        [data-testid="stSidebar"] * {
            color: #e5edf7;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.12);
        }
        section[data-testid="stSidebar"] .stButton button {
            width: 100%;
            background: rgba(37, 99, 235, 0.18);
            border-color: rgba(255, 255, 255, 0.18);
            color: #ffffff;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            background: rgba(37, 99, 235, 0.34);
            border-color: rgba(255, 255, 255, 0.32);
        }
        section[data-testid="stSidebar"] input {
            background: #ffffff !important;
            color: #111827 !important;
        }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
            color: #d7e3f2 !important;
        }
        section[data-testid="stSidebar"] a:not(.bf-nav-link) {
            color: #e5edf7 !important;
            border-radius: 8px !important;
            padding: 9px 12px !important;
            margin: 2px 10px !important;
            text-decoration: none !important;
            box-shadow: none !important;
            background: rgba(6, 32, 61, 0.96) !important;
            background-image: none !important;
            filter: none !important;
            justify-content: flex-start !important;
            font-weight: 700 !important;
            min-height: 40px !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
        }
        section[data-testid="stSidebar"] a:not(.bf-nav-link) span,
        section[data-testid="stSidebar"] a:not(.bf-nav-link) p {
            line-height: 1.2 !important;
            white-space: nowrap !important;
        }
        section[data-testid="stSidebar"] a:not(.bf-nav-link)::before,
        section[data-testid="stSidebar"] a:not(.bf-nav-link)::after {
            background: transparent !important;
            background-image: none !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] a:not(.bf-nav-link):hover {
            background: rgba(255, 255, 255, 0.08) !important;
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] a:not(.bf-nav-link)[aria-current="page"],
        section[data-testid="stSidebar"] a:not(.bf-nav-link)[aria-selected="true"] {
            background: #1d4ed8 !important;
            color: #ffffff !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none !important;
        }
        .bf-side-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 4px 8px 18px 8px;
            margin-bottom: 14px;
            border-bottom: 1px solid rgba(255,255,255,0.12);
        }
        .bf-side-mark {
            width: 28px;
            height: 38px;
            display: flex;
            gap: 4px;
            align-items: flex-end;
        }
        .bf-side-mark span {
            display: block;
            width: 8px;
            border-radius: 2px;
        }
        .bf-side-title {
            font-size: 1.08rem;
            font-weight: 850;
            line-height: 1.05;
            color: #ffffff;
        }
        .bf-side-subtitle {
            color: #b9c8da;
            font-size: 0.72rem;
            margin-top: 3px;
        }
        .bf-nav {
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin: 0 0 18px 0;
        }
        .bf-nav-link {
            display: block;
            padding: 10px 12px;
            border-radius: 8px;
            color: #dce8f7 !important;
            text-decoration: none !important;
            border: 1px solid transparent;
        }
        .bf-nav-link:hover {
            background: rgba(255,255,255,0.08);
            color: #ffffff !important;
        }
        .bf-nav-link.active {
            background: #1d4ed8;
            color: #ffffff !important;
            box-shadow: inset 3px 0 0 #60a5fa;
        }
        .bf-nav-title {
            display: block;
            font-size: 0.9rem;
            font-weight: 800;
            line-height: 1.2;
        }
        .bf-nav-caption {
            display: block;
            color: #b9c8da;
            font-size: 0.68rem;
            margin-top: 2px;
        }
        div[data-testid="stMetric"] {
            background: var(--bf-panel);
            border: 1px solid var(--bf-border);
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 2px 8px rgba(23, 33, 47, 0.05);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--bf-muted);
            font-size: 0.88rem;
            font-weight: 650;
        }
        div[data-testid="stMetricValue"] {
            color: var(--bf-text);
            font-size: 1.38rem;
            font-weight: 760;
        }
        div[data-testid="stMetricDelta"] {
            font-weight: 700;
        }
        .bf-panel {
            background: var(--bf-panel);
            border: 1px solid var(--bf-border);
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(23, 33, 47, 0.05);
        }
        .bf-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 2px 18px 2px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12);
            margin-bottom: 14px;
        }
        .bf-logo {
            width: 30px;
            height: 38px;
            border-radius: 7px;
            background: linear-gradient(160deg, #47d68c 0%, #14b8a6 45%, #2563eb 100%);
            box-shadow: 0 10px 24px rgba(20, 184, 166, 0.28);
        }
        .bf-brand-title {
            font-size: 1.12rem;
            line-height: 1.1;
            font-weight: 850;
            color: #ffffff;
        }
        .bf-brand-subtitle {
            margin-top: 3px;
            font-size: 0.72rem;
            color: #b9c8da;
        }
        .bf-kpi {
            background: #ffffff;
            border: 1px solid var(--bf-border);
            border-radius: 8px;
            padding: 14px 14px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            min-height: 96px;
            display: flex;
            align-items: center;
            gap: 11px;
            min-width: 0;
            overflow: hidden;
        }
        .bf-kpi-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 850;
            font-size: 0.82rem;
            flex: 0 0 auto;
        }
        .bf-kpi-label {
            color: var(--bf-muted);
            font-size: 0.76rem;
            font-weight: 700;
            margin-bottom: 4px;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        .bf-kpi-value {
            color: var(--bf-text);
            font-size: 1.05rem;
            font-weight: 850;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        .bf-kpi-note {
            color: var(--bf-muted);
            font-size: 0.75rem;
            margin-top: 4px;
        }
        .bf-muted {
            color: var(--bf-muted);
        }
        h1, h2, h3 {
            color: var(--bf-text);
            letter-spacing: 0;
        }
        h1 {
            font-size: 1.6rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }
        h2, h3 {
            font-weight: 750;
        }
        .stCaptionContainer, p, label, span {
            color: var(--bf-text);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom: 1px solid var(--bf-border);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px 8px 0 0;
            color: var(--bf-muted);
            font-weight: 700;
        }
        .stTabs [aria-selected="true"] {
            background: #ffffff;
            color: var(--bf-blue);
            border: 1px solid var(--bf-border);
            border-bottom: 1px solid #ffffff;
        }
        .stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] button {
            border-radius: 8px;
            border: 1px solid var(--bf-blue);
            background: var(--bf-blue);
            color: #ffffff;
            font-weight: 750;
            min-height: 2.45rem;
        }
        .stButton button:hover, .stDownloadButton button:hover, div[data-testid="stFormSubmitButton"] button:hover {
            background: var(--bf-blue-strong);
            border-color: var(--bf-blue-strong);
            color: #ffffff;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--bf-border);
            border-radius: 8px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stPlotlyChart"] {
            background: #ffffff;
            border: 1px solid var(--bf-border);
            border-radius: 8px;
            padding: 10px 12px 4px 12px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        div[data-baseweb="select"] > div, input, textarea {
            border-color: var(--bf-border) !important;
            border-radius: 8px !important;
            background: #ffffff !important;
        }
        div[data-baseweb="select"]:focus-within > div, input:focus, textarea:focus {
            border-color: var(--bf-blue) !important;
            box-shadow: 0 0 0 2px rgba(30, 78, 140, 0.14) !important;
        }
        .stAlert {
            border-radius: 8px;
            border: 1px solid var(--bf-border);
        }
        hr {
            border-color: var(--bf-border);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def aplicar_tema_grafico(fig, altura: int | None = None):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Arial, sans-serif", "color": "#17212f", "size": 13},
        title={"font": {"size": 17, "color": "#17212f"}, "x": 0.02, "xanchor": "left"},
        legend={"orientation": "h", "yanchor": "top", "y": -0.18, "xanchor": "left", "x": 0},
        margin={"l": 20, "r": 20, "t": 54, "b": 82},
        colorway=CHART_COLORS,
        hoverlabel={"bgcolor": "#17212f", "font_color": "#ffffff"},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#cfd8e3", tickfont={"color": "#5f6f82"})
    fig.update_yaxes(gridcolor="#e8eef5", zeroline=False, tickfont={"color": "#5f6f82"})
    if altura:
        fig.update_layout(height=altura)
    return fig


def kpi_card(label: str, value: str, accent: str = "#2563eb", icon: str = "R$", note: str = "") -> None:
    st.markdown(
        f"""
        <div class="bf-kpi">
            <div class="bf-kpi-icon" style="background:{accent};">{icon}</div>
            <div>
                <div class="bf-kpi-label">{label}</div>
                <div class="bf-kpi-value">{value}</div>
                <div class="bf-kpi-note">{note}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def moeda(valor: float | int | None) -> str:
    valor = float(valor or 0)
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def percentual(valor: float | int | None) -> str:
    return f"{float(valor or 0):.1f}%".replace(".", ",")
