# Deploy do Dashboard (Streamlit)

O dashboard do projeto está em `dashboard/app.py` e usa `requirements.txt` na raiz.

## Opção 1 — Streamlit Community Cloud (recomendado)

1. Suba este repositório para o GitHub (público ou privado).
2. Acesse o Streamlit Community Cloud e crie um novo app.
3. Selecione o repositório e configure:
   - **Main file path**: `dashboard/app.py`
4. Aguarde o build e copie o link gerado (use no PDF de entregáveis).

Obs.: o app consegue gerar `data/prc/reclameaqui_ibyte_clean.csv` a partir de `data/raw/RECLAMEAQUI_IBYTE.csv` se o arquivo processado não estiver presente.

## Opção 2 — Render (Web Service)

Você pode usar o `render.yaml` (na raiz) ou configurar manualmente:

- **Build command**: `python -m pip install -r requirements.txt`
- **Start command**: `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`

Depois do deploy, copie a URL pública do serviço para `docs/entregaveis_links.json`.
