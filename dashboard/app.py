from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from wordcloud import WordCloud


GEO_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

UF_TO_ESTADO = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

STATUS_MAP = {
    "resolvido": "Resolvido",
    "respondida": "Respondida",
    "em réplica": "Em réplica",
    "não resolvido": "Não resolvido",
    "nao resolvido": "Não resolvido",
    "não respondida": "Não respondida",
    "nao respondida": "Não respondida",
}

DEFAULT_STOPWORDS_PT = {
    "a",
    "à",
    "agora",
    "ainda",
    "além",
    "algo",
    "algum",
    "alguma",
    "algumas",
    "alguns",
    "ao",
    "aos",
    "após",
    "as",
    "até",
    "com",
    "como",
    "da",
    "das",
    "de",
    "dei",
    "delas",
    "dele",
    "deles",
    "demais",
    "depois",
    "desde",
    "do",
    "dos",
    "e",
    "ela",
    "elas",
    "ele",
    "eles",
    "em",
    "entre",
    "era",
    "eram",
    "essa",
    "essas",
    "esse",
    "esses",
    "esta",
    "está",
    "estão",
    "estas",
    "este",
    "estes",
    "eu",
    "faz",
    "foi",
    "for",
    "fora",
    "foram",
    "há",
    "isso",
    "isto",
    "já",
    "la",
    "lá",
    "lhe",
    "lhes",
    "mais",
    "mas",
    "me",
    "mesmo",
    "meu",
    "minha",
    "muito",
    "na",
    "não",
    "nas",
    "nem",
    "no",
    "nos",
    "nós",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "por",
    "porque",
    "pra",
    "quando",
    "que",
    "quem",
    "se",
    "sem",
    "ser",
    "só",
    "sua",
    "suas",
    "também",
    "tem",
    "tendo",
    "tenho",
    "ter",
    "teve",
    "tinha",
    "tive",
    "toda",
    "todas",
    "todo",
    "todos",
    "um",
    "uma",
    "umas",
    "uns",
    "vai",
    "vou",
    "vocês",
    "você",
    "vc",
    "vcs",
    "www",
    # termos muito específicos do contexto (ajuda a limpar a wordcloud)
    "ibyte",
    "loja",
    "produto",
}


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    for parent in [start, *start.parents]:
        if (parent / "data").exists() and (parent / "docs").exists():
            return parent
        
    return start


