import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(
    page_title="Simulador de Crédito",
    page_icon="🏦",
    layout="centered"
)

# ─── Credenciales desde secrets ───────────────────────────────────────────────
USER     = st.secrets["DB_USER"]
PASSWORD = st.secrets["DB_PASSWORD"]
HOST     = st.secrets["DB_HOST"]
PORT     = st.secrets["DB_PORT"]
DBNAME   = st.secrets["DB_NAME"]

# ─── Conexión ─────────────────────────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        connect_timeout=5
    )

# ─── Cálculo de cuota mensual (sistema francés) ───────────────────────────────
def calcular_cuota(monto: float, cuotas: int, tasa_mensual: float = 0.015) -> float:
    r = tasa_mensual
    return monto * r * (1 + r) ** cuotas / ((1 + r) ** cuotas - 1)

# ─── Estilos personalizados ───────────────────────────────────────────────────
st.markdown("""
<style>
    .big-title  { font-size: 2rem; font-weight: 700; margin-bottom: 0; }
    .sub-title  { font-size: 1rem; color: #6b7280; margin-top: 0; }
    .metric-row { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
    .metric-box {
        flex: 1; min-width: 130px;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.75rem 1rem;
    }
    .metric-label { font-size: 0.75rem; color: #6b7280; margin: 0; }
    .metric-value { font-size: 1.1rem; font-weight: 600; margin: 0; }
    .score-bar-track {
        height: 8px; border-radius: 4px;
        background: #e5e7eb; overflow: hidden; margin: 4px 0 12px;
    }
    .score-bar-fill {
        height: 100%; border-radius: 4px; transition: width 0.5s;
    }
</style>
""", unsafe_allow_html=True)

# ─── Encabezado ───────────────────────────────────────────────────────────────
st.markdown('<p class="big-title">🏦 Banco Regional Andino</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Simulador de Crédito Inteligente</p>', unsafe_allow_html=True)
st.divider()

# ─── Estado de sesión ─────────────────────────────────────────────────────────
if "cliente" not in st.session_state:
    st.session_state.cliente = None
if "aprobado" not in st.session_state:
    st.session_state.aprobado = False
if "dni" not in st.session_state:
    st.session_state.dni = ""
if "desembolsado" not in st.session_state:
    st.session_state.desembolsado = False

# ─── SECCIÓN 1: Buscar cliente ────────────────────────────────────────────────
st.subheader("🔎 Consulta tu crédito")

col1, col2 = st.columns([3, 1])
with col1:
    dni = st.text_input("Número de DNI", placeholder="Ej: 12345678", label_visibility="collapsed")
with col2:
    buscar = st.button("Consultar", use_container_width=True, type="primary")

if buscar:
    st.session_state.desembolsado = False
    if not dni:
        st.error("⚠️ Ingresa un DNI válido.")
    else:
        with st.spinner("Consultando base de datos..."):
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute("""
                    SELECT edad, ingreso_mensual, tipo_empleo,
                           antiguedad_laboral, score_crediticio,
                           deudas_actuales, ratio_deuda_ingreso,
                           historial_pagos, nombre
                    FROM ml.credito
                    WHERE dni = %s
                    LIMIT 1
                """, (dni,))
                row = cur.fetchone()
                cur.close()
                conn.close()

                if row:
                    st.session_state.cliente = row
                    st.session_state.dni      = dni
                    _, _, _, _, score, _, ratio, historial, _ = row
                    st.session_state.aprobado = (
                        score >= 600 and ratio < 0.4 and historial != "malo"
                    )
                else:
                    st.session_state.cliente  = None
                    st.session_state.aprobado = False
                    st.error("❌ DNI no encontrado en el sistema.")

            except Exception as e:
                st.error(f"Error de conexión: {e}")

