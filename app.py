import streamlit as st
import psycopg2

# ---------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------
st.set_page_config(
    page_title="Banco Regional Andino",
    page_icon="🏦",
    layout="centered"
)

st.title("🏦 Banco Regional Andino")
st.subheader("Evaluación Inteligente de Crédito")

# ---------------------------------------------------
# CREDENCIALES BD
# ---------------------------------------------------
USER = st.secrets["DB_USER"]
PASSWORD = st.secrets["DB_PASSWORD"]
HOST = st.secrets["DB_HOST"]
PORT = st.secrets["DB_PORT"]
DBNAME = st.secrets["DB_NAME"]

def get_connection():
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=5
    )

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "cliente" not in st.session_state:
    st.session_state.cliente = None

if "aprobado" not in st.session_state:
    st.session_state.aprobado = False


# ---------------------------------------------------
# FUNCION SCORE VISUAL
# ---------------------------------------------------
def mostrar_score(score):

    st.markdown("### 📊 Score Crediticio")

    st.progress(score / 1000)

    if score >= 750:
        st.success("🟢 Riesgo Bajo")
    elif score >= 600:
        st.warning("🟡 Riesgo Medio")
    else:
        st.error("🔴 Riesgo Alto")


# ---------------------------------------------------
# BUSCAR CLIENTE
# ---------------------------------------------------
dni = st.text_input("🔎 Ingresa tu DNI")

if st.button("Evaluar cliente"):

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT edad,
                   ingreso_mensual,
                   tipo_empleo,
                   antiguedad_laboral,
                   score_crediticio,
                   deudas_actuales,
                   ratio_deuda_ingreso,
                   historial_pagos
            FROM ml.credito
            WHERE dni = %s
            LIMIT 1
        """, (dni,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if row:

            st.session_state.cliente = row

            edad, ingreso, empleo, antiguedad, score, deudas, ratio, historial = row

            # 🧠 MODELO SIMPLE CREDIT SCORING
            if score >= 650 and ratio < 0.45 and historial != "malo":
                st.session_state.aprobado = True
            else:
                st.session_state.aprobado = False

        else:
            st.error("❌ Cliente no encontrado")
            st.session_state.cliente = None

    except Exception as e:
        st.error(f"Error conexión BD: {e}")


# ---------------------------------------------------
# MOSTRAR RESULTADOS
# ---------------------------------------------------
if st.session_state.cliente:

    edad, ingreso, empleo, antiguedad, score, deudas, ratio, historial = st.session_state.cliente

    st.success("✅ Cliente encontrado")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Edad", edad)
        st.metric("Ingreso Mensual", f"S/ {ingreso:,.0f}")
        st.metric("Tipo Empleo", empleo)

    with col2:
        st.metric("Antigüedad Laboral", f"{antiguedad} años")
        st.metric("Deudas Actuales", f"S/ {deudas:,.0f}")
        st.metric("Ratio Deuda/Ingreso", f"{ratio:.2f}")

    st.divider()

    # SCORE CREDITICIO
    mostrar_score(score)

    st.write(f"Historial de pagos: **{historial.upper()}**")

    st.divider()

    # DECISIÓN
    if st.session_state.aprobado:
        st.success("✅ Cliente PREAPROBADO para crédito")
    else:
        st.error("❌ Cliente NO califica para crédito")
