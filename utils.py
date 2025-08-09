from typing import Tuple, List
import pandas as pd

REQUIRED_COLS = [
    "id",
    "inicio",
    "profissional_nome",
    "cliente_nome",
    "servico_nome",
    "status",
    "duracao_calc",
]


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Verifica se todas as colunas obrigatórias estão presentes.

    Retorna (is_valid, missing_columns).
    """
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    return (len(missing) == 0, missing)


def load_excel(file) -> pd.DataFrame:
    """Carrega o arquivo excel em DataFrame e faz parse básico de tipos."""
    df = pd.read_excel(file)
    # Normalize column names (strip spaces)
    df.columns = [c.strip() for c in df.columns]

    # Ensure expected columns exist — caller deverá validar
    if "inicio" in df.columns:
        # try to parse dates
        df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce")

    if "duracao_calc" in df.columns:
        # coerce to numeric
        df["duracao_calc"] = pd.to_numeric(df["duracao_calc"], errors="coerce")

    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas derivadas úteis para análise de séries temporais e agrupamentos."""
    out = df.copy()
    if "inicio" in out.columns:
        out["date"] = out["inicio"].dt.date
        out["month"] = out["inicio"].dt.to_period("M").dt.to_timestamp()
        out["week"] = out["inicio"].dt.to_period("W").dt.start_time
        out["hour"] = out["inicio"].dt.hour

    # status normalization
    if "status" in out.columns:
        out["status"] = out["status"].astype(str).str.upper().str.strip()

    return out


def kpis(df: pd.DataFrame) -> dict:
    """Calcula KPIs básicos."""
    total = len(df)
    concluded = df[df["status"].str.contains("CONCL", na=False)].shape[0]
    scheduled = df[df["status"].str.contains("AGEN", na=False)].shape[0]
    avg_duration = df["duracao_calc"].dropna().mean()

    return {
        "total_servicos": int(total),
        "concluidos": int(concluded),
        "agendados": int(scheduled),
        "avg_duration": float(avg_duration) if not pd.isna(avg_duration) else None,
    }


def top_n_services(df: pd.DataFrame, n=5) -> pd.DataFrame:
    return (
        df.groupby("servico_nome")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(n)
    )


def services_by_professional(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("profissional_nome")
        .agg(total_servicos=("id","count"), avg_duration=("duracao_calc","mean"))
        .reset_index()
        .sort_values("total_servicos", ascending=False)
    )


def time_series_counts(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Agrupa quantidade de serviços por data com frequência: 'D', 'W', 'M'."""
    if "inicio" not in df.columns:
        raise ValueError("Coluna 'inicio' não encontrada")
    s = df.set_index("inicio").resample(freq).size()
    return s.rename("count").reset_index()