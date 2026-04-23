import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

st.set_page_config(
    page_title="Simulador de Crédito",
    page_icon="🏦",
    layout="centered"
)

# ─── Conexión MongoDB Atlas ────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return MongoClient(st.secrets["MONGO_URI"], serverSelectionTimeoutMS=5000)

def get_collection():
    client = get_client()
    db     = client[st.secrets["MONGO_DB"]]
    return db[st.secrets["MONGO_COL"]]

# ─── Cálculo de cuota mensual (sistema francés) ───────────────────────────────
def calcular_cuota(monto: float, cuotas: int, tasa_mensual: float = 0.015) -> float:
    r = tasa_mensual
    return monto * r * (1 + r) ** cuotas / ((1 + r) ** cuotas - 1)

# ─── Estilos ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .big-title  { font-size: 2rem; font-weight: 700; margin-bottom: 0; }
    .sub-title  { font-size: 1rem; color: #6b7280; margin-top: 0; }
    .metric-row { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
    .metric-box {
        flex: 1; min-width: 130px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.75rem 1rem;
    }
    .metric-label { font-size: 0.75rem; color: #374151; margin: 0; }
    .metric-value { font-size: 1.1rem; font-weight: 600; margin: 0; }
    .score-bar-track {
        height: 8px; border-radius: 4px;
        background: #111827!important; overflow: hidden; margin: 4px 0 12px;
    }
    .score-bar-fill { height: 100%; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ─── Encabezado ───────────────────────────────────────────────────────────────
st.markdown('<p class="big-title">🏦 Banco Regional Andino</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Simulador de Crédito Inteligente</p>', unsafe_allow_html=True)
st.divider()

# ─── Estado de sesión ─────────────────────────────────────────────────────────
for key, val in {
    "cliente": None,
    "aprobado": False,
    "dni": "",
    "desembolsado": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─── SECCIÓN 1: Buscar cliente ────────────────────────────────────────────────
st.subheader("🔎 Consulta tu crédito")

col1, col2 = st.columns([3, 1])
with col1:
    dni = st.text_input(
        "DNI", placeholder="Ingresa tus 8 dígitos",
        max_chars=8, label_visibility="collapsed"
    )
with col2:
    buscar = st.button("Consultar", use_container_width=True, type="primary")

if buscar:
    st.session_state.desembolsado = False
    st.session_state.cliente      = None

    if not dni or not dni.isdigit() or len(dni) != 8:
        st.error("⚠️ Ingresa un DNI válido de 8 dígitos.")
    else:
        with st.spinner("Consultando base de datos..."):
            try:
                col_db = get_collection()
                doc    = col_db.find_one({"dni": dni})

                if doc:
                    st.session_state.cliente  = doc
                    st.session_state.dni      = dni
                    score     = doc.get("score_crediticio", 0)
                    ratio     = doc.get("ratio_deuda_ingreso", 1)
                    historial = doc.get("historial_pagos", "malo")
                    st.session_state.aprobado = (
                        score >= 600 and ratio < 0.4 and historial != "malo"
                    )
                else:
                    st.error("❌ DNI no encontrado en el sistema.")

            except ConnectionFailure:
                st.error("❌ No se pudo conectar a la base de datos. Verifica tu MONGO_URI.")
            except OperationFailure as e:
                st.error(f"❌ Error de autenticación: {e}")
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")

# ─── SECCIÓN 2: Perfil del cliente ────────────────────────────────────────────
if st.session_state.cliente:
    doc = st.session_state.cliente

    nombre     = doc.get("nombre", "Cliente")
    edad       = doc.get("edad", "—")
    ingreso    = doc.get("ingreso_mensual", 0)
    empleo     = doc.get("tipo_empleo", "—")
    antiguedad = doc.get("antiguedad_laboral", "—")
    score      = doc.get("score_crediticio", 0)
    deudas     = doc.get("deudas_actuales", 0)
    ratio      = doc.get("ratio_deuda_ingreso", 0)
    historial  = doc.get("historial_pagos", "—")

    st.divider()
    st.subheader(f"👤 {nombre}")

    # Barra de score
    score_pct = min(int((score / 900) * 100), 100)
    bar_color = "#16a34a" if score >= 600 else "#dc2626"
    st.markdown(f"""
    <p style="font-size:0.8rem;color:#6b7280;margin-bottom:2px;">
        Score crediticio: <strong>{score}</strong> / 900
    </p>
    <div class="score-bar-track">
        <div class="score-bar-fill"
             style="width:{score_pct}%; background:{bar_color};"></div>
    </div>
    """, unsafe_allow_html=True)

    # Tarjetas de métricas
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

        cm, cc = st.columns(2)
        with cm:
            monto = st.selectbox(
                "Monto a solicitar (S/)",
                [1000, 3000, 5000, 10000, 20000],
                format_func=lambda x: f"S/ {x:,}",
                index=2
            )
        with cc:
            cuotas = st.selectbox(
                "Número de cuotas",
                [6, 12, 18, 24, 36],
                format_func=lambda x: f"{x} meses",
                index=1
            )

        cuota_mensual   = calcular_cuota(monto, cuotas)
        total_pagar     = cuota_mensual * cuotas
        total_intereses = total_pagar - monto

        c1, c2, c3 = st.columns(3)
        c1.metric("Cuota mensual",   f"S/ {cuota_mensual:,.2f}")
        c2.metric("Total a pagar",   f"S/ {total_pagar:,.2f}")
        c3.metric("Total intereses", f"S/ {total_intereses:,.2f}")
        st.caption("⚙️ Tasa: 1.5% mensual (TEA ~19.56%). Sistema francés.")

        st.divider()

        if not st.session_state.desembolsado:
            if st.button("💳 Aceptar y desembolsar crédito", type="primary", use_container_width=True):
                with st.spinner("Procesando desembolso..."):
                    try:
                        col_db = get_collection()
                        col_db.update_one(
                            {"dni": st.session_state.dni},
                            {"$set": {
                                "monto_solicitado": monto,
                                "plazo_meses":      cuotas,
                                "preaprobado":      True
                            }}
                        )
                        st.session_state.desembolsado = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al procesar: {e}")
        else:
            st.success(
                f"🎉 ¡Crédito desembolsado! "
                f"S/ {monto:,} en {cuotas} cuotas de S/ {cuota_mensual:,.2f}"
            )
            st.balloons()

    else:
        st.error("❌ Crédito rechazado")

        motivos = []
        if score < 600:
            motivos.append(f"Score crediticio insuficiente ({score} / mínimo 600)")
        if ratio >= 0.4:
            motivos.append(f"Ratio deuda/ingreso elevado ({ratio:.0%} / máximo 40%)")
        if historial == "malo":
            motivos.append("Historial de pagos negativo")

        if motivos:
            with st.expander("Ver motivos de rechazo"):
                for m in motivos:
                    st.markdown(f"• {m}")

        st.info("Puedes volver a solicitar cuando mejore tu perfil crediticio.")