# ─── SECCIÓN 2: Mostrar perfil del cliente ────────────────────────────────────
if st.session_state.cliente:
    (edad, ingreso, empleo, antiguedad,
     score, deudas, ratio, historial, nombre) = st.session_state.cliente

    st.divider()
    st.subheader(f"👤 {nombre or 'Cliente'}")

    # Score bar
    score_pct  = min(int((score / 900) * 100), 100)
    bar_color  = "#16a34a" if score >= 600 else "#dc2626"
    st.markdown(f"""
    <p style="font-size:0.8rem;color:#6b7280;margin-bottom:2px;">
        Score crediticio: <strong>{score}</strong> / 900
    </p>
    <div class="score-bar-track">
        <div class="score-bar-fill"
             style="width:{score_pct}%; background:{bar_color};"></div>
    </div>
    """, unsafe_allow_html=True)

    # Métricas
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box">
            <p class="metric-label">Edad</p>
            <p class="metric-value">{edad} años</p>
        </div>
        <div class="metric-box">
            <p class="metric-label">Ingreso mensual</p>
            <p class="metric-value">S/ {ingreso:,.0f}</p>
        </div>
        <div class="metric-box">
            <p class="metric-label">Tipo de empleo</p>
            <p class="metric-value">{empleo.capitalize()}</p>
        </div>
        <div class="metric-box">
            <p class="metric-label">Antigüedad laboral</p>
            <p class="metric-value">{antiguedad} años</p>
        </div>
        <div class="metric-box">
            <p class="metric-label">Deudas actuales</p>
            <p class="metric-value">S/ {deudas:,.0f}</p>
        </div>
        <div class="metric-box">
            <p class="metric-label">Ratio deuda/ingreso</p>
            <p class="metric-value">{ratio:.0%}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── SECCIÓN 3: Resultado ─────────────────────────────────────────────────
    st.divider()

    if st.session_state.aprobado:
        st.success("✅ ¡Crédito PRE-APROBADO!")

        st.subheader("📋 Configura tu crédito")
        col_m, col_c = st.columns(2)
        with col_m:
            monto = st.selectbox(
                "Monto a solicitar (S/)",
                options=[1000, 3000, 5000, 10000, 20000],
                format_func=lambda x: f"S/ {x:,}",
                index=2
            )
        with col_c:
            cuotas = st.selectbox(
                "Número de cuotas",
                options=[6, 12, 18, 24, 36],
                format_func=lambda x: f"{x} meses",
                index=1
            )

        # Simulación financiera
        cuota_mensual = calcular_cuota(monto, cuotas)
        total_pagar   = cuota_mensual * cuotas
        total_intereses = total_pagar - monto

        c1, c2, c3 = st.columns(3)
        c1.metric("Cuota mensual",   f"S/ {cuota_mensual:,.2f}")
        c2.metric("Total a pagar",   f"S/ {total_pagar:,.2f}")
        c3.metric("Total intereses", f"S/ {total_intereses:,.2f}")

        st.caption("⚙️ Tasa de interés: 1.5% mensual (TEA ~19.56%). Cálculo en sistema francés.")

        st.divider()

        if not st.session_state.desembolsado:
            if st.button("💳 Aceptar y desembolsar crédito", type="primary", use_container_width=True):
                with st.spinner("Procesando..."):
                    try:
                        conn = get_connection()
                        cur  = conn.cursor()
                        cur.execute("""
                            UPDATE ml.credito
                            SET monto_solicitado = %s,
                                plazo_meses      = %s,
                                preaprobado      = TRUE
                            WHERE dni = %s
                        """, (monto, cuotas, st.session_state.dni))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.session_state.desembolsado = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al procesar: {e}")
        else:
            st.success(
                f"🎉 ¡Crédito desembolsado! "
                f"S/ {monto:,} en {cuotas} cuotas de S/ {cuota_mensual:,.2f}"
            )
            st.balloons()

    else:
        st.error("❌ Crédito rechazado")

        # Mostrar motivo de rechazo
        motivos = []
        if score < 600:
            motivos.append(f"• Score crediticio insuficiente ({score} / mínimo 600)")
        if ratio >= 0.4:
            motivos.append(f"• Ratio deuda/ingreso elevado ({ratio:.0%} / máximo 40%)")
        if historial == "malo":
            motivos.append("• Historial de pagos negativo")

        if motivos:
            with st.expander("Ver motivos de rechazo"):
                for m in motivos:
                    st.write(m)

        st.info("Puedes volver a solicitar cuando mejore tu perfil crediticio.")
