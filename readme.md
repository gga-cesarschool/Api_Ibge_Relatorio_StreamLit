# 📊 Dashboard — Mercado de Trabalho Brasileiro (2012–2025)

Dashboard interativo em Streamlit para análise da evolução do mercado de trabalho
brasileiro, seguindo estrutura de **Data Storytelling** em cinco atos narrativos.

---

## 🎯 Objetivo

Contar a história do mercado de trabalho brasileiro entre 2012 e 2025,
conduzindo o usuário por uma sequência lógica de análise:

1. **Contexto** — Apresentação do tema e do período analisado
2. **KPIs** — Situação mais recente em números de destaque
3. **A jornada da desocupação** — Três fases: expansão, crise e recuperação
4. **A desigualdade de gênero** — O gap persistente entre homens e mulheres
5. **A crise silenciosa** — Informalidade estruturalmente elevada mesmo com queda do desemprego
6. **Conclusões** — Síntese narrativa dos principais achados

---

## 🗂️ Bases de dados utilizadas

| Arquivo | Separador | Conteúdo |
|---------|-----------|----------|
| `desocupacao.csv` | `;` | Taxa de desocupação trimestral (total, homens, mulheres) — 2012 a 2025 |
| `emprego.csv` | `,` | Taxa de emprego trimestral (total, homens, mulheres) — 2012 a 2025 |
| `informalidade.csv` | `;` | Taxa de informalidade trimestral (total, homens, mulheres) — 2015 a 2025 |

Fonte: **PNAD Contínua — IBGE** · Periodicidade trimestral.

> ⚠️ **Dados ausentes:** os zeros presentes no dataset original representam ausência de dados
> (lacuna de 2020-T2 a 2022-T1 nas três séries; 2012–2015-T2 na série de informalidade).
> No dashboard, esses zeros são substituídos por `NaN` para não distorcer as análises.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Versão mínima | Uso |
|------------|---------------|-----|
| Python | 3.9+ | Linguagem base |
| Streamlit | 1.35+ | Interface do dashboard |
| Pandas | 2.0+ | Carregamento e tratamento dos dados |
| Plotly | 5.20+ | Gráficos interativos |
| NumPy | 1.24+ | Operações numéricas auxiliares |

---

## 📁 Estrutura de arquivos

```
.
├── app.py               ← Código completo do dashboard
├── requirements.txt     ← Dependências Python
├── README.md            ← Este arquivo
├── desocupacao.csv      ← Base de dados (deve estar na mesma pasta)
├── emprego.csv          ← Base de dados (deve estar na mesma pasta)
└── informalidade.csv    ← Base de dados (deve estar na mesma pasta)
```

> ⚠️ Os três arquivos CSV devem estar **na mesma pasta** que o `app.py`.

---

## 🚀 Como executar

### 1. Clone ou copie os arquivos para uma pasta local

```bash
mkdir dashboard-mercado-trabalho
cd dashboard-mercado-trabalho
# Copie app.py, requirements.txt e os três CSVs para esta pasta
```

### 2. (Opcional) Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o dashboard

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente em `http://localhost:8501`.

---

## 🎛️ Filtros disponíveis

| Filtro | Localização | Efeito |
|--------|-------------|--------|
| **Período de análise** | Sidebar | Filtra todos os gráficos pelo intervalo de anos selecionado |
| **Recorte por sexo** | Sidebar | Exibe/oculta as séries Total, Homens e Mulheres nos gráficos comparativos |
| **Eixo X da dispersão** | Sidebar | Alterna entre Desocupação e Emprego no gráfico de correlação |

---

## 📊 Gráficos do dashboard

| # | Tipo | Indicador | Objetivo narrativo |
|---|------|-----------|-------------------|
| 1 | KPIs (cards) | Todos | Âncora numérica — situação atual |
| 2 | Linha + faixas de fase | Desocupação total | Mostrar as 3 fases históricas (expansão, crise, recuperação) |
| 3 | Barras verticais coloridas | Desocupação anual | Comparar anos com código de cor por gravidade |
| 4 | Linhas múltiplas + área de gap | Desocupação H/M | Revelar e medir a desigualdade de gênero |
| 5 | Barras agrupadas | Desocupação anual H/M | Gap de gênero ano a ano |
| 6 | Linhas múltiplas + gap | Emprego H/M | Evidenciar o diferencial estrutural de ~24 pp |
| 7 | Área + linhas | Informalidade H/M | Mostrar a crise silenciosa da qualidade do emprego |
| 8 | Painel duplo (subplots) | Desocupação × Informalidade | Comparar as duas tendências no mesmo eixo temporal |
| 9 | Dispersão (bolhas) | Desocupação × Informalidade | Correlação entre os indicadores por ano |

---

## 👤 Autoria

Análise baseada em dados públicos do **IBGE — Instituto Brasileiro de Geografia e Estatística**,
via PNAD Contínua. Dashboard desenvolvido com fins educacionais e analíticos.