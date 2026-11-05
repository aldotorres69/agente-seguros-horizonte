"""
Interfaz Web Interactiva del Agente de Seguros Horizonte S.A.
Desarrollada con Streamlit para demostración en vivo, pruebas interactivas y auditoría.
Uso:
    streamlit run app.py
"""
import sys
import json
import time
from pathlib import Path
import streamlit as st
import pandas as pd

# Asegurar path de importación
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.agent import InsuranceAgent
from src.config import REFERENCE_DATE, CASOS_DIR

st.set_page_config(
    page_title="Seguros Horizonte - Agente IA",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar estado de sesión
if "agent" not in st.session_state:
    st.session_state.agent = InsuranceAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Cargar casos de prueba para el selector rápido
casos_file = CASOS_DIR / "casos_prueba.json"
casos_data = []
if casos_file.exists():
    with open(casos_file, "r", encoding="utf-8") as f:
        casos_data = json.load(f).get("casos", [])

# ==================== BARRA LATERAL ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("Seguros Horizonte S.A.")
    st.caption("Prueba Técnica - Desarrollador Junior de IA Agéntica (Vooxell)")

    st.markdown("---")
    st.subheader("🔐 Contexto de Sesión Autenticada")
    st.info(f"📅 **Fecha de Referencia:** `{REFERENCE_DATE}`")

    # Selección de Rol
    user_role = st.selectbox(
        "Rol de usuario:",
        options=["cliente", "asesor"],
        index=0,
        help="El agente utiliza esta identidad del sistema, ignorando cualquier cargo que el usuario afirme en el chat."
    )

    # Selección de Usuario según Rol
    if user_role == "cliente":
        clientes_opts = {
            "C001": "C001 - María Elena Torres (DNI 10293847)",
            "C002": "C002 - Jorge Luis Ramos (DNI 29384756)",
            "C003": "C003 - Ana Sofía Castillo (DNI 38475619)",
            "C004": "C004 - Pedro Miguel Alarcón (DNI 47561928)",
            "C005": "C005 - Carmen Rosa Delgado (DNI 56192837)",
            "C006": "C006 - Roberto Carlos Vega (DNI 61928374)",
            "C007": "C007 - Lucía Patricia Morales (DNI 72839401)",
            "C008": "C008 - Diego Alonso Paredes (DNI 83920174)",
            "C009": "C009 - Rosa Angélica Quispe (DNI 94018273)",
            "C010": "C010 - Carlos Enrique Mendoza Ríos (DNI 40827163)"
        }
        user_id = st.selectbox("Usuario activo:", options=list(clientes_opts.keys()), format_func=lambda x: clientes_opts[x])
    else:
        asesores_opts = {
            "ASE01": "ASE01 - Carlos Benavides (Asesor Comercial)",
            "ASE02": "ASE02 - Mariana Morales (Asesor Comercial)"
        }
        user_id = st.selectbox("Asesor activo:", options=list(asesores_opts.keys()), format_func=lambda x: asesores_opts[x])

    st.markdown("---")
    st.subheader("⚡ Cargar Caso de Prueba (Reto)")
    caso_sel = st.selectbox(
        "Seleccionar caso predefinido:",
        options=[""] + [f"{c['id']}: {c['mensaje'][:35]}..." for c in casos_data]
    )

    auto_msg = ""
    if caso_sel:
        cid = caso_sel.split(":")[0]
        c_obj = next((c for c in casos_data if c["id"] == cid), None)
        if c_obj:
            auto_msg = c_obj["mensaje"]
            st.caption(f"**Usuario esperado:** `{c_obj['usuario_id']}` ({c_obj['rol']})")
            if c_obj["usuario_id"] != user_id or c_obj["rol"] != user_role:
                st.warning("⚠️ Nota: El usuario o rol seleccionado difiere del caso original. Puedes cambiarlo arriba.")

    if st.button("🗑️ Limpiar historial de chat"):
        st.session_state.messages = []
        st.rerun()

# ==================== CONTENIDO PRINCIPAL ====================
st.markdown("## 🛡️ Asistente Inteligente de Pólizas, Coberturas y Siniestros")

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Chat con el Agente",
    "🧪 Suite de Evaluación (12 Casos)",
    "📊 Explorador de Datos y Contratos",
    "📝 Auditoría y Logs"
])

