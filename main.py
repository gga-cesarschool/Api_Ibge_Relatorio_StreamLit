# =============================================================================
# DASHBOARD — Mercado de Trabalho Brasileiro (2012–2025)
# Storytelling baseado em: Desocupação | Emprego | Informalidade (PNAD/IBGE)
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

# CSS personalizado para estética limpa e profissional
st.markdown("""
<style>
    /* Tipografia e cores base */
    .main { background-color: #F8F9FA; }
    h1 { color: #1F4E79 !important; font-size: 2rem !important; }
    h2 { color: #2E75B6 !important; font-size: 1.3rem !important; }
    h3 { color: #2E4A7A !important; }

    /* Bloco de introdução */
    .intro-box {
        background: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .intro-box p { color: white !important; margin: 0.3rem 0; font-size: 0.95rem; }

    /* Cards de KPI */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        border-left: 5px solid #2E75B6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        text-align: center;
    }
    .kpi-label { font-size: 0.78rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; color: #1F4E79; line-height: 1.1; }
    .kpi-sub   { font-size: 0.75rem; color: #888; margin-top: 0.25rem; }
    .kpi-delta-up   { font-size: 0.8rem; color: #C0392B; font-weight: 600; }
    .kpi-delta-down { font-size: 0.8rem; color: #1E8449; font-weight: 600; }

    /* Bloco de narrativa entre gráficos */
    .story-box {
        background: #EBF3FB;
        border-left: 4px solid #2E75B6;
        padding: 0.9rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1.2rem 0;
        font-size: 0.92rem;
        color: #2C3E50;
    }
    .story-box b { color: #1F4E79; }

    /* Bloco de alerta / destaque */
    .alert-box {
        background: #FEF9E7;
        border-left: 4px solid #F39C12;
        padding: 0.9rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1.2rem 0;
        font-size: 0.92rem;
        color: #7D6608;
    }

    /* Bloco de conclusão */
    .conclusion-box {
        background: #EAFAF1;
        border-left: 4px solid #1E8449;
        padding: 0.9rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0 1.2rem 0;
        font-size: 0.92rem;
        color: #1E4D2B;
    }

    /* Separador de seções */
    .section-divider {
        border: none;
        border-top: 2px solid #D6EAF8;
        margin: 2rem 0 1.5rem 0;
    }

    /* Oculta menu padrão do Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS
# =============================================================================

@st.cache_data
def carregar_dados():
    """
    Carrega os três arquivos CSV com separadores diferentes.
    Realiza todos os tratamentos necessários:
      - Padronização de separadores (ponto-e-vírgula vs vírgula)
      - Conversão da coluna 'periodo' para datetime
      - Criação de colunas auxiliares: ano, trimestre, label_trim
      - Substituição de zeros por NaN (dados ausentes de 2020-T2 a 2022-T1)
      - Filtragem de registros inválidos para cada série
    """

    # --- Desocupação: separador ponto-e-vírgula ---
    desocp = pd.read_csv(
        "desocupacao.csv",
        sep=";",
        dtype={"total": float, "homens": float, "mulheres": float},
    )

    # --- Emprego: separador vírgula ---
    emprego = pd.read_csv(
        "emprego.csv",
        sep=",",
        dtype={"total": float, "homens": float, "mulheres": float},
    )

    # --- Informalidade: separador ponto-e-vírgula ---
    inform = pd.read_csv(
        "informalidade.csv",
        sep=";",
        dtype={"total": float, "homens": float, "mulheres": float},
    )

    dfs = {"desocupacao": desocp, "emprego": emprego, "informalidade": inform}

    for nome, df in dfs.items():
        # Converter 'periodo' para datetime (formato YYYY-MM-DD)
        df["periodo"] = pd.to_datetime(df["periodo"])

        # Criar coluna de ano
        df["ano"] = df["periodo"].dt.year

        # Criar coluna de trimestre (1 a 4)
        df["trimestre"] = df["periodo"].dt.quarter

        # Criar label legível: "2012 T1", "2012 T2", ...
        df["label_trim"] = df["ano"].astype(str) + " T" + df["trimestre"].astype(str)

        # Substituir zeros por NaN — zeros representam dados ausentes no dataset
        # (lacuna de 2020-T2 a 2022-T1 e, na informalidade, 2012-2015)
        for col in ["total", "homens", "mulheres"]:
            df[col] = df[col].replace(0.0, np.nan)

        # Garantir ordenação cronológica
        df.sort_values("periodo", inplace=True)
        df.reset_index(drop=True, inplace=True)

    # Informalidade: série só tem dados válidos a partir de 2015-T3
    # (zeros anteriores já foram convertidos para NaN acima)

    return dfs["desocupacao"], dfs["emprego"], dfs["informalidade"]


desocp, emprego, inform = carregar_dados()


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def anos_disponiveis(df):
    """Retorna lista de anos com ao menos um valor não-nulo."""
    return sorted(df.dropna(subset=["total"])["ano"].unique().tolist())


def filtrar_por_periodo(df, ano_inicio, ano_fim):
    """Filtra dataframe pelo intervalo de anos selecionado."""
    return df[(df["ano"] >= ano_inicio) & (df["ano"] <= ano_fim)].copy()


def calcular_media_anual(df, cols=("total", "homens", "mulheres")):
    """Calcula média anual ignorando NaNs."""
    return df.groupby("ano")[list(cols)].mean().reset_index()


def ultimo_valor(df, col="total"):
    """Retorna o último valor não-nulo de uma coluna."""
    serie = df.dropna(subset=[col])
    if serie.empty:
        return None, None
    ultima_linha = serie.iloc[-1]
    return ultima_linha[col], ultima_linha["label_trim"]


def variacao_pp(df, col="total", n_periodos=4):
    """Variação em pontos percentuais vs n_periodos atrás (default: 1 ano = 4 trimestres)."""
    serie = df.dropna(subset=[col])
    if len(serie) < n_periodos + 1:
        return None
    atual = serie.iloc[-1][col]
    anterior = serie.iloc[-1 - n_periodos][col]
    return round(atual - anterior, 1)


# Paleta de cores consistente com o relatório
COR_TOTAL    = "#1F4E79"   # azul escuro
COR_HOMENS   = "#2196F3"   # azul médio
COR_MULHERES = "#E91E63"   # rosa
COR_ALERTA   = "#E74C3C"   # vermelho
COR_OK       = "#27AE60"   # verde
COR_NEUTRO   = "#95A5A6"   # cinza
TEMPLATE     = "plotly_white"


# =============================================================================
# SIDEBAR — FILTROS
# =============================================================================

with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/320px-Flag_of_Brazil.svg.png",
        width=90,
    )
    st.markdown("## Filtros")
    st.markdown("---")

    # Intervalo de anos
    todos_anos = sorted(set(
        anos_disponiveis(desocp) +
        anos_disponiveis(emprego) +
        anos_disponiveis(inform)
    ))
    ano_min, ano_max = min(todos_anos), max(todos_anos)

    ano_inicio, ano_fim = st.select_slider(
        "Período de análise",
        options=todos_anos,
        value=(ano_min, ano_max),
        help="Filtra todos os gráficos pelo intervalo de anos selecionado.",
    )

    st.markdown("---")

    # Filtro de recorte de gênero
    generos = st.multiselect(
        "Exibir recorte por sexo",
        options=["Total", "Homens", "Mulheres"],
        default=["Total", "Homens", "Mulheres"],
        help="Selecione quais séries exibir nos gráficos com recorte por sexo.",
    )
    if not generos:
        generos = ["Total"]  # ao menos uma série sempre visível

    st.markdown("---")

    # Filtro de indicador para o gráfico de correlação
    st.markdown("**Dispersão (Ato 5)**")
    eixo_x_scatter = st.selectbox(
        "Eixo X",
        ["Desocupação", "Emprego"],
        index=0,
        help="Variável do eixo horizontal no gráfico de correlação.",
    )

    st.markdown("---")
    st.caption(
        "Fonte: PNAD Contínua — IBGE  \n"
        "Periodicidade: trimestral  \n"
        "Período: 2012–2025  \n"
        "⚠️ Dados ausentes: 2020-T2 a 2022-T1"
    )


# Aplicar filtro de período aos três dataframes
d = filtrar_por_periodo(desocp, ano_inicio, ano_fim)
e = filtrar_por_periodo(emprego, ano_inicio, ano_fim)
i = filtrar_por_periodo(inform, ano_inicio, ano_fim)


# =============================================================================
# ATO 1 — CONTEXTO E INTRODUÇÃO
# =============================================================================

st.markdown("""
<div class="intro-box">
    <h2 style="color:white; margin:0 0 0.5rem 0; font-size:1.6rem;">
        📊 Mercado de Trabalho Brasileiro — 2012 a 2025
    </h2>
    <p>Uma análise da evolução da <b>desocupação</b>, <b>emprego</b> e <b>informalidade</b>
    no Brasil ao longo de três fases distintas: expansão econômica (2012–2014),
    crise profunda (2015–2020) e recuperação gradual (2022–2025).</p>
    <p>Fonte: <b>PNAD Contínua — IBGE</b> · Dados trimestrais · Recorte por sexo disponível.</p>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# ATO 2 — KPIs: SITUAÇÃO MAIS RECENTE
# =============================================================================

st.markdown("## 📌 Situação atual do mercado de trabalho")
st.markdown(
    "<div class='story-box'>Os indicadores abaixo refletem o <b>último trimestre disponível "
    "no período filtrado</b>. Eles são a âncora numérica da nossa análise — ponto de partida "
    "para entender de onde viemos e para onde caminhamos.</div>",
    unsafe_allow_html=True,
)

# Calcular KPIs dinamicamente conforme filtro de período
kpi_desocp_total, kpi_desocp_label  = ultimo_valor(d, "total")
kpi_desocp_h,     _                  = ultimo_valor(d, "homens")
kpi_desocp_m,     _                  = ultimo_valor(d, "mulheres")
kpi_emprego,      kpi_emprego_label  = ultimo_valor(e, "total")
kpi_inform,       kpi_inform_label   = ultimo_valor(i, "total")

var_desocp = variacao_pp(d, "total")
var_emprego = variacao_pp(e, "total")
var_inform  = variacao_pp(i, "total")

def delta_html(val, inverso=False):
    """Gera HTML do delta colorido. inverso=True para indicadores onde queda é boa."""
    if val is None:
        return ""
    sinal = "▲" if val > 0 else "▼"
    classe = "kpi-delta-down" if (val > 0) == inverso else "kpi-delta-up"
    return f'<div class="{classe}">{sinal} {abs(val):.1f} pp vs. ano anterior</div>'

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Desocupação Total</div>
        <div class="kpi-value" style="color:#E74C3C;">{kpi_desocp_total:.1f}%</div>
        {delta_html(var_desocp, inverso=True)}
        <div class="kpi-sub">{kpi_desocp_label}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#2196F3;">
        <div class="kpi-label">Desocupação — Homens</div>
        <div class="kpi-value" style="color:#2196F3;">{kpi_desocp_h:.1f}%</div>
        <div class="kpi-sub">{kpi_desocp_label}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#E91E63;">
        <div class="kpi-label">Desocupação — Mulheres</div>
        <div class="kpi-value" style="color:#E91E63;">{kpi_desocp_m:.1f}%</div>
        <div class="kpi-sub">{kpi_desocp_label}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#27AE60;">
        <div class="kpi-label">Taxa de Emprego</div>
        <div class="kpi-value" style="color:#27AE60;">{kpi_emprego:.1f}%</div>
        {delta_html(var_emprego, inverso=False)}
        <div class="kpi-sub">{kpi_emprego_label}</div>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#F39C12;">
        <div class="kpi-label">Taxa de Informalidade</div>
        <div class="kpi-value" style="color:#F39C12;">{kpi_inform:.1f}%</div>
        {delta_html(var_inform, inverso=True)}
        <div class="kpi-sub">{kpi_inform_label}</div>
    </div>""", unsafe_allow_html=True)


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


# =============================================================================
# ATO 3 — EVOLUÇÃO TEMPORAL: A JORNADA DA DESOCUPAÇÃO
# =============================================================================

st.markdown("## 📈 Ato 1 · A jornada da desocupação (2012–2025)")
st.markdown(
    "<div class='story-box'>O gráfico abaixo conta a <b>história completa do desemprego brasileiro</b> "
    "em três atos: a era de ouro do emprego (2012–2014), a grande crise que triplicou o desemprego "
    "(2015–2019) e a recuperação que nos trouxe ao patamar atual. "
    "As <b>faixas coloridas</b> demarcam as três fases históricas.</div>",
    unsafe_allow_html=True,
)

# --- Gráfico 1: Linha temporal da desocupação total com faixas de fase ---

d_valido = d.dropna(subset=["total"])

fig1 = go.Figure()

# Faixas de fase históricas (fixas, independente do filtro)
fases = [
    (2012, 2014, "rgba(39,174,96,0.07)",  "🟢 Expansão"),
    (2015, 2020, "rgba(231,76,60,0.07)",  "🔴 Crise"),
    (2022, 2025, "rgba(52,152,219,0.07)", "🔵 Recuperação"),
]
for fa_ini, fa_fim, cor_faixa, _ in fases:
    fig1.add_vrect(
        x0=f"{fa_ini}-01-01", x1=f"{fa_fim}-12-31",
        fillcolor=cor_faixa, layer="below", line_width=0,
    )

# Linha principal — total
fig1.add_trace(go.Scatter(
    x=d_valido["periodo"],
    y=d_valido["total"],
    mode="lines+markers",
    name="Desocupação total",
    line=dict(color=COR_TOTAL, width=3),
    marker=dict(size=5),
    hovertemplate="<b>%{x|%Y T%{customdata}}</b><br>Desocupação: <b>%{y:.1f}%</b><extra></extra>",
    customdata=d_valido["trimestre"],
))

# Anotações de pico e mínimo
pico_row = d_valido.loc[d_valido["total"].idxmax()]
min_row  = d_valido.loc[d_valido["total"].idxmin()]

fig1.add_annotation(
    x=pico_row["periodo"], y=pico_row["total"],
    text=f"<b>Pico histórico<br>{pico_row['total']:.1f}% ({pico_row['label_trim']})</b>",
    showarrow=True, arrowhead=2, arrowcolor=COR_ALERTA,
    font=dict(color=COR_ALERTA, size=11),
    bgcolor="white", bordercolor=COR_ALERTA, borderwidth=1,
    ax=40, ay=-45,
)
fig1.add_annotation(
    x=min_row["periodo"], y=min_row["total"],
    text=f"<b>Mínimo: {min_row['total']:.1f}%<br>({min_row['label_trim']})</b>",
    showarrow=True, arrowhead=2, arrowcolor=COR_OK,
    font=dict(color=COR_OK, size=11),
    bgcolor="white", bordercolor=COR_OK, borderwidth=1,
    ax=-50, ay=40,
)

# Legendas das fases
for fa_ini, fa_fim, _, rotulo in fases:
    fig1.add_annotation(
        x=f"{(fa_ini+fa_fim)//2}-06-01", y=d_valido["total"].max() * 1.02,
        text=rotulo, showarrow=False,
        font=dict(size=10, color="#555"),
    )

fig1.update_layout(
    title=dict(text="Taxa de Desocupação Total — Trimestral (%)", font=dict(size=16, color=COR_TOTAL)),
    xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
    yaxis=dict(title="Taxa de Desocupação (%)", range=[0, d_valido["total"].max() * 1.12]),
    template=TEMPLATE,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
    margin=dict(t=60, b=40, l=60, r=30),
)

st.plotly_chart(fig1, use_container_width=True)

# --- Gráfico 2: Barras anuais — médias por fase ---

st.markdown("### Desocupação média por ano")
st.markdown(
    "<div class='story-box'>As barras mostram a <b>média anual da desocupação</b>, "
    "facilitando a comparação entre anos. A coloração por fase deixa evidente "
    "o mergulho e a recuperação do mercado.</div>",
    unsafe_allow_html=True,
)

media_anual_d = calcular_media_anual(d, ["total"])

def cor_barra_desocp(v):
    if v >= 15:   return COR_ALERTA
    if v >= 12:   return "#E67E22"
    if v < 9:     return COR_OK
    return COR_NEUTRO

cores_barras = [cor_barra_desocp(v) for v in media_anual_d["total"]]

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=media_anual_d["ano"].astype(str),
    y=media_anual_d["total"].round(1),
    marker_color=cores_barras,
    name="Média anual",
    text=media_anual_d["total"].round(1).astype(str) + "%",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Desocupação média: <b>%{y:.1f}%</b><extra></extra>",
))

# Linha de referência: média geral do período
media_geral = media_anual_d["total"].mean()
fig2.add_hline(
    y=media_geral,
    line_dash="dot", line_color="#888",
    annotation_text=f"Média do período: {media_geral:.1f}%",
    annotation_position="bottom right",
    annotation_font_color="#888",
)

fig2.update_layout(
    title=dict(text="Desocupação Média Anual (%) — verde < 9% | cinza 9–12% | laranja 12–15% | vermelho ≥ 15%", font=dict(size=14, color=COR_TOTAL)),
    xaxis=dict(title="Ano"),
    yaxis=dict(title="Desocupação média (%)", range=[0, media_anual_d["total"].max() * 1.18]),
    template=TEMPLATE,
    showlegend=False,
    height=380,
    margin=dict(t=55, b=40, l=60, r=30),
)

st.plotly_chart(fig2, use_container_width=True)


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


# =============================================================================
# ATO 4 — DESIGUALDADE DE GÊNERO
# =============================================================================

st.markdown("## ⚖️ Ato 2 · A desigualdade que não desaparece — recorte por sexo")
st.markdown(
    "<div class='alert-box'>Mesmo nos períodos de melhora geral do mercado de trabalho, "
    "as <b>mulheres consistentemente registram taxas de desocupação mais altas</b> que os homens. "
    "Esse diferencial estrutural de ~3 pontos percentuais persistiu ao longo de toda a série "
    "e não mostra sinais de convergência.</div>",
    unsafe_allow_html=True,
)

# --- Gráfico 3: Linhas múltiplas — desocupação por sexo ---

col_map = {"Total": ("total", COR_TOTAL), "Homens": ("homens", COR_HOMENS), "Mulheres": ("mulheres", COR_MULHERES)}

fig3 = go.Figure()
for gen in generos:
    col, cor = col_map[gen]
    d_gen = d.dropna(subset=[col])
    fig3.add_trace(go.Scatter(
        x=d_gen["periodo"],
        y=d_gen[col],
        mode="lines+markers",
        name=gen,
        line=dict(
            color=cor,
            width=2.5,
            dash="dot" if gen == "Total" else "solid",
        ),
        marker=dict(size=4),
        hovertemplate=f"<b>{gen}</b> · %{{x|%Y T%{{customdata}}}}: <b>%{{y:.1f}}%</b><extra></extra>",
        customdata=d_gen["trimestre"],
    ))

# Área de destaque do gap H/M
if "Homens" in generos and "Mulheres" in generos:
    d_hm = d.dropna(subset=["homens", "mulheres"])
    fig3.add_trace(go.Scatter(
        x=pd.concat([d_hm["periodo"], d_hm["periodo"][::-1]]),
        y=pd.concat([d_hm["mulheres"], d_hm["homens"][::-1]]),
        fill="toself",
        fillcolor="rgba(233,30,99,0.07)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Gap H/M",
        showlegend=True,
        hoverinfo="skip",
    ))

fig3.update_layout(
    title=dict(text="Taxa de Desocupação por Sexo — Trimestral (%)", font=dict(size=16, color=COR_TOTAL)),
    xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
    yaxis=dict(title="Desocupação (%)"),
    template=TEMPLATE,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
    margin=dict(t=60, b=40, l=60, r=30),
)

st.plotly_chart(fig3, use_container_width=True)

# --- Gráfico 4: Barras agrupadas — média anual por sexo ---

st.markdown("### Gap de gênero por ano")
st.markdown(
    "<div class='story-box'>As barras agrupadas permitem comparar o diferencial entre homens "
    "e mulheres <b>ano a ano</b>. Observe como, mesmo no pico da recuperação (2025), "
    "a diferença permanece evidente.</div>",
    unsafe_allow_html=True,
)

media_anual_gen = calcular_media_anual(d, ["homens", "mulheres"])

fig4 = go.Figure()
if "Homens" in generos:
    fig4.add_trace(go.Bar(
        x=media_anual_gen["ano"].astype(str),
        y=media_anual_gen["homens"].round(1),
        name="Homens",
        marker_color=COR_HOMENS,
        hovertemplate="<b>Homens %{x}</b>: %{y:.1f}%<extra></extra>",
    ))
if "Mulheres" in generos:
    fig4.add_trace(go.Bar(
        x=media_anual_gen["ano"].astype(str),
        y=media_anual_gen["mulheres"].round(1),
        name="Mulheres",
        marker_color=COR_MULHERES,
        hovertemplate="<b>Mulheres %{x}</b>: %{y:.1f}%<extra></extra>",
    ))

fig4.update_layout(
    barmode="group",
    title=dict(text="Desocupação Média Anual por Sexo (%)", font=dict(size=14, color=COR_TOTAL)),
    xaxis=dict(title="Ano"),
    yaxis=dict(title="Desocupação média (%)"),
    template=TEMPLATE,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=380,
    margin=dict(t=55, b=40, l=60, r=30),
)

st.plotly_chart(fig4, use_container_width=True)

# --- Gráfico 5: Taxa de emprego por sexo ---

st.markdown("### Taxa de emprego: uma assimetria estrutural")
st.markdown(
    "<div class='alert-box'><b>~24 pontos percentuais</b> separam homens e mulheres na taxa de "
    "emprego ao longo de toda a série. Essa lacuna estrutural — maior que em praticamente qualquer "
    "outro país da América Latina — reflete jornadas de cuidado não remuneradas, barreiras setoriais "
    "e segregação ocupacional.</div>",
    unsafe_allow_html=True,
)

fig5 = go.Figure()
for gen in generos:
    col, cor = col_map[gen]
    e_gen = e.dropna(subset=[col])
    dash = "dot" if gen == "Total" else "solid"
    fig5.add_trace(go.Scatter(
        x=e_gen["periodo"],
        y=e_gen[col],
        mode="lines+markers",
        name=gen,
        line=dict(color=cor, width=2.5, dash=dash),
        marker=dict(size=4),
        hovertemplate=f"<b>Emprego — {gen}</b> · %{{x|%Y}}: <b>%{{y:.1f}}%</b><extra></extra>",
    ))

# Área de gap H/M no emprego
if "Homens" in generos and "Mulheres" in generos:
    e_hm = e.dropna(subset=["homens", "mulheres"])
    fig5.add_trace(go.Scatter(
        x=pd.concat([e_hm["periodo"], e_hm["periodo"][::-1]]),
        y=pd.concat([e_hm["homens"], e_hm["mulheres"][::-1]]),
        fill="toself",
        fillcolor="rgba(52,152,219,0.07)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Gap H/M (emprego)",
        showlegend=True,
        hoverinfo="skip",
    ))

fig5.update_layout(
    title=dict(text="Taxa de Emprego por Sexo — Trimestral (%)", font=dict(size=16, color=COR_TOTAL)),
    xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
    yaxis=dict(title="Taxa de emprego (%)"),
    template=TEMPLATE,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400,
    margin=dict(t=60, b=40, l=60, r=30),
)

st.plotly_chart(fig5, use_container_width=True)


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


# =============================================================================
# ATO 5 — A QUALIDADE DO EMPREGO: INFORMALIDADE
# =============================================================================

st.markdown("## 🔧 Ato 3 · A crise silenciosa — informalidade estrutural")
st.markdown(
    "<div class='story-box'>Enquanto o desemprego caiu, a informalidade permaneceu cronicamente "
    "alta. Em 2025, <b>quase 1 em cada 2 trabalhadores brasileiros ocupados</b> está sem carteira "
    "assinada, FGTS, 13º salário ou seguro-desemprego. A recuperação do mercado gerou "
    "<i>quantidade</i> de empregos — mas não necessariamente <i>qualidade</i>.</div>",
    unsafe_allow_html=True,
)

# --- Gráfico 6: Informalidade — área empilhada + linhas por sexo ---

i_valido = i.dropna(subset=["total"])

fig6 = go.Figure()

# Área de fundo para total
fig6.add_trace(go.Scatter(
    x=i_valido["periodo"],
    y=i_valido["total"],
    mode="lines",
    name="Total (área)",
    line=dict(color="rgba(243,156,18,0.4)", width=0),
    fill="tozeroy",
    fillcolor="rgba(243,156,18,0.12)",
    showlegend=False,
    hoverinfo="skip",
))

for gen in generos:
    col, cor = col_map[gen]
    i_gen = i.dropna(subset=[col])
    if i_gen.empty:
        continue
    fig6.add_trace(go.Scatter(
        x=i_gen["periodo"],
        y=i_gen[col],
        mode="lines+markers",
        name=gen,
        line=dict(
            color=cor,
            width=2.5,
            dash="dot" if gen == "Total" else "solid",
        ),
        marker=dict(size=4),
        hovertemplate=f"<b>Informalidade — {gen}</b> · %{{x|%Y}}: <b>%{{y:.1f}}%</b><extra></extra>",
    ))

# Marcação do pico
pico_i = i_valido.loc[i_valido["total"].idxmax()]
fig6.add_annotation(
    x=pico_i["periodo"], y=pico_i["total"],
    text=f"<b>Pico: {pico_i['total']:.1f}%<br>({pico_i['label_trim']})</b>",
    showarrow=True, arrowhead=2, arrowcolor=COR_ALERTA,
    font=dict(color=COR_ALERTA, size=11),
    bgcolor="white", bordercolor=COR_ALERTA, borderwidth=1,
    ax=50, ay=-35,
)

fig6.update_layout(
    title=dict(text="Taxa de Informalidade por Sexo — Trimestral (%) · Série a partir de 2015", font=dict(size=16, color=COR_TOTAL)),
    xaxis=dict(title="Período", showgrid=False, tickformat="%Y"),
    yaxis=dict(title="Informalidade (%)", range=[40, i_valido["total"].max() * 1.12]),
    template=TEMPLATE,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
    margin=dict(t=60, b=40, l=60, r=30),
)

st.plotly_chart(fig6, use_container_width=True)

# --- Gráfico 7: Painel duplo — desocupação vs informalidade ---

st.markdown("### Desemprego cai, informalidade permanece")
st.markdown(
    "<div class='story-box'>O painel abaixo sobrepõe as duas séries no mesmo eixo temporal. "
    "Fica evidente que a queda do desemprego <b>não se traduz automaticamente</b> em melhora "
    "da qualidade do emprego.</div>",
    unsafe_allow_html=True,
)

# Unir os dois datasets pelo período para o painel duplo
df_comparativo = pd.merge(
    d[["periodo", "ano", "label_trim", "total"]].rename(columns={"total": "desocupacao"}),
    i[["periodo", "total"]].rename(columns={"total": "informalidade"}),
    on="periodo",
    how="inner",
).dropna()

fig7 = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    subplot_titles=("Desocupação Total (%)", "Informalidade Total (%)"),
    vertical_spacing=0.08,
)

fig7.add_trace(go.Scatter(
    x=df_comparativo["periodo"],
    y=df_comparativo["desocupacao"],
    name="Desocupação",
    line=dict(color=COR_TOTAL, width=2.5),
    mode="lines",
    hovertemplate="<b>Desocupação</b> %{x|%Y}: %{y:.1f}%<extra></extra>",
), row=1, col=1)

fig7.add_trace(go.Scatter(
    x=df_comparativo["periodo"],
    y=df_comparativo["informalidade"],
    name="Informalidade",
    line=dict(color="#F39C12", width=2.5),
    fill="tozeroy",
    fillcolor="rgba(243,156,18,0.1)",
    mode="lines",
    hovertemplate="<b>Informalidade</b> %{x|%Y}: %{y:.1f}%<extra></extra>",
), row=2, col=1)

fig7.update_layout(
    title=dict(text="Desocupação vs. Informalidade — Evolução Comparada", font=dict(size=14, color=COR_TOTAL)),
    template=TEMPLATE,
    hovermode="x unified",
    showlegend=True,
    height=500,
    margin=dict(t=60, b=40, l=60, r=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig7.update_yaxes(title_text="Desocupação (%)", row=1, col=1)
fig7.update_yaxes(title_text="Informalidade (%)", row=2, col=1)
fig7.update_xaxes(title_text="Período", showgrid=False, tickformat="%Y", row=2, col=1)

st.plotly_chart(fig7, use_container_width=True)

# --- Gráfico 8: Dispersão — correlação entre indicadores ---

st.markdown("### Correlação entre indicadores")
st.markdown(
    "<div class='story-box'>O gráfico de dispersão mostra a relação entre "
    f"<b>{eixo_x_scatter.lower()}</b> e <b>informalidade</b> para cada ano disponível. "
    "Cada bolha representa um ano — o tamanho indica a variação anual da desocupação.</div>",
    unsafe_allow_html=True,
)

# Calcular médias anuais dos três indicadores para o scatter
ma_d = calcular_media_anual(d, ["total"]).rename(columns={"total": "desocp"})
ma_e = calcular_media_anual(e, ["total"]).rename(columns={"total": "emprego"})
ma_i = calcular_media_anual(i, ["total"]).rename(columns={"total": "informal"})

df_scatter = ma_d.merge(ma_e, on="ano").merge(ma_i, on="ano").dropna()
df_scatter["variacao_desocp"] = df_scatter["desocp"].diff().abs().fillna(1)

eixo_x_col = "desocp" if eixo_x_scatter == "Desocupação" else "emprego"
eixo_x_titulo = "Desocupação média anual (%)" if eixo_x_scatter == "Desocupação" else "Taxa de emprego média (%)"

fig8 = go.Figure()
fig8.add_trace(go.Scatter(
    x=df_scatter[eixo_x_col],
    y=df_scatter["informal"],
    mode="markers+text",
    text=df_scatter["ano"].astype(str),
    textposition="top center",
    textfont=dict(size=10, color="#555"),
    marker=dict(
        size=df_scatter["variacao_desocp"] * 10 + 14,
        color=df_scatter["desocp"],
        colorscale=[[0, COR_OK], [0.5, "#E67E22"], [1, COR_ALERTA]],
        showscale=True,
        colorbar=dict(title="Desocupação (%)"),
        opacity=0.85,
        line=dict(color="white", width=1),
    ),
    hovertemplate=(
        "<b>Ano: %{text}</b><br>"
        f"{eixo_x_titulo.split(' (')[0]}: <b>%{{x:.1f}}%</b><br>"
        "Informalidade: <b>%{y:.1f}%</b><extra></extra>"
    ),
    name="Ano",
))

fig8.update_layout(
    title=dict(text=f"Dispersão: {eixo_x_titulo.split(' (')[0]} × Informalidade (médias anuais)", font=dict(size=14, color=COR_TOTAL)),
    xaxis=dict(title=eixo_x_titulo),
    yaxis=dict(title="Informalidade média anual (%)"),
    template=TEMPLATE,
    height=420,
    margin=dict(t=55, b=40, l=60, r=30),
)

st.plotly_chart(fig8, use_container_width=True)


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


# =============================================================================
# ATO 6 — CONCLUSÕES
# =============================================================================

st.markdown("## ✅ Conclusões — O que os dados nos dizem")

col_c1, col_c2, col_c3 = st.columns(3)

with col_c1:
    st.markdown("""
    <div class="conclusion-box">
        <b>🔄 Recuperação real, mas frágil</b><br><br>
        A desocupação recuou de <b>19,0%</b> (pico de 2017) para <b>8,8%</b> (T4/2025),
        aproximando-se dos níveis pré-crise de 2013. A recuperação é real, mas ainda não
        está consolidada estruturalmente.
    </div>
    """, unsafe_allow_html=True)

with col_c2:
    st.markdown("""
    <div class="alert-box">
        <b>⚠️ Desigualdade de gênero persistente</b><br><br>
        A diferença de desocupação entre homens e mulheres se manteve em torno de
        <b>3,2 pp</b> durante toda a série. A recuperação não corrigiu essa
        assimetria estrutural — ela apenas a acompanhou.
    </div>
    """, unsafe_allow_html=True)

with col_c3:
    st.markdown("""
    <div class="alert-box">
        <b>🏗️ Informalidade ainda é o maior desafio</b><br><br>
        Mesmo no mínimo histórico de <b>45,9%</b> (T4/2025), quase metade
        dos trabalhadores ocupados está sem proteção trabalhista plena.
        A qualidade do emprego gerado segue como questão central.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div class='story-box'>"
    "📌 <b>Leitura final:</b> O mercado de trabalho brasileiro entre 2012 e 2025 viveu "
    "uma montanha-russa — com uma queda profunda e uma recuperação expressiva. "
    "Contudo, dois problemas estruturais resistiram ao ciclo: "
    "<b>(1)</b> a desigualdade de gênero no acesso ao emprego, e "
    "<b>(2)</b> a informalidade crônica, que limita a proteção social de quase metade da força de trabalho. "
    "Indicadores de quantidade (desocupação) melhoraram — os de qualidade, ainda não o suficiente."
    "</div>",
    unsafe_allow_html=True,
)

# Nota de rodapé metodológica
st.markdown("---")
st.caption(
    "📋 **Nota metodológica** · Fonte: PNAD Contínua — IBGE · "
    "Periodicidade trimestral (T1=jan-mar, T2=abr-jun, T3=jul-set, T4=out-dez) · "
    "Período coberto: 2012–2025 · "
    "**Dados ausentes:** zeros substituídos por NaN — afeta 2020-T2 a 2022-T1 nas três séries "
    "e 2012–2015-T2 na série de informalidade · "
    "Médias anuais calculadas apenas sobre trimestres com dados válidos."
)