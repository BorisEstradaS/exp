import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# -----------------------------------
# CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Sample Supplies Dashboard",
    layout="wide",
)

st.title("📦 MongoDB Atlas - Sample Supplies Dashboard")

# -----------------------------------
# CONNECTION
# -----------------------------------
@st.cache_resource
def get_client():
    uri = st.secrets["MONGO_URI"]
    return MongoClient(uri)

client = get_client()

# database y colección
db = client["sample_supplies"]
collection = db["sales"]

# -----------------------------------
# LOAD DATA
# -----------------------------------
@st.cache_data
def load_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    return df

df = load_data()

st.success(f"✅ Registros cargados: {len(df)}")

# -----------------------------------
# DATA CLEANING
# -----------------------------------
if "storeLocation" not in df.columns:
    st.error("La columna storeLocation no existe.")
    st.stop()

df["purchaseDate"] = pd.to_datetime(df["purchaseDate"])

# -----------------------------------
# SIDEBAR FILTERS
# -----------------------------------
st.sidebar.header("Filtros")

stores = df["storeLocation"].dropna().unique()

selected_store = st.sidebar.selectbox(
    "Seleccionar tienda",
    stores
)

filtered_df = df[df["storeLocation"] == selected_store]

# -----------------------------------
# KPIs
# -----------------------------------
total_sales = filtered_df["saleDate"].count()
total_items = filtered_df["items"].apply(len).sum()

col1, col2 = st.columns(2)

col1.metric("🛒 Ventas Totales", total_sales)
col2.metric("📦 Items Vendidos", total_items)

# -----------------------------------
# SALES OVER TIME
# -----------------------------------
sales_time = (
    filtered_df
    .groupby(filtered_df["purchaseDate"].dt.date)
    .size()
    .reset_index(name="ventas")
)

fig_time = px.line(
    sales_time,
    x="purchaseDate",
    y="ventas",
    title="Ventas por Día"
)

st.plotly_chart(fig_time, use_container_width=True)

# -----------------------------------
# ITEMS ANALYSIS
# -----------------------------------
items_df = filtered_df.explode("items")

items_df["itemName"] = items_df["items"].apply(
    lambda x: x.get("name") if isinstance(x, dict) else None
)

top_items = (
    items_df["itemName"]
    .value_counts()
    .head(10)
    .reset_index()
)

top_items.columns = ["Producto", "Cantidad"]

fig_items = px.bar(
    top_items,
    x="Producto",
    y="Cantidad",
    title="Top Productos Vendidos"
)

st.plotly_chart(fig_items, use_container_width=True)

# -----------------------------------
# DATA PREVIEW
# -----------------------------------
st.subheader("📋 Vista de Datos")

st.dataframe(filtered_df.head(50), use_container_width=True)