def normalize_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_stopwords_pt() -> set[str]:
    stop = set(DEFAULT_STOPWORDS_PT)
    try:
        import nltk  # type: ignore
        from nltk.corpus import stopwords  # type: ignore

        try:
            stop |= set(stopwords.words("portuguese"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            stop |= set(stopwords.words("portuguese"))
    except Exception:
        pass
    
    return stop


def clean_raw_dataset(raw_path: Path) -> pd.DataFrame:
    df_raw = pd.read_csv(raw_path, encoding="utf-8", skipinitialspace=True)

    rename = {
        "ID": "id",
        "TEMA": "tema",
        "LOCAL": "local",
        "TEMPO": "tempo",
        "CATEGORIA": "categoria",
        "STATUS": "status",
        "DESCRICAO": "descricao",
        "URL": "url",
        "ANO": "ano",
        "MES": "mes",
        "DIA": "dia",
        "DIA_DO_ANO": "dia_do_ano",
        "SEMANA_DO_ANO": "semana_do_ano",
        "DIA_DA_SEMANA": "dia_da_semana",
        "TRIMETRES": "trimestre",
        "CASOS": "casos",
    }
    df = df_raw.rename(columns=rename).copy()

    text_cols = ["tema", "local", "tempo", "categoria", "status", "descricao", "url"]
    num_cols = [
        "id",
        "ano",
        "mes",
        "dia",
        "dia_do_ano",
        "semana_do_ano",
        "dia_da_semana",
        "trimestre",
        "casos",
    ]

    for col in text_cols:
        df[col] = df[col].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df["data_reclamacao"] = pd.to_datetime(df["tempo"], errors="coerce")

    df["status"] = df["status"].str.lower().map(STATUS_MAP).fillna(df["status"])

    df[["cidade", "uf"]] = df["local"].str.rsplit(" - ", n=1, expand=True)
    df["cidade"] = df["cidade"].astype("string").str.strip()
    df["uf"] = df["uf"].astype("string").str.strip().str.upper()
    df["estado"] = df["uf"].map(UF_TO_ESTADO).astype("string")

    cat_levels = df["categoria"].str.split("<->", expand=True)
    cat_levels.columns = [f"categoria_n{i+1}" for i in range(cat_levels.shape[1])]
    df = pd.concat([df, cat_levels], axis=1)
    df["categoria_final"] = df["categoria"].str.split("<->").str[-1]
    df["categoria_profundidade"] = df["categoria"].str.count("<->") + 1

    df["descricao_n_caracteres"] = df["descricao"].str.len().astype("Int64")
    df["descricao_n_palavras"] = df["descricao"].str.split().map(len).astype("Int64")

    q33 = int(df["descricao_n_palavras"].quantile(1 / 3))
    q66 = int(df["descricao_n_palavras"].quantile(2 / 3))
    labels = [f"Curto (≤{q33})", f"Médio ({q33+1}–{q66})", f"Longo (>{q66})"]
    df["faixa_tamanho_texto"] = pd.cut(
        df["descricao_n_palavras"],
        bins=[-1, q33, q66, float("inf")],
        labels=labels,
    )

    return df


@st.cache_data(show_spinner=False)
def load_data(project_root: str) -> pd.DataFrame:
    root = Path(project_root)
    prc_path = root / "data" / "prc" / "reclameaqui_ibyte_clean.csv"
    raw_path = root / "data" / "raw" / "RECLAMEAQUI_IBYTE.csv"

    if prc_path.exists():
        df = pd.read_csv(prc_path, encoding="utf-8")
    elif raw_path.exists():
        df = clean_raw_dataset(raw_path)
        prc_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(prc_path, index=False, encoding="utf-8")
    else:
        raise FileNotFoundError(f"Não encontrei {prc_path} nem {raw_path}.")

    df["data_reclamacao"] = pd.to_datetime(df["data_reclamacao"], errors="coerce")
    for col in ["ano", "mes", "casos", "descricao_n_palavras"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data(show_spinner=False)
def load_geojson(project_root: str) -> dict:
    root = Path(project_root)
    geo_dir = root / "data" / "ref"
    geo_dir.mkdir(parents=True, exist_ok=True)
    geo_path = geo_dir / "brazil-states.geojson"

    if not geo_path.exists():
        urllib.request.urlretrieve(GEO_URL, geo_path)

    return json.loads(geo_path.read_text(encoding="utf-8"))


def filter_df(
    df: pd.DataFrame,
    estados: list[str],
    status: list[str],
    faixas_texto: list[str],
) -> pd.DataFrame:
    out = df.copy()
    if estados:
        out = out[out["estado"].isin(estados)]
    if status:
        out = out[out["status"].isin(status)]
    if faixas_texto:
        out = out[out["faixa_tamanho_texto"].astype(str).isin(faixas_texto)]
    return out


@dataclass(frozen=True)
class KPIs:
    casos_total: int
    pct_resolvido: float
    top_uf: str
    top_categoria: str


def compute_kpis(df: pd.DataFrame) -> KPIs:
    casos_total = int(pd.to_numeric(df["casos"], errors="coerce").fillna(0).sum())
    resolved = int(pd.to_numeric(df.loc[df["status"] == "Resolvido", "casos"], errors="coerce").fillna(0).sum())
    pct = (resolved / casos_total) if casos_total else 0.0

    top_uf = "-"
    if "uf" in df.columns and len(df):
        top_uf = str(df.groupby("uf")["casos"].sum().sort_values(ascending=False).index[0])

    top_cat = "-"
    if "categoria_final" in df.columns and len(df):
        top_cat = str(df.groupby("categoria_final")["casos"].sum().sort_values(ascending=False).index[0])

    return KPIs(casos_total=casos_total, pct_resolvido=pct, top_uf=top_uf, top_categoria=top_cat)


def make_time_series(df: pd.DataFrame) -> go.Figure:
    ts = df.groupby(pd.Grouper(key="data_reclamacao", freq="MS"))["casos"].sum().reset_index()
    ts["mm_3m"] = ts["casos"].rolling(window=3, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["data_reclamacao"], y=ts["casos"], mode="lines+markers", name="CASOS"))
    fig.add_trace(go.Scatter(x=ts["data_reclamacao"], y=ts["mm_3m"], mode="lines", name="Média móvel (3M)"))
    fig.update_layout(
        title="Série temporal: reclamações por mês (CASOS) + tendência (média móvel)",
        xaxis_title="Mês",
        yaxis_title="CASOS",
        legend_title="Série",
    )
    return fig


def make_status_bar(df: pd.DataFrame) -> go.Figure:
    agg = df.groupby("status")["casos"].sum().sort_values(ascending=False).reset_index()
    total = float(agg["casos"].sum()) if len(agg) else 0.0
    agg["pct"] = (agg["casos"] / total) * 100 if total else 0.0

    fig = px.bar(
        agg,
        x="status",
        y="casos",
        text=agg["pct"].map(lambda x: f"{x:.1f}%"),
        title="Proporção de resoluções: reclamações por Status (CASOS)",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="CASOS", xaxis_title="Status")
    return fig


def make_pareto_uf(df: pd.DataFrame) -> go.Figure:
    uf_tot = df.groupby("uf")["casos"].sum().sort_values(ascending=False)
    pareto = uf_tot.reset_index().rename(columns={"casos": "casos_uf"})
    pareto["perc"] = pareto["casos_uf"] / pareto["casos_uf"].sum() if len(pareto) else 0
    pareto["perc_acum"] = pareto["perc"].cumsum() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=pareto["uf"], y=pareto["casos_uf"], name="CASOS por UF"), secondary_y=False)
    fig.add_trace(
        go.Scatter(x=pareto["uf"], y=pareto["perc_acum"], name="% acumulado", mode="lines+markers"),
        secondary_y=True,
    )
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%", secondary_y=True)
    fig.update_layout(title="Distribuição espacial: Pareto de reclamações por UF (CASOS)")
    fig.update_yaxes(title_text="CASOS", secondary_y=False)
    fig.update_yaxes(title_text="% acumulado", secondary_y=True, range=[0, 105])
    return fig


