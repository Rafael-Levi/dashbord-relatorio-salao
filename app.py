import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_excel, validate_dataframe, add_derived_columns, kpis, top_n_services, services_by_professional, time_series_counts

st.set_page_config(page_title="Relatorio de Servicos — Dashboard", layout="wide")

st.title("Dashboard Estratégico — relatorio_servicos.xlsx")
st.markdown("Faça upload do arquivo `relatorio_servicos.xlsx` (ou arraste e solte) para validar e explorar os dados.")

uploaded = st.file_uploader("Upload do arquivo Excel", type=["xlsx", "xls"], accept_multiple_files=False)

if uploaded is None:
    st.info("Faça upload do arquivo `relatorio_servicos.xlsx` para começar.\n\nO app valida as colunas esperadas e gera KPIs e gráficos.")
    st.stop()

try:
    df = load_excel(uploaded)
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

is_valid, missing = validate_dataframe(df)
if not is_valid:
    st.error(f"Arquivo inválido: faltam colunas obrigatórias: {missing}")
    st.write("Colunas detectadas:", df.columns.tolist())
    st.stop()

# Add derived
df = add_derived_columns(df)

# Top bar KPIs
kp = kpis(df)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total serviços", kp["total_servicos"])
col2.metric("Concluídos", kp["concluidos"])
col3.metric("Agendados", kp["agendados"])
col4.metric("Duração média (min)", f"{kp['avg_duration']:.1f}" if kp["avg_duration"] is not None else "—")

# Main layout: left filters, right charts
with st.expander("Amostra dos dados e qualidade", expanded=True):
    st.dataframe(df.head(200))
    st.write("Informações gerais:")
    st.write(df.info())

# Filters
with st.sidebar:
    st.header("Filtros")
    profs = st.multiselect("Profissional", options=df["profissional_nome"].unique().tolist(), default=None)
    servs = st.multiselect("Serviço", options=df["servico_nome"].unique().tolist(), default=None)
    statuses = st.multiselect("Status", options=df["status"].unique().tolist(), default=None)
    date_range = st.date_input("Intervalo de datas (início)", value=(df["date"].min(), df["date"].max()))

# Apply filters
fdf = df.copy()
if profs:
    fdf = fdf[fdf["profissional_nome"].isin(profs)]
if servs:
    fdf = fdf[fdf["servico_nome"].isin(servs)]
if statuses:
    fdf = fdf[fdf["status"].isin(statuses)]
if date_range:
    start, end = date_range
    fdf = fdf[(fdf["date"] >= start) & (fdf["date"] <= end)]

st.subheader("Visão geral")
left, right = st.columns((2,3))

with left:
    st.write("Serviços por profissional (top 10)")
    df_prof = services_by_professional(fdf)
    st.dataframe(df_prof.head(20))

    st.write("Top serviços")
    st.dataframe(top_n_services(fdf, n=10))

with right:
    st.write("Série temporal — quantidade de atendimentos por dia")
    ts = time_series_counts(fdf, freq="D")
    fig = px.line(ts, x="inicio", y="count", title="Atendimentos por dia")
    st.plotly_chart(fig, use_container_width=True)

st.write("## Distribuições e análises adicionais")
col_a, col_b = st.columns(2)
with col_a:
    st.write("Distribuição de duração")
    fig2 = px.histogram(fdf, x="duracao_calc", nbins=20, title="Histograma: duração (min)")
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    st.write("Composição por status")
    fig3 = px.pie(fdf, names="status", title="Status dos atendimentos")
    st.plotly_chart(fig3, use_container_width=True)

st.write("## Exportar dados filtrados")
csv = fdf.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV filtrado", data=csv, file_name="relatorio_servicos_filtrado.csv", mime="text/csv")

st.write("Feito por Rafael Levi --\nDashbord para desafio da M2 Tecnologia")