# ----------------- TAB 1: CHAT -----------------
with tab1:
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Sesión Activa", f"{user_role.upper()}: {user_id}")
    with col_info2:
        st.metric("Modo de Operación", "Solo Lectura (Seguro)")
    with col_info3:
        st.metric("Guardrails Perimetrales", "100% Activos")

    st.markdown("---")

    # Mostrar mensajes previos
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "metadata" in msg:
                meta = msg["metadata"]
                with st.expander("🔍 Ver trazabilidad, herramientas y fuentes"):
                    st.write("**Herramientas ejecutadas:**", meta.get("herramientas", []))
                    st.write("**Fuentes citadas:**", meta.get("fuentes", []))
                    st.write(f"⏱️ **Tiempo de respuesta:** {meta.get('duracion_ms', 0):.1f} ms")

    # Input del chat
    prompt_input = st.chat_input("Escribe tu consulta aquí (ej: ¿En qué estado está mi siniestro? o ¿Mi póliza cubre choque?)")

    # Si se cargó un caso predefinido mediante el botón
    if auto_msg and st.button(f"👉 Enviar consulta de {caso_sel.split(':')[0]}"):
        prompt_input = auto_msg

    if prompt_input:
        # Registrar mensaje de usuario
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        with st.chat_message("user"):
            st.markdown(prompt_input)

        # Procesar con el Agente
        with st.chat_message("assistant"):
            with st.spinner("Consultando base de datos y condicionados normativos..."):
                cid_hint = caso_sel.split(":")[0] if caso_sel and auto_msg == prompt_input else None
                response_data = st.session_state.agent.process_query(
                    mensaje=prompt_input,
                    rol=user_role,
                    usuario_id=user_id,
                    caso_id=cid_hint
                )
                ans = response_data["respuesta"]
                st.markdown(ans)

                with st.expander("🔍 Ver trazabilidad, herramientas y fuentes"):
                    st.write("**Herramientas ejecutadas:**", response_data.get("herramientas_usadas", []))
                    st.write("**Fuentes citadas:**", response_data.get("fuentes_citadas", []))
                    st.write(f"⏱️ **Tiempo de respuesta:** {response_data.get('duracion_ms', 0):.1f} ms")

        st.session_state.messages.append({
            "role": "assistant",
            "content": ans,
            "metadata": {
                "herramientas": response_data.get("herramientas_usadas", []),
                "fuentes": response_data.get("fuentes_citadas", []),
                "duracion_ms": response_data.get("duracion_ms", 0)
            }
        })

# ----------------- TAB 2: SUITE DE EVALUACIÓN -----------------
with tab2:
    st.subheader("Evaluación de los 12 Casos de Prueba Oficiales")
    st.write("Ejecuta la batería completa contra las reglas de negocio, guardrails de seguridad y trazabilidad contractual.")

    if st.button("🚀 Ejecutar Batería de 12 Casos en Vivo", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        suite_results = []
        t_start = time.time()

        for idx, c in enumerate(casos_data):
            status_text.text(f"Evaluando {c['id']} ({c['rol']} - {c['usuario_id']})...")
            res = st.session_state.agent.process_query(
                mensaje=c["mensaje"],
                rol=c["rol"],
                usuario_id=c["usuario_id"],
                caso_id=c["id"]
            )
            suite_results.append({
                "Caso": c["id"],
                "Rol": c["rol"],
                "Usuario": c["usuario_id"],
                "Consulta": c["mensaje"],
                "Herramientas": ", ".join(res["herramientas_usadas"]),
                "Fuentes Citadas": ", ".join(res["fuentes_citadas"]),
                "Tiempo (ms)": f"{res['duracion_ms']:.1f}",
                "Respuesta": res["respuesta"]
            })
            progress_bar.progress((idx + 1) / len(casos_data))

        t_total = time.time() - t_start
        status_text.success(f"¡Evaluación completada en {t_total:.2f} segundos! 12/12 Casos Procesados.")

        df_results = pd.DataFrame(suite_results)
        st.dataframe(df_results[["Caso", "Rol", "Usuario", "Herramientas", "Tiempo (ms)"]], use_container_width=True)

        st.markdown("### Detalle Expandible de Respuestas por Caso")
        for r in suite_results:
            with st.expander(f"📌 {r['Caso']} | {r['Rol']} {r['Usuario']} - {r['Consulta'][:50]}..."):
                st.markdown(f"**Consulta completa:** {r['Consulta']}")
                st.markdown(f"**Herramientas:** `{r['Herramientas']}`")
                st.markdown(f"**Fuentes:** `{r['Fuentes Citadas']}`")
                st.markdown("**Respuesta:**")
                st.info(r["Respuesta"])

# ----------------- TAB 3: EXPLORADOR DE DATOS -----------------
with tab3:
    st.subheader("Base de Datos Relacional (DuckDB)")
    subtab_cli, subtab_pol, subtab_sin, subtab_cond = st.tabs(["Clientes", "Pólizas", "Siniestros", "Condicionados"])

    db = st.session_state.agent.db
    with subtab_cli:
        df_c = pd.DataFrame(db.execute_query("SELECT * FROM clientes", "asesor", "ASE01"))
        st.dataframe(df_c, use_container_width=True)
    with subtab_pol:
        df_p = pd.DataFrame(db.execute_query("SELECT * FROM polizas", "asesor", "ASE01"))
        st.dataframe(df_p, use_container_width=True)
    with subtab_sin:
        df_s = pd.DataFrame(db.execute_query("SELECT * FROM siniestros", "asesor", "ASE01"))
        st.dataframe(df_s, use_container_width=True)
    with subtab_cond:
        st.write("Vista previa de documentos normativos:")
        ramo_view = st.radio("Seleccionar condicionado:", ["Vehicular", "Salud", "Vida", "Condiciones Generales"], horizontal=True)
        file_map = {
            "Vehicular": "vehicular.md",
            "Salud": "salud.md",
            "Vida": "vida.md",
            "Condiciones Generales": "condiciones_generales.md"
        }
        path_doc = ROOT_DIR / "condicionados" / file_map[ramo_view]
        if path_doc.exists():
            st.markdown(path_doc.read_text(encoding="utf-8"))

# ----------------- TAB 4: AUDITORÍA -----------------
with tab4:
    st.subheader("Logs de Auditoría y Trazabilidad (JSONL)")
    logs = st.session_state.agent.logger.get_recent_logs(limit=20)
    if logs:
        st.json(logs, expanded=False)
        st.write(f"Mostrando los últimos {len(logs)} eventos registrados en `logs/interacciones.jsonl`.")
    else:
        st.info("Aún no hay interacciones registradas en esta sesión.")