def make_map_uf_year(df: pd.DataFrame, geojson: dict, year: int) -> go.Figure:
    map_df = df[df["ano"] == year].groupby("uf")["casos"].sum().reset_index()

    all_ufs = sorted({f["properties"]["sigla"] for f in geojson.get("features", []) if "properties" in f})
    if all_ufs:
        base = pd.DataFrame({"uf": all_ufs})
        map_df = base.merge(map_df, on="uf", how="left").fillna({"casos": 0})

    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="uf",
        featureidkey="properties.sigla",
        color="casos",
        color_continuous_scale="Reds",
        labels={"casos": "Reclamações (CASOS)", "uf": "UF"},
        title=f"Mapa (cloroplético): reclamações por UF no ano {year}",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig


def make_text_boxplot(df: pd.DataFrame) -> go.Figure:
    fig = px.box(
        df,
        x="status",
        y="descricao_n_palavras",
        points="outliers",
        title="Análise estatística de textos: tamanho da descrição (palavras) × Status",
    )
    fig.update_layout(xaxis_title="Status", yaxis_title="Nº de palavras")
    return fig


@st.cache_data(show_spinner=False)
def compute_wordcloud_image(texts: tuple[tuple[str, int], ...]) -> np.ndarray:
    stop = get_stopwords_pt()

    freq: Counter[str] = Counter()
    for text, weight in texts:
        if not text:
            continue
        tokens = [
            t
            for t in normalize_text(text).split()
            if (t not in stop) and (len(t) >= 3)
        ]
        if not tokens:
            continue
        for t in tokens:
            freq[t] += max(int(weight), 1)

    wc = WordCloud(
        width=1200,
        height=500,
        background_color="white",
        colormap="viridis",
        random_state=42,
    )
    wc.generate_from_frequencies(freq)
    return wc.to_array()


