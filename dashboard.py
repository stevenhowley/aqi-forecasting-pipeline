import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import text

from src.db.connection import get_engine

st.set_page_config(page_title="Oregon AQI Dashboard", layout="wide")

AQI_THRESHOLD = 100


def aqi_label(aqi: int) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy for Sensitive Groups"
    if aqi <= 200:  return "Unhealthy"
    return "Very Unhealthy"


@st.cache_data(ttl=300)
def load_locations() -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(
            text("SELECT id, name FROM locations ORDER BY name"), conn
        )


@st.cache_data(ttl=300)
def load_daily_aggregates() -> pd.DataFrame:
    sql = text("""
        SELECT da.location_id, l.name, da.date, da.max_aqi, da.mean_aqi,
               da.min_aqi, da.is_interpolated
        FROM daily_aggregates da
        JOIN locations l ON l.id = da.location_id
        ORDER BY l.name, da.date
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, parse_dates=["date"])


@st.cache_data(ttl=300)
def load_forecasts() -> pd.DataFrame:
    sql = text("""
        SELECT f.location_id, l.name, f.target_date, f.forecast_aqi, f.model_name
        FROM forecasts f
        JOIN locations l ON l.id = f.location_id
        ORDER BY l.name, f.target_date
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(sql, conn, parse_dates=["target_date"])


# --- Load ---
locations   = load_locations()
df_agg      = load_daily_aggregates()
df_forecast = load_forecasts()

# --- Sidebar ---
st.sidebar.title("Filters")
location_options = ["All"] + sorted(locations["name"].tolist())
selected = st.sidebar.selectbox("Location", location_options)
date_range = st.sidebar.slider(
    "Date range (days back)",
    min_value=7, max_value=180, value=60, step=7,
)

cutoff = df_agg["date"].max() - pd.Timedelta(days=date_range)
df_agg_filtered = df_agg[df_agg["date"] >= cutoff].copy()
if selected != "All":
    df_agg_filtered = df_agg_filtered[df_agg_filtered["name"] == selected]
    df_forecast_filtered = df_forecast[df_forecast["name"] == selected]
else:
    df_forecast_filtered = df_forecast.copy()

# --- Title ---
st.title("Oregon AQI Forecasting Dashboard")
st.caption(f"Data refreshes every 5 minutes. Showing last {date_range} days.")

# --- Forecast cards ---
st.subheader("Tomorrow's Forecast")
latest = (
    df_forecast_filtered
    .sort_values("target_date")
    .groupby("name")
    .last()
    .reset_index()
)

if latest.empty:
    st.info("No forecasts available yet.")
else:
    cols = st.columns(len(latest))
    for col, row in zip(cols, latest.itertuples()):
        aqi = row.forecast_aqi
        label = aqi_label(aqi)
        alert = " ⚠️" if aqi >= AQI_THRESHOLD else ""
        col.metric(
            label=f"{row.name}{alert}",
            value=f"AQI {aqi}",
            help=f"{label} — {row.target_date.date()}",
        )

st.divider()

# --- Historical trend ---
st.subheader("Historical Max AQI")

df_real   = df_agg_filtered[~df_agg_filtered["is_interpolated"]]
df_interp = df_agg_filtered[df_agg_filtered["is_interpolated"]]

fig = go.Figure()
for loc_name in sorted(df_agg_filtered["name"].unique()):
    real   = df_real[df_real["name"] == loc_name]
    interp = df_interp[df_interp["name"] == loc_name]

    fig.add_trace(go.Scatter(
        x=real["date"], y=real["max_aqi"],
        mode="lines", name=loc_name,
        legendgroup=loc_name,
    ))
    if not interp.empty:
        fig.add_trace(go.Scatter(
            x=interp["date"], y=interp["max_aqi"],
            mode="markers", name=f"{loc_name} (estimated)",
            legendgroup=loc_name,
            marker=dict(symbol="x", size=7, opacity=0.6),
        ))

fig.add_hline(
    y=AQI_THRESHOLD, line_dash="dot", line_color="red",
    annotation_text="Alert threshold (100)", annotation_position="bottom right",
)
fig.update_layout(
    xaxis_title="Date", yaxis_title="Max AQI",
    hovermode="x unified", height=400, margin=dict(t=20),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Forecast accuracy ---
st.subheader("Forecast vs Actual")

df_accuracy = df_forecast_filtered.merge(
    df_agg[["name", "date", "max_aqi"]].rename(columns={"max_aqi": "actual_aqi"}),
    left_on=["name", "target_date"],
    right_on=["name", "date"],
    how="inner",
).drop(columns="date")

if df_accuracy.empty:
    st.info("Not enough overlapping forecast and actual data to compare yet.")
else:
    df_accuracy = df_accuracy[df_accuracy["target_date"] >= cutoff]

    fig2 = go.Figure()
    for loc_name in sorted(df_accuracy["name"].unique()):
        loc = df_accuracy[df_accuracy["name"] == loc_name].sort_values("target_date")
        fig2.add_trace(go.Scatter(
            x=loc["target_date"], y=loc["actual_aqi"],
            mode="lines", name=f"{loc_name} actual",
            legendgroup=loc_name,
        ))
        fig2.add_trace(go.Scatter(
            x=loc["target_date"], y=loc["forecast_aqi"],
            mode="lines", name=f"{loc_name} forecast",
            legendgroup=loc_name,
            line=dict(dash="dash"),
        ))

    fig2.update_layout(
        xaxis_title="Date", yaxis_title="AQI",
        hovermode="x unified", height=400, margin=dict(t=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

    mae = (df_accuracy["forecast_aqi"] - df_accuracy["actual_aqi"]).abs().mean()
    st.caption(f"Mean Absolute Error (visible range, all locations): **{mae:.1f} AQI points**")

st.divider()

# --- Raw data ---
with st.expander("Raw daily aggregates"):
    st.dataframe(
        df_agg_filtered.sort_values(["name", "date"], ascending=[True, False]),
        use_container_width=True,
    )
