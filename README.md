# eda-projeto1

Projeto 1 — **Análise Exploratória (EDA)** e preparação de métricas para **Dashboard** a partir de dados do ReclameAqui (empresa: **Ibyte**).

## Estrutura

- `data/raw/RECLAMEAQUI_IBYTE.csv`: dataset bruto
- `data/prc/`: saídas processadas (geradas pelos notebooks)
- `docs/Projeto 1 - Análise Exploratória e Dashboard de Dados do ReclameAqui.pdf`: enunciado
- `notebooks/`: notebooks do projeto

## Como rodar

1. Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

2. Execute na ordem:

- `notebooks/01_limpeza_reclameaqui_ibyte.ipynb` → gera `data/prc/reclameaqui_ibyte_clean.csv`
- `notebooks/02_analise_exploratoria_reclameaqui_ibyte.ipynb` → gera agregações em `data/prc/` (ex.: `agg_mensal_casos.csv`, `agg_uf_ano_casos.csv`)

Obs.: o notebook de EDA baixa (e cacheia) um GeoJSON de UFs em `data/ref/brazil-states.geojson` para o mapa.

## Dashboard (Streamlit)

O dashboard atende aos requisitos do enunciado (filtros globais + componentes obrigatórios).

Para rodar localmente:

```bash
streamlit run dashboard/app.py
```

Obs.: o app lê `data/prc/reclameaqui_ibyte_clean.csv` se existir; caso contrário, processa `data/raw/RECLAMEAQUI_IBYTE.csv` automaticamente.

Deploy: veja `docs/deploy_dashboard.md`.

## Entregáveis (PDF com links)

1. Preencha `docs/entregaveis_links.json`
2. Gere o PDF:

```bash
python scripts/generate_entregaveis_pdf.py
```

Isso cria `docs/Entregaveis_Projeto1_ReclameAqui.pdf`.