def main() -> None:
    st.set_page_config(page_title="Projeto 1 — ReclameAqui (Ibyte)", layout="wide")

    st.title("Projeto 1 — Dashboard (ReclameAqui • Ibyte)")
    st.caption(
        "Filtros globais obrigatórios: Estado, Status e Faixa de tamanho do texto. "
        "Componentes: série temporal + média móvel, mapa por UF com slider de ano, Pareto por UF, "
        "proporção de status, boxplot texto×status e WordCloud."
    )

    project_root = str(find_repo_root(Path.cwd()))
    df = load_data(project_root)
    geojson = load_geojson(project_root)

    # Sidebar — filtros globais
    st.sidebar.header("Filtros globais")

    estados_opts = sorted([e for e in df["estado"].dropna().unique()])
    status_opts = sorted([s for s in df["status"].dropna().unique()])
    faixa_opts = sorted([f for f in df["faixa_tamanho_texto"].dropna().astype(str).unique()])

    estados_sel = st.sidebar.multiselect("Estado", options=estados_opts, default=estados_opts)
    status_sel = st.sidebar.multiselect("Status", options=status_opts, default=status_opts)
    faixa_sel = st.sidebar.multiselect(
        "Faixa do tamanho do texto",
        options=faixa_opts,
        default=faixa_opts,
        help="Criada no notebook de limpeza a partir do nº de palavras em DESCRICAO.",
    )

    df_f = filter_df(df, estados=estados_sel, status=status_sel, faixas_texto=faixa_sel)

    # KPI cards
    kpis = compute_kpis(df_f)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CASOS (total)", f"{kpis.casos_total:,}".replace(",", "."))
    c2.metric("% Resolvido", f"{kpis.pct_resolvido*100:.1f}%")
    c3.metric("Top UF", kpis.top_uf)
    c4.metric("Top Categoria", kpis.top_categoria)

    st.divider()

    # 1) Série temporal + média móvel
    st.subheader("1) Série temporal com tendência (média móvel)")
    st.plotly_chart(make_time_series(df_f), use_container_width=True)

    # 2) Mapa com slider de ano
    st.subheader("2) Análise geográfica: mapa do Brasil (UF) com seletor de ano")
    min_year = int(pd.to_numeric(df["ano"], errors="coerce").dropna().min())
    max_year = int(pd.to_numeric(df["ano"], errors="coerce").dropna().max())
    year = st.slider("Ano (mapa)", min_value=min_year, max_value=max_year, value=max_year, step=1)
    st.plotly_chart(make_map_uf_year(df_f, geojson=geojson, year=year), use_container_width=True)

    # 3) Pareto por UF
    st.subheader("3) Distribuição espacial: Pareto por UF")
    st.plotly_chart(make_pareto_uf(df_f), use_container_width=True)

    # 4) Proporção por status
    st.subheader("4) Proporção de resoluções (STATUS)")
    st.plotly_chart(make_status_bar(df_f), use_container_width=True)

    # 5) Texto × status
    st.subheader("5) Estatística de textos: tamanho do texto × status")
    st.plotly_chart(make_text_boxplot(df_f), use_container_width=True)

    # 6) WordCloud
    st.subheader("6) Mineração de texto: WordCloud (com remoção de stopwords)")
    st.caption("A WordCloud abaixo considera as descrições filtradas e pondera por CASOS.")

    texts = tuple(
        (str(row.descricao) if row.descricao is not None else "", int(row.casos) if not pd.isna(row.casos) else 1)
        for row in df_f[["descricao", "casos"]].itertuples(index=False)
    )
    wc_img = compute_wordcloud_image(texts)
    st.image(wc_img, use_container_width=True)

    with st.expander("Tabela: top 30 palavras (pós-stopwords)", expanded=False):
        stop = get_stopwords_pt()
        freq: Counter[str] = Counter()
        for text, weight in texts:
            if not text:
                continue
            tokens = [
                t
                for t in normalize_text(text).split()
                if (t not in stop) and (len(t) >= 3)
            ]
            for t in tokens:
                freq[t] += max(int(weight), 1)
        top = pd.DataFrame(freq.most_common(30), columns=["palavra", "freq"])
        st.dataframe(top, use_container_width=True, hide_index=True)

    st.divider()
    st.caption("Extra: o app gera/usa `data/prc/reclameaqui_ibyte_clean.csv` automaticamente se não existir.")


if __name__ == "__main__":
    main()

