# =============================================================================
# DASHBOARD — Mercado de Trabalho Brasileiro (2012–2025)
# Versão 2.0 — Páginas separadas + busca rápida + tratamento robusto de nulos
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Mercado de Trabalho Brasileiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CSS GLOBAL
# =============================================================================

st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    h1 { color: #1F4E79 !important; }
    h2 { color: #2E75B6 !important; }
    h3 { color: #2E4A7A !important; }

    .intro-box {
        background: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
        color: white; padding: 1.5rem 2rem;
        border-radius: 10px; margin-bottom: 1.5rem;
    }
    .intro-box p { color: white !important; margin: 0.3rem 0; font-size: 0.95rem; }

    .kpi-card {
        background: white; border-radius: 10px;
        padding: 1.2rem 1.4rem; border-left: 5px solid #2E75B6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07); text-align: center;
    }
    .kpi-label { font-size: 0.76rem; color: #666; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
    .kpi-value { font-size: 2.1rem; font-weight: 700; color: #1F4E79; line-height: 1.1; }
    .kpi-sub   { font-size: 0.74rem; color: #888; margin-top: 0.25rem; }
    .kpi-delta-up   { font-size: 0.79rem; color: #C0392B; font-weight: 600; }
    .kpi-delta-down { font-size: 0.79rem; color: #1E8449; font-weight: 600; }

    .story-box {
        background: #EBF3FB; border-left: 4px solid #2E75B6;
        padding: 0.9rem 1.2rem; border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1.2rem 0; font-size: 0.92rem; color: #2C3E50;
    }
    .story-box b { color: #1F4E79; }

    .alert-box {
        background: #FEF9E7; border-left: 4px solid #F39C12;
        padding: 0.9rem 1.2rem; border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1.2rem 0; font-size: 0.92rem; color: #7D6608;
    }
    .conclusion-box {
        background: #EAFAF1; border-left: 4px solid #1E8449;
        padding: 0.9rem 1.2rem; border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1.2rem 0; font-size: 0.92rem; color: #1E4D2B;
    }
    .warn-box {
        background: #FDF2F8; border-left: 4px solid #8E44AD;
        padding: 0.7rem 1rem; border-radius: 0 6px 6px 0;
        margin: 0.4rem 0 0.8rem 0; font-size: 0.85rem; color: #6C3483;
    }

    /* Barra de busca destaque */
    .search-hit {
        background: #FFF9C4; border-left: 4px solid #F1C40F;
        padding: 0.6rem 1rem; border-radius: 0 6px 6px 0;
        margin-bottom: 0.5rem; font-size: 0.88rem;
    }

    .nav-pill {
        display: inline-block; background: #EBF3FB;
        color: #1F4E79; border-radius: 20px;
        padding: 0.2rem 0.8rem; font-size: 0.8rem;
        font-weight: 600; margin: 0.1rem;
        cursor: pointer;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CARREGAMENTO E TRATAMENTO DE DADOS
# =============================================================================

@st.cache_data
def carregar_dados():
    """
    Carrega os CSVs e aplica tratamento robusto de valores nulos:

    1. Zeros → NaN  (zeros = ausência real de dado, não valor zero)
    2. Interpolação linear temporal para preencher lacunas internas
       (ex: lacuna 2020-T2 a 2022-T1) — evita quebras/saltos nos gráficos
    3. Cria coluna 'interpolado' (bool) para marcar pontos estimados
    4. Mantém cópias _raw sem interpolação para tabelas e KPIs

    Regras por série:
    - desocupacao.csv  → separador ';'
    - emprego.csv      → separador ','
    - informalidade.csv → separador ';', dados só a partir de 2015-T3
    """
    leituras = {
        "desocupacao": dict(path="desocupacao.csv", sep=";"),
        "emprego":     dict(path="emprego.csv",     sep=","),
        "informalidade": dict(path="informalidade.csv", sep=";"),
    }

    resultados = {}
    for nome, cfg in leituras.items():
        df = pd.read_csv(cfg["path"], sep=cfg["sep"])

        # --- Conversão de tipos ---
        df["periodo"] = pd.to_datetime(df["periodo"])
        df["ano"] = df["periodo"].dt.year
        df["trimestre"] = df["periodo"].dt.quarter
        df["label_trim"] = df["ano"].astype(str) + " T" + df["trimestre"].astype(str)

        # --- Passo 1: substituir zeros por NaN ---
        # Zeros indicam ausência de coleta (lacuna pandemia 2020-T2→2022-T1
        # e informalidade sem dados antes de 2015-T3)
        for col in ["total", "homens", "mulheres"]:
            df[col] = df[col].replace(0.0, np.nan)

        # --- Ordenação temporal obrigatória antes de interpolar ---
        df.sort_values("periodo", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # --- Cópia RAW (sem interpolação) para KPIs e tabelas ---
        df_raw = df.copy()

        # --- Passo 2: interpolação linear apenas para lacunas INTERNAS ---
        # limit_area="inside" garante que NaNs nas pontas (informalidade 2012-2015)
        # NÃO são preenchidos — apenas lacunas entre dados válidos.
        for col in ["total", "homens", "mulheres"]:
            df[f"{col}_interp"] = (
                df[col]
                .interpolate(method="linear", limit_area="inside")
            )

        # --- Passo 3: marcar quais linhas foram estimadas por interpolação ---
        df["interpolado"] = (
            df["total"].isna() & df["total_interp"].notna()
        )

        # Usar coluna interpolada como coluna principal nos gráficos
        # (mantendo _raw para KPIs)
        for col in ["total", "homens", "mulheres"]:
            df[col] = df[f"{col}_interp"]
            df.drop(columns=[f"{col}_interp"], inplace=True)

        resultados[nome] = (df, df_raw)

    return (
        resultados["desocupacao"][0], resultados["desocupacao"][1],
        resultados["emprego"][0],     resultados["emprego"][1],
        resultados["informalidade"][0], resultados["informalidade"][1],
    )


desocp, desocp_raw, emprego, emprego_raw, inform, inform_raw = carregar_dados()


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def anos_disponiveis(df_raw):
    """Anos com ao menos um trimestre real (não interpolado)."""
    return sorted(df_raw.dropna(subset=["total"])["ano"].unique().tolist())

def filtrar(df, ano_ini, ano_fim):
    return df[(df["ano"] >= ano_ini) & (df["ano"] <= ano_fim)].copy()

def media_anual(df, cols):
    return df.groupby("ano")[list(cols)].mean().reset_index()

def ultimo_valor_real(df_raw, col="total"):
    """Último valor REAL (não interpolado) de uma coluna."""
    s = df_raw.dropna(subset=[col])
    if s.empty:
        return None, None
    r = s.iloc[-1]
    return r[col], r["label_trim"]

def variacao_pp(df_raw, col="total", n=4):
    s = df_raw.dropna(subset=[col])
    if len(s) < n + 1:
        return None
    return round(s.iloc[-1][col] - s.iloc[-1 - n][col], 1)

def delta_html(val, inverso=False):
    if val is None:
        return ""
    sinal = "▲" if val > 0 else "▼"
    classe = "kpi-delta-down" if (val > 0) == inverso else "kpi-delta-up"
    return f'<div class="{classe}">{sinal} {abs(val):.1f} pp vs. ano anterior</div>'

def nota_interpolacao(df_filtrado):
    """Retorna aviso se o período filtrado contém dados interpolados."""
    n = df_filtrado["interpolado"].sum() if "interpolado" in df_filtrado.columns else 0
    if n > 0:
        return (f"<div class='warn-box'>⚠️ <b>{n} trimestre(s) interpolado(s)</b> no período "
                "selecionado (lacuna 2020-T2 a 2022-T1). Pontos estimados por interpolação "
                "linear — indicados com linha tracejada nos gráficos.</div>")
    return ""

# Paleta
COR_TOTAL    = "#1F4E79"
COR_HOMENS   = "#2196F3"
COR_MULHERES = "#E91E63"
COR_ALERTA   = "#E74C3C"
COR_OK       = "#27AE60"
COR_NEUTRO   = "#95A5A6"
COR_INTERP   = "#8E44AD"   # cor especial para segmentos interpolados
TEMPLATE     = "plotly_white"

col_map = {
    "Total":    ("total",    COR_TOTAL),
    "Homens":   ("homens",   COR_HOMENS),
    "Mulheres": ("mulheres", COR_MULHERES),
}

# =============================================================================
# CATÁLOGO DE PÁGINAS/GRÁFICOS (usado pela busca e navegação)
# =============================================================================

PAGINAS = [
    {
        "id": "visao_geral",
        "emoji": "🏠",
        "titulo": "Visão Geral",
        "descricao": "KPIs, introdução e resumo do período",
        "tags": ["kpi", "resumo", "introdução", "visão geral", "início", "indicadores",
                 "desocupação", "emprego", "informalidade", "situação atual"],
    },
    {
        "id": "desocupacao_historica",
        "emoji": "📈",
        "titulo": "Desocupação — Evolução Histórica",
        "descricao": "Linha temporal com as 3 fases: expansão, crise e recuperação",
        "tags": ["desocupação", "desemprego", "histórico", "fases", "crise", "expansão",
                 "recuperação", "linha", "temporal", "pico", "mínimo", "2017"],
    },
    {
        "id": "desocupacao_anual",
        "emoji": "📊",
        "titulo": "Desocupação — Média Anual",
        "descricao": "Barras por ano com código de cor por gravidade",
        "tags": ["desocupação", "anual", "barras", "média", "ano a ano", "gravidade"],
    },
    {
        "id": "genero_desocupacao",
        "emoji": "⚖️",
        "titulo": "Gênero — Desocupação por Sexo",
        "descricao": "Comparação homens vs mulheres na desocupação trimestral e anual",
        "tags": ["gênero", "sexo", "homens", "mulheres", "gap", "desigualdade",
                 "desocupação", "comparação", "diferença"],
    },
    {
        "id": "genero_emprego",
        "emoji": "💼",
        "titulo": "Gênero — Emprego por Sexo",
        "descricao": "Gap estrutural de ~24 pp entre homens e mulheres na taxa de emprego",
        "tags": ["gênero", "sexo", "homens", "mulheres", "emprego", "gap", "24pp",
                 "desigualdade", "estrutural", "trabalho"],
    },
    {
        "id": "informalidade",
        "emoji": "🔧",
        "titulo": "Informalidade",
        "descricao": "Taxa de informalidade por sexo (série a partir de 2015)",
        "tags": ["informalidade", "informal", "carteira", "fgts", "sem carteira",
                 "qualidade", "emprego informal", "2015"],
    },
    {
        "id": "comparacao",
        "emoji": "🔍",
        "titulo": "Desocupação vs. Informalidade",
        "descricao": "Painel comparativo e gráfico de dispersão por ano",
        "tags": ["comparação", "dispersão", "correlação", "desocupação", "informalidade",
                 "scatter", "bolhas", "relação", "painel"],
    },
    {
        "id": "conclusoes",
        "emoji": "✅",
        "titulo": "Conclusões",
        "descricao": "Síntese narrativa dos três principais achados",
        "tags": ["conclusão", "síntese", "achados", "resultado", "final", "resumo",
                 "estrutural", "recuperação", "desigualdade"],
    },
]

# =============================================================================
# SIDEBAR — NAVEGAÇÃO + BUSCA + FILTROS
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:0.5rem 0 1rem;'>
        <span style='font-size:2rem;'>📊</span><br>
        <span style='font-size:0.85rem; color:#1F4E79; font-weight:700;'>
        Mercado de Trabalho BR</span><br>
        <span style='font-size:0.72rem; color:#888;'>2012–2025 · PNAD/IBGE</span>
    </div>
    """, unsafe_allow_html=True)

    # ── BARRA DE BUSCA ──────────────────────────────────────────────────────
    st.markdown("#### 🔎 Busca rápida")
    busca = st.text_input(
        label="busca_input",
        placeholder="Ex: desemprego, gênero, informalidade...",
        label_visibility="collapsed",
        help="Digite palavras-chave para encontrar gráficos e análises.",
        key="busca_global",
    )

    # Lógica de busca: filtra páginas cujas tags contêm o termo buscado
    resultados_busca = []
    if busca.strip():
        termo = busca.strip().lower()
        for pg in PAGINAS:
            score = sum(1 for tag in pg["tags"] if termo in tag)
            if score:
                resultados_busca.append((score, pg))
        resultados_busca.sort(key=lambda x: -x[0])

    # Exibir resultados da busca como links clicáveis
    if busca.strip() and resultados_busca:
        st.markdown(f"**{len(resultados_busca)} resultado(s) para:** *{busca}*")
        for _, pg in resultados_busca:
            if st.button(
                f"{pg['emoji']} {pg['titulo']}",
                key=f"busca_btn_{pg['id']}",
                help=pg["descricao"],
                use_container_width=True,
            ):
                st.session_state["pagina_ativa"] = pg["id"]
                st.rerun()
        st.markdown("---")
    elif busca.strip() and not resultados_busca:
        st.warning("Nenhum resultado encontrado.")
        st.markdown("---")

    # ── NAVEGAÇÃO POR PÁGINAS ───────────────────────────────────────────────
    st.markdown("#### 🗂️ Navegação")

    # Inicializar página padrão
    if "pagina_ativa" not in st.session_state:
        st.session_state["pagina_ativa"] = "visao_geral"

    # Ler a página ATUAL já com o estado atualizado pelo rerun anterior
    pagina_atual = st.session_state["pagina_ativa"]

    for pg in PAGINAS:
        ativo = pagina_atual == pg["id"]
        if st.button(
            f"{pg['emoji']} {pg['titulo']}",
            key=f"nav_{pg['id']}",
            help=pg["descricao"],
            use_container_width=True,
            type="primary" if ativo else "secondary",
        ):
            # Só faz rerun se mudou de página (evita re-render desnecessário)
            if st.session_state["pagina_ativa"] != pg["id"]:
                st.session_state["pagina_ativa"] = pg["id"]
                st.rerun()

    st.markdown("---")

    # ── FILTROS GLOBAIS ─────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Filtros")

    todos_anos = sorted(set(
        anos_disponiveis(desocp_raw) +
        anos_disponiveis(emprego_raw) +
        anos_disponiveis(inform_raw)
    ))
    ano_min, ano_max = min(todos_anos), max(todos_anos)

    ano_inicio, ano_fim = st.select_slider(
        "Período",
        options=todos_anos,
        value=(ano_min, ano_max),
        help="Filtra todos os gráficos.",
    )

    generos = st.multiselect(
        "Recorte por sexo",
        options=["Total", "Homens", "Mulheres"],
        default=["Total", "Homens", "Mulheres"],
    )
    if not generos:
        generos = ["Total"]

    eixo_x_scatter = st.selectbox(
        "Dispersão — Eixo X",
        ["Desocupação", "Emprego"],
        help="Variável do eixo X no gráfico de correlação.",
    )

    st.markdown("---")
    st.caption("Fonte: PNAD Contínua — IBGE\n⚠️ Lacuna: 2020-T2 a 2022-T1")


# =============================================================================
# DADOS FILTRADOS (usados por todas as páginas)
# =============================================================================

d      = filtrar(desocp,      ano_inicio, ano_fim)
d_raw  = filtrar(desocp_raw,  ano_inicio, ano_fim)
e      = filtrar(emprego,     ano_inicio, ano_fim)
e_raw  = filtrar(emprego_raw, ano_inicio, ano_fim)
i      = filtrar(inform,      ano_inicio, ano_fim)
i_raw  = filtrar(inform_raw,  ano_inicio, ano_fim)

pagina = st.session_state.get("pagina_ativa", "visao_geral")


# =============================================================================
# HELPER: traçar linha com segmento interpolado destacado
# =============================================================================

def adicionar_linha_com_interp(fig, df, col, cor, nome, dash="solid", customdata_col="trimestre"):
    """
    Adiciona uma trace de linha normal + uma trace pontilhada roxa
    sobre os segmentos que foram interpolados.
    Isso torna transparente ao usuário quais pontos são estimados.
    """
    df_ok    = df[~df["interpolado"]].dropna(subset=[col]) if "interpolado" in df.columns else df.dropna(subset=[col])
    df_interp = df[df["interpolado"]].dropna(subset=[col])  if "interpolado" in df.columns else df.iloc[0:0]

    # Linha principal (dados reais)
    fig.add_trace(go.Scatter(
        x=df_ok["periodo"],
        y=df_ok[col],
        mode="lines+markers",
        name=nome,
        line=dict(color=cor, width=2.5, dash=dash),
        marker=dict(size=4),
        hovertemplate=f"<b>{nome}</b> %{{x|%Y T%{{customdata}}}}: <b>%{{y:.1f}}%</b><extra></extra>",
        customdata=df_ok[customdata_col],
        legendgroup=nome,
    ))

    # Segmento interpolado (pontilhado roxo)
    if not df_interp.empty:
        # Pegar o ponto anterior e posterior para conectar visualmente
        idx_interp = df[df["interpolado"]].index
        idx_vizinhos = sorted(set(
            [max(0, idx_interp.min() - 1)] +
            list(idx_interp) +
            [min(len(df) - 1, idx_interp.max() + 1)]
        ))
        df_seg = df.iloc[idx_vizinhos].dropna(subset=[col])

        fig.add_trace(go.Scatter(
            x=df_seg["periodo"],
            y=df_seg[col],
            mode="lines",
            name=f"{nome} (estimado)",
            line=dict(color=COR_INTERP, width=1.8, dash="dot"),
            hovertemplate=f"<b>{nome} ⚠️ estimado</b> %{{x|%Y}}: <b>%{{y:.1f}}%</b><extra></extra>",
            legendgroup=nome,
            showlegend=True,
        ))


# =============================================================================
# ██████████████████████  PÁGINAS  ██████████████████████
# =============================================================================


# ─────────────────────────────────────────────────────────────
# PÁGINA 1 — VISÃO GERAL / KPIs
# ─────────────────────────────────────────────────────────────
if pagina == "visao_geral":

    st.markdown("""
    <div class="intro-box">
        <h2 style="color:white; margin:0 0 0.5rem 0; font-size:1.6rem;">
            📊 Mercado de Trabalho Brasileiro — 2012 a 2025
        </h2>
        <p>Uma análise da evolução da <b>desocupação</b>, <b>emprego</b> e <b>informalidade</b>
        no Brasil em três fases: expansão (2012–2014), crise (2015–2020) e recuperação (2022–2025).</p>
        <p>Use a <b>navegação à esquerda</b> ou a <b>barra de busca</b> para acessar cada análise.</p>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    st.markdown("## 📌 Situação atual do mercado de trabalho")
    st.markdown("<div class='story-box'>Indicadores do <b>último trimestre real</b> no período "
                "filtrado (interpolações excluídas dos KPIs).</div>", unsafe_allow_html=True)

    kpi_dt, kpi_dl = ultimo_valor_real(d_raw, "total")
    kpi_dh, _      = ultimo_valor_real(d_raw, "homens")
    kpi_dm, _      = ultimo_valor_real(d_raw, "mulheres")
    kpi_e,  kpi_el = ultimo_valor_real(e_raw, "total")
    kpi_i,  kpi_il = ultimo_valor_real(i_raw, "total")

    var_d = variacao_pp(d_raw, "total")
    var_e = variacao_pp(e_raw, "total")
    var_i = variacao_pp(i_raw, "total")

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "Desocupação Total",   f"{kpi_dt:.1f}%", "#E74C3C", "#2E75B6",  delta_html(var_d, inverso=True),  kpi_dl),
        (c2, "Desocupação Homens",  f"{kpi_dh:.1f}%", COR_HOMENS, COR_HOMENS, "",                               kpi_dl),
        (c3, "Desocupação Mulheres",f"{kpi_dm:.1f}%", COR_MULHERES, COR_MULHERES, "",                           kpi_dl),
        (c4, "Taxa de Emprego",     f"{kpi_e:.1f}%",  COR_OK,   COR_OK,     delta_html(var_e, inverso=False),  kpi_el),
        (c5, "Informalidade",       f"{kpi_i:.1f}%",  "#F39C12", "#F39C12",  delta_html(var_i, inverso=True),   kpi_il),
    ]
    for col_obj, label, val, cor_val, cor_borda, delta, sub in cards:
        with col_obj:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{cor_borda};">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{cor_val};">{val}</div>
                {delta}
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Mapa rápido de páginas
    st.markdown("## 🗺️ O que você encontra neste dashboard")
    cols = st.columns(4)
    for idx, pg in enumerate(PAGINAS[1:]):   # pula visão_geral
        with cols[idx % 4]:
            st.markdown(f"""
            <div style='background:white; border-radius:8px; padding:0.8rem;
                        box-shadow:0 2px 6px rgba(0,0,0,0.06); margin-bottom:0.6rem;
                        border-top: 3px solid #2E75B6;'>
                <div style='font-size:1.4rem;'>{pg['emoji']}</div>
                <div style='font-size:0.85rem; font-weight:700; color:#1F4E79;
                            margin:0.3rem 0 0.2rem;'>{pg['titulo']}</div>
                <div style='font-size:0.75rem; color:#666;'>{pg['descricao']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("📋 Fonte: PNAD Contínua — IBGE · Trimestral · 2012–2025 · "
               "Lacuna 2020-T2→2022-T1 preenchida por interpolação linear.")


# ─────────────────────────────────────────────────────────────
# PÁGINA 2 — DESOCUPAÇÃO HISTÓRICA
# ─────────────────────────────────────────────────────────────
elif pagina == "desocupacao_historica":

    st.markdown("## 📈 Desocupação — Evolução Histórica (2012–2025)")
    st.markdown(nota_interpolacao(d), unsafe_allow_html=True)
    st.markdown(
        "<div class='story-box'>Três fases distintas marcam o mercado de trabalho brasileiro. "
        "As <b>faixas coloridas</b> demarcam cada período. Pontos <b>roxos pontilhados</b> "
        "indicam trimestres estimados por interpolação linear.</div>",
        unsafe_allow_html=True,
    )

    d_valido = d.dropna(subset=["total"])

    fig = go.Figure()

    # Faixas de fase
    fases = [
        (2012, 2014, "rgba(39,174,96,0.07)",  "🟢 Expansão"),
        (2015, 2020, "rgba(231,76,60,0.07)",  "🔴 Crise"),
        (2022, 2025, "rgba(52,152,219,0.07)", "🔵 Recuperação"),
    ]
    for fa_ini, fa_fim, cor_f, _ in fases:
        fig.add_vrect(x0=f"{fa_ini}-01-01", x1=f"{fa_fim}-12-31",
                      fillcolor=cor_f, layer="below", line_width=0)

    # Linha com segmento interpolado
    adicionar_linha_com_interp(fig, d, "total", COR_TOTAL, "Desocupação total")

    # Anotações pico e mínimo (sobre dados reais)
    if not d_raw.dropna(subset=["total"]).empty:
        dr = d_raw.dropna(subset=["total"])
        pico = dr.loc[dr["total"].idxmax()]
        mini = dr.loc[dr["total"].idxmin()]
        fig.add_annotation(x=pico["periodo"], y=pico["total"],
            text=f"<b>Pico: {pico['total']:.1f}%<br>({pico['label_trim']})</b>",
            showarrow=True, arrowhead=2, arrowcolor=COR_ALERTA,
            font=dict(color=COR_ALERTA, size=11), bgcolor="white",
            bordercolor=COR_ALERTA, borderwidth=1, ax=40, ay=-45)
        fig.add_annotation(x=mini["periodo"], y=mini["total"],
            text=f"<b>Mín: {mini['total']:.1f}%<br>({mini['label_trim']})</b>",
            showarrow=True, arrowhead=2, arrowcolor=COR_OK,
            font=dict(color=COR_OK, size=11), bgcolor="white",
            bordercolor=COR_OK, borderwidth=1, ax=-50, ay=40)

    # Rótulos de fase
    for fa_ini, fa_fim, _, rotulo in fases:
        fig.add_annotation(x=f"{(fa_ini+fa_fim)//2}-06-01",
            y=d_valido["total"].max() * 1.02 if not d_valido.empty else 20,
            text=rotulo, showarrow=False, font=dict(size=10, color="#555"))

    fig.update_layout(
        title=dict(text="Taxa de Desocupação Total — Trimestral (%)", font=dict(size=16, color=COR_TOTAL)),
        xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
        yaxis=dict(title="Desocupação (%)"),
        template=TEMPLATE, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=460, margin=dict(t=60, b=40, l=60, r=30),
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.caption("⚠️ Segmento roxo pontilhado = interpolação linear da lacuna 2020-T2→2022-T1. "
               "Dados reais ausentes nesse intervalo.")


# ─────────────────────────────────────────────────────────────
# PÁGINA 3 — DESOCUPAÇÃO ANUAL
# ─────────────────────────────────────────────────────────────
elif pagina == "desocupacao_anual":

    st.markdown("## 📊 Desocupação — Média Anual por Gravidade")
    st.markdown(
        "<div class='story-box'>Médias calculadas <b>apenas sobre trimestres reais</b> "
        "(interpolações excluídas). Código de cor: "
        "<b style='color:#27AE60'>verde &lt; 9%</b> · "
        "<b style='color:#95A5A6'>cinza 9–12%</b> · "
        "<b style='color:#E67E22'>laranja 12–15%</b> · "
        "<b style='color:#E74C3C'>vermelho ≥ 15%</b></div>",
        unsafe_allow_html=True,
    )

    # Usar apenas dados reais para médias anuais
    ma = media_anual(d_raw.dropna(subset=["total"]), ["total"])

    def cor_barra(v):
        if v >= 15:  return COR_ALERTA
        if v >= 12:  return "#E67E22"
        if v < 9:    return COR_OK
        return COR_NEUTRO

    cores = [cor_barra(v) for v in ma["total"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ma["ano"].astype(str),
        y=ma["total"].round(1),
        marker_color=cores,
        text=ma["total"].round(1).astype(str) + "%",
        textposition="outside",
        hovertemplate="<b>%{x}</b> — Desocupação média: <b>%{y:.1f}%</b><extra></extra>",
    ))
    media_geral = ma["total"].mean()
    fig.add_hline(y=media_geral, line_dash="dot", line_color="#888",
                  annotation_text=f"Média geral: {media_geral:.1f}%",
                  annotation_position="bottom right", annotation_font_color="#888")

    fig.update_layout(
        title=dict(text="Desocupação Média Anual (%) — somente dados reais", font=dict(size=16, color=COR_TOTAL)),
        xaxis=dict(title="Ano"),
        yaxis=dict(title="Desocupação média (%)", range=[0, ma["total"].max() * 1.18]),
        template=TEMPLATE, showlegend=False,
        height=420, margin=dict(t=60, b=40, l=60, r=30),
    )
    st.plotly_chart(fig, width="stretch")

    # Tabela de dados
    with st.expander("📋 Ver tabela de dados"):
        st.dataframe(
            ma.rename(columns={"ano": "Ano", "total": "Desocupação média (%)"})
              .assign(**{"Desocupação média (%)": lambda df: df["Desocupação média (%)"].round(2)})
              .set_index("Ano"),
            use_container_width=True,
        )


# ─────────────────────────────────────────────────────────────
# PÁGINA 4 — GÊNERO: DESOCUPAÇÃO
# ─────────────────────────────────────────────────────────────
elif pagina == "genero_desocupacao":

    st.markdown("## ⚖️ Gênero — Desocupação por Sexo")
    st.markdown(nota_interpolacao(d), unsafe_allow_html=True)
    st.markdown(
        "<div class='alert-box'>Mulheres registram desocupação <b>consistentemente acima</b> "
        "dos homens ao longo de toda a série. O gap médio foi de <b>~3,2 pontos percentuais</b> "
        "e não mostrou convergência significativa nem mesmo durante a recuperação.</div>",
        unsafe_allow_html=True,
    )

    # Gráfico de linhas por sexo
    fig3 = go.Figure()
    for gen in generos:
        col_nome, cor = col_map[gen]
        adicionar_linha_com_interp(
            fig3, d, col_nome, cor, gen,
            dash="dot" if gen == "Total" else "solid",
        )

    # Área de gap H/M (usando dados reais)
    if "Homens" in generos and "Mulheres" in generos:
        d_hm = d.dropna(subset=["homens", "mulheres"])
        if not d_hm.empty:
            fig3.add_trace(go.Scatter(
                x=pd.concat([d_hm["periodo"], d_hm["periodo"][::-1]]),
                y=pd.concat([d_hm["mulheres"], d_hm["homens"][::-1]]),
                fill="toself", fillcolor="rgba(233,30,99,0.07)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Gap H/M", showlegend=True, hoverinfo="skip",
            ))

    fig3.update_layout(
        title=dict(text="Taxa de Desocupação por Sexo — Trimestral (%)", font=dict(size=16, color=COR_TOTAL)),
        xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
        yaxis=dict(title="Desocupação (%)"),
        template=TEMPLATE, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420, margin=dict(t=60, b=40, l=60, r=30),
    )
    st.plotly_chart(fig3, width="stretch")

    # Barras agrupadas anuais
    st.markdown("### Gap de gênero — média anual")
    st.markdown("<div class='story-box'>Apenas anos com dados reais são exibidos. "
                "Barras calculadas excluindo trimestres interpolados.</div>", unsafe_allow_html=True)

    ma_gen = media_anual(d_raw.dropna(subset=["homens", "mulheres"]), ["homens", "mulheres"])
    fig4 = go.Figure()
    if "Homens" in generos:
        fig4.add_trace(go.Bar(x=ma_gen["ano"].astype(str), y=ma_gen["homens"].round(1),
            name="Homens", marker_color=COR_HOMENS,
            hovertemplate="<b>Homens %{x}</b>: %{y:.1f}%<extra></extra>"))
    if "Mulheres" in generos:
        fig4.add_trace(go.Bar(x=ma_gen["ano"].astype(str), y=ma_gen["mulheres"].round(1),
            name="Mulheres", marker_color=COR_MULHERES,
            hovertemplate="<b>Mulheres %{x}</b>: %{y:.1f}%<extra></extra>"))

    fig4.update_layout(
        barmode="group",
        title=dict(text="Desocupação Média Anual por Sexo (%)", font=dict(size=14, color=COR_TOTAL)),
        xaxis=dict(title="Ano"), yaxis=dict(title="Desocupação média (%)"),
        template=TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380, margin=dict(t=55, b=40, l=60, r=30),
    )
    st.plotly_chart(fig4, width="stretch")

    # Gap médio no período filtrado
    if not ma_gen.empty:
        gap_medio = (ma_gen["mulheres"] - ma_gen["homens"]).mean()
        st.markdown(f"<div class='story-box'>📐 <b>Gap médio no período selecionado: "
                    f"{gap_medio:.1f} pp</b> (mulheres acima dos homens).</div>",
                    unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PÁGINA 5 — GÊNERO: EMPREGO
# ─────────────────────────────────────────────────────────────
elif pagina == "genero_emprego":

    st.markdown("## 💼 Gênero — Taxa de Emprego por Sexo")
    st.markdown(nota_interpolacao(e), unsafe_allow_html=True)
    st.markdown(
        "<div class='alert-box'><b>~24 pontos percentuais</b> separam homens e mulheres "
        "na taxa de emprego ao longo de toda a série. Essa assimetria estrutural persiste "
        "independentemente do ciclo econômico — expansão ou crise.</div>",
        unsafe_allow_html=True,
    )

    fig5 = go.Figure()
    for gen in generos:
        col_nome, cor = col_map[gen]
        adicionar_linha_com_interp(
            fig5, e, col_nome, cor, gen,
            dash="dot" if gen == "Total" else "solid",
            customdata_col="trimestre",
        )

    # Gap
    if "Homens" in generos and "Mulheres" in generos:
        e_hm = e.dropna(subset=["homens", "mulheres"])
        if not e_hm.empty:
            fig5.add_trace(go.Scatter(
                x=pd.concat([e_hm["periodo"], e_hm["periodo"][::-1]]),
                y=pd.concat([e_hm["homens"], e_hm["mulheres"][::-1]]),
                fill="toself", fillcolor="rgba(52,152,219,0.07)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Gap H/M", showlegend=True, hoverinfo="skip",
            ))

    fig5.update_layout(
        title=dict(text="Taxa de Emprego por Sexo — Trimestral (%)", font=dict(size=16, color=COR_TOTAL)),
        xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
        yaxis=dict(title="Taxa de emprego (%)"),
        template=TEMPLATE, hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=440, margin=dict(t=60, b=40, l=60, r=30),
    )
    st.plotly_chart(fig5, width="stretch")

    # Estatística de gap
    e_hm_raw = e_raw.dropna(subset=["homens", "mulheres"])
    if not e_hm_raw.empty:
        gap_emp = (e_hm_raw["homens"] - e_hm_raw["mulheres"]).mean()
        st.markdown(f"<div class='story-box'>📐 <b>Gap médio de emprego no período: "
                    f"{gap_emp:.1f} pp</b> (homens acima das mulheres).</div>",
                    unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PÁGINA 6 — INFORMALIDADE
# ─────────────────────────────────────────────────────────────
elif pagina == "informalidade":

    st.markdown("## 🔧 Informalidade — A Crise Silenciosa")
    st.markdown(nota_interpolacao(i), unsafe_allow_html=True)
    st.markdown(
        "<div class='story-box'>Enquanto a desocupação caiu, a informalidade permaneceu "
        "cronicamente elevada. Em 2025, <b>quase 1 em cada 2 trabalhadores ocupados</b> "
        "está sem carteira assinada, FGTS, 13º ou seguro-desemprego. "
        "<br><b>Série disponível a partir de 2015-T3.</b></div>",
        unsafe_allow_html=True,
    )

    i_valido = i.dropna(subset=["total"])

    if i_valido.empty:
        st.warning("Nenhum dado de informalidade no período selecionado. "
                   "A série começa em 2015-T3 — ajuste o filtro de período.")
    else:
        fig6 = go.Figure()

        # Área de fundo
        fig6.add_trace(go.Scatter(
            x=i_valido["periodo"], y=i_valido["total"],
            mode="lines", name="Total (área)",
            line=dict(color="rgba(243,156,18,0.4)", width=0),
            fill="tozeroy", fillcolor="rgba(243,156,18,0.10)",
            showlegend=False, hoverinfo="skip",
        ))

        # Linhas por sexo com segmento interpolado
        for gen in generos:
            col_nome, cor = col_map[gen]
            adicionar_linha_com_interp(fig6, i, col_nome, cor, gen,
                dash="dot" if gen == "Total" else "solid")

        # Pico sobre dados reais
        i_real = i_raw.dropna(subset=["total"])
        if not i_real.empty:
            pico_i = i_real.loc[i_real["total"].idxmax()]
            fig6.add_annotation(x=pico_i["periodo"], y=pico_i["total"],
                text=f"<b>Pico: {pico_i['total']:.1f}%<br>({pico_i['label_trim']})</b>",
                showarrow=True, arrowhead=2, arrowcolor=COR_ALERTA,
                font=dict(color=COR_ALERTA, size=11), bgcolor="white",
                bordercolor=COR_ALERTA, borderwidth=1, ax=50, ay=-35)

        fig6.update_layout(
            title=dict(text="Taxa de Informalidade por Sexo — Trimestral (%) · Série a partir de 2015-T3",
                       font=dict(size=16, color=COR_TOTAL)),
            xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
            yaxis=dict(title="Informalidade (%)",
                       range=[i_valido["total"].min() * 0.95, i_valido["total"].max() * 1.08]),
            template=TEMPLATE, hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=440, margin=dict(t=60, b=40, l=60, r=30),
        )
        st.plotly_chart(fig6, width="stretch")

        # Tabela anual
        with st.expander("📋 Ver médias anuais de informalidade"):
            ma_i = media_anual(i_raw.dropna(subset=["total"]), ["total", "homens", "mulheres"])
            st.dataframe(
                ma_i.rename(columns={"ano": "Ano", "total": "Total (%)",
                                     "homens": "Homens (%)", "mulheres": "Mulheres (%)"})
                    .assign(**{c: ma_i[k].round(1) for c, k in
                               [("Total (%)", "total"), ("Homens (%)", "homens"), ("Mulheres (%)", "mulheres")]})
                    .set_index("Ano"),
                use_container_width=True,
            )


# ─────────────────────────────────────────────────────────────
# PÁGINA 7 — COMPARAÇÃO: DESOCUPAÇÃO vs INFORMALIDADE
# ─────────────────────────────────────────────────────────────
elif pagina == "comparacao":

    st.markdown("## 🔍 Desocupação vs. Informalidade — Comparação")
    st.markdown(
        "<div class='story-box'>O painel duplo e a dispersão revelam que a queda do "
        "desemprego <b>não se traduz automaticamente</b> em melhora da qualidade do emprego. "
        "A informalidade permanece elevada mesmo quando o desemprego cai.</div>",
        unsafe_allow_html=True,
    )

    # Painel duplo
    df_comp = pd.merge(
        d_raw[["periodo", "ano", "label_trim", "total"]].rename(columns={"total": "desocupacao"}),
        i_raw[["periodo", "total"]].rename(columns={"total": "informalidade"}),
        on="periodo", how="inner",
    ).dropna()

    if df_comp.empty:
        st.warning("Sem dados sobrepostos entre as duas séries no período selecionado.")
    else:
        fig7 = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            subplot_titles=("Desocupação Total (%)", "Informalidade Total (%)"),
            vertical_spacing=0.1,
        )
        fig7.add_trace(go.Scatter(
            x=df_comp["periodo"], y=df_comp["desocupacao"],
            name="Desocupação", line=dict(color=COR_TOTAL, width=2.5), mode="lines",
            hovertemplate="<b>Desocupação</b> %{x|%Y}: %{y:.1f}%<extra></extra>",
        ), row=1, col=1)
        fig7.add_trace(go.Scatter(
            x=df_comp["periodo"], y=df_comp["informalidade"],
            name="Informalidade", line=dict(color="#F39C12", width=2.5),
            fill="tozeroy", fillcolor="rgba(243,156,18,0.1)", mode="lines",
            hovertemplate="<b>Informalidade</b> %{x|%Y}: %{y:.1f}%<extra></extra>",
        ), row=2, col=1)

        fig7.update_yaxes(title_text="Desocupação (%)", row=1, col=1)
        fig7.update_yaxes(title_text="Informalidade (%)", row=2, col=1)
        fig7.update_xaxes(showgrid=False, tickformat="%Y", row=2, col=1)
        fig7.update_layout(
            title=dict(text="Desocupação vs. Informalidade — Painel Comparativo (dados reais)",
                       font=dict(size=14, color=COR_TOTAL)),
            template=TEMPLATE, hovermode="x unified",
            height=520, margin=dict(t=60, b=40, l=60, r=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig7, width="stretch")

    st.markdown("---")

    # Dispersão
    st.markdown("### Dispersão por ano")
    st.markdown(
        f"<div class='story-box'>Cada bolha = um ano. Eixo X: "
        f"<b>{eixo_x_scatter.lower()}</b>. Eixo Y: <b>informalidade</b>. "
        "Tamanho = variação absoluta da desocupação. Cor = nível de desocupação.</div>",
        unsafe_allow_html=True,
    )

    ma_d_s = media_anual(d_raw.dropna(subset=["total"]), ["total"]).rename(columns={"total": "desocp"})
    ma_e_s = media_anual(e_raw.dropna(subset=["total"]), ["total"]).rename(columns={"total": "emp"})
    ma_i_s = media_anual(i_raw.dropna(subset=["total"]), ["total"]).rename(columns={"total": "inform"})
    df_sc  = ma_d_s.merge(ma_e_s, on="ano").merge(ma_i_s, on="ano").dropna()

    if df_sc.empty:
        st.info("Dados insuficientes para o gráfico de dispersão no período selecionado.")
    else:
        df_sc["var_d"] = df_sc["desocp"].diff().abs().fillna(1)
        eixo_x_col    = "desocp" if eixo_x_scatter == "Desocupação" else "emp"
        eixo_x_titulo = ("Desocupação média anual (%)"
                         if eixo_x_scatter == "Desocupação" else "Taxa de emprego média (%)")

        fig8 = go.Figure()
        fig8.add_trace(go.Scatter(
            x=df_sc[eixo_x_col], y=df_sc["inform"],
            mode="markers+text",
            text=df_sc["ano"].astype(str),
            textposition="top center",
            textfont=dict(size=10, color="#555"),
            marker=dict(
                size=df_sc["var_d"] * 10 + 14,
                color=df_sc["desocp"],
                colorscale=[[0, COR_OK], [0.5, "#E67E22"], [1, COR_ALERTA]],
                showscale=True,
                colorbar=dict(title="Desocupação (%)"),
                opacity=0.85,
                line=dict(color="white", width=1),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"{eixo_x_titulo.split(' (')[0]}: <b>%{{x:.1f}}%</b><br>"
                "Informalidade: <b>%{y:.1f}%</b><extra></extra>"
            ),
        ))
        fig8.update_layout(
            title=dict(text=f"Dispersão: {eixo_x_titulo.split(' (')[0]} × Informalidade (médias anuais — dados reais)",
                       font=dict(size=14, color=COR_TOTAL)),
            xaxis=dict(title=eixo_x_titulo),
            yaxis=dict(title="Informalidade média anual (%)"),
            template=TEMPLATE, height=440,
            margin=dict(t=55, b=40, l=60, r=30),
        )
        st.plotly_chart(fig8, width="stretch")


# ─────────────────────────────────────────────────────────────
# PÁGINA 8 — CONCLUSÕES
# ─────────────────────────────────────────────────────────────
elif pagina == "conclusoes":

    st.markdown("## ✅ Conclusões — O que os dados nos dizem")
    st.markdown(
        "<div class='story-box'>Síntese dos três achados centrais da análise, "
        "com base nos dados trimestrais da PNAD Contínua (2012–2025).</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="conclusion-box">
            <b>🔄 Recuperação real, mas frágil</b><br><br>
            A desocupação recuou de <b>19,0%</b> (pico de 2017-T2) para <b>8,8%</b>
            (T4/2025), próxima ao mínimo pré-crise de 7,4% (2013). A recuperação é
            expressiva — mas ainda não está consolidada estruturalmente.
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="alert-box">
            <b>⚠️ Desigualdade de gênero persistente</b><br><br>
            O diferencial de desocupação entre mulheres e homens manteve-se em
            <b>~3,2 pp</b> ao longo de toda a série. A recuperação <i>acompanhou</i>
            o gap — mas não o reduziu. A taxa de emprego feminina ficou ~24 pp
            abaixo da masculina durante todo o período.
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="alert-box">
            <b>🏗️ Informalidade — o maior desafio estrutural</b><br><br>
            Mesmo no mínimo histórico de <b>45,9%</b> (T4/2025), quase metade
            dos ocupados está sem proteção trabalhista plena. A queda do desemprego
            gerou <i>quantidade</i> de empregos — a <i>qualidade</i> segue como
            questão em aberto.
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class='story-box'>
    📌 <b>Leitura final:</b> O mercado de trabalho brasileiro entre 2012 e 2025 percorreu
    uma montanha-russa — queda profunda e recuperação expressiva. Dois problemas estruturais
    resistiram ao ciclo inteiro: <b>(1)</b> a desigualdade de gênero no acesso ao emprego,
    e <b>(2)</b> a informalidade crônica, que limita a proteção social de quase metade da
    força de trabalho. Indicadores de quantidade (desocupação) melhoraram — os de qualidade,
    ainda não o suficiente.
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption(
        "📋 **Nota metodológica** · Fonte: PNAD Contínua — IBGE · "
        "Periodicidade trimestral · Período: 2012–2025 · "
        "Zeros substituídos por NaN · Lacuna 2020-T2→2022-T1 preenchida por "
        "interpolação linear (limit_area='inside') — pontos estimados sinalizados "
        "nos gráficos com linha roxa pontilhada · "
        "KPIs e médias anuais calculados exclusivamente sobre dados reais."
    )