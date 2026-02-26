import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURACIÓN Y CONSTANTES ---
st.set_page_config(page_title="Gran Premio: Tono vs Franco", layout="centered")

ARCHIVO_DATOS = "datos_apuestas.json"
MAX_TRAGOS = 12

APOSTADORES = [
    "Selecciona...", "Franco (admin)", "Tono", "Ancla", "Zkpl", "Postigo",
    "Benja", "Ivo", "Corbe", "Cums", "Turri", "Chucrut", "Yoyo", "Caco", "Maquina"
]


# --- FUNCIONES DE BASE DE DATOS (JSON) ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r") as f:
            return json.load(f)
    return {
        "estado_apuestas": "Ronda 1 (Pre-partido)",
        "apuestas": {}
    }


def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w") as f:
        json.dump(datos, f)


datos = cargar_datos()
estado_actual = datos["estado_apuestas"]

# --- ENCABEZADO Y ACTUALIZACIÓN ---
col_title, col_btn = st.columns([3, 1])
col_title.title("🎾 Tono vs Franco")
if col_btn.button("🔄 Actualizar", help="Toca para ver las apuestas de los demás"):
    st.rerun()

st.markdown(f"### 📢 Estado: **{estado_actual}**")
st.markdown("💰 **Regla de oro:** Tienes 1 Piscola (12 tragos) en total para administrar.")
st.divider()

# --- VALIDACIÓN DE USUARIO ---
st.subheader("👤 Identifícate")
col1, col2 = st.columns(2)
usuario_1 = col1.selectbox("¿Quién eres?", APOSTADORES, key="user1")
usuario_2 = col2.selectbox("Confirma tu nombre", APOSTADORES, key="user2")

if usuario_1 != "Selecciona..." and usuario_1 == usuario_2:
    st.success(f"¡Bienvenido, {usuario_1}!")

    # --- PANEL DE ADMINISTRADOR ---
    if usuario_1 == "Franco (admin)":
        with st.expander("⚙️ Panel de Administrador"):
            nuevo_estado = st.radio("Cambiar fase del juego:",
                                    ["Ronda 1 (Pre-partido)", "Ronda 2 (Durante el partido)", "Apuestas Cerradas"])
            if st.button("Aplicar Cambio de Fase"):
                datos["estado_apuestas"] = nuevo_estado
                guardar_datos(datos)
                st.rerun()

            st.divider()
            # BOTÓN DE REINICIO
            if st.button("🚨 Reiniciar todas las apuestas (BORRAR TODO)"):
                datos_limpios = {
                    "estado_apuestas": "Ronda 1 (Pre-partido)",
                    "apuestas": {}
                }
                guardar_datos(datos_limpios)
                st.rerun()

    # --- ZONA DE APUESTAS ---
    if estado_actual == "Apuestas Cerradas":
        st.error("Las apuestas están cerradas. ¡A disfrutar el partido!")
    else:
        with st.form("formulario_apuesta"):
            st.write("Haz o ajusta tu jugada:")
            apuesta_previa = datos["apuestas"].get(usuario_1, {"jugador": "Tono", "tragos": 0})

            jugador_elegido = st.radio("¿A quién le vas?", ["Tono", "Franco"],
                                       index=0 if apuesta_previa["jugador"] == "Tono" else 1)

            tragos_apostados = st.slider(f"Tragos a apostar (Ronda actual: {estado_actual})",
                                         0, MAX_TRAGOS, apuesta_previa["tragos"])

            btn_apostar = st.form_submit_button("Confirmar Apuesta 🚀")

            if btn_apostar:
                datos["apuestas"][usuario_1] = {"jugador": jugador_elegido, "tragos": tragos_apostados}
                guardar_datos(datos)
                st.success("¡Apuesta registrada exitosamente!")

elif usuario_1 != "Selecciona..." and usuario_1 != usuario_2:
    st.error("⚠️ Los nombres no coinciden. Selecciona el mismo nombre en ambas listas.")

st.divider()

# --- CÁLCULO DE FACTORES Y TABLAS EN TIEMPO REAL ---
st.header("📊 Pizarra en Tiempo Real")

df_apuestas = pd.DataFrame([
    {"Nombre": nombre, "Jugador": info["jugador"], "Tragos Apostados": info["tragos"]}
    for nombre, info in datos["apuestas"].items() if info["tragos"] > 0
])

if not df_apuestas.empty:
    total_tono = df_apuestas[df_apuestas['Jugador'] == 'Tono']['Tragos Apostados'].sum()
    total_franco = df_apuestas[df_apuestas['Jugador'] == 'Franco']['Tragos Apostados'].sum()
    pozo_total = total_tono + total_franco

    st.caption(f"Tragos totales en juego: {pozo_total} (Tono: {total_tono} | Franco: {total_franco})")

    factor_tono = pozo_total / total_tono if total_tono > 0 else 1.0
    factor_franco = pozo_total / total_franco if total_franco > 0 else 1.0

    col_f1, col_f2 = st.columns(2)
    col_f1.metric("Factor Tono", f"{factor_tono:.2f}x")
    col_f2.metric("Factor Franco", f"{factor_franco:.2f}x")

    st.divider()
    st.subheader("🍻 ¿Qué pasa si termina el partido hoy?")

    df_resultados = df_apuestas.copy()


    def calcular_resultado(row, ganador, factor):
        if row['Jugador'] == ganador:
            ganancia_neta = int(round((row['Tragos Apostados'] * factor) - row['Tragos Apostados']))
            if ganancia_neta <= 0:
                return "No ganas nada (Nadie apostó en contra)"
            return f"🔥 ¡REGALAS {ganancia_neta} tragos!"
        else:
            return f"💀 BEBES {row['Tragos Apostados']} tragos"


    df_resultados["Si gana TONO"] = df_resultados.apply(lambda row: calcular_resultado(row, 'Tono', factor_tono),
                                                        axis=1)
    df_resultados["Si gana FRANCO"] = df_resultados.apply(lambda row: calcular_resultado(row, 'Franco', factor_franco),
                                                          axis=1)

    st.dataframe(df_resultados[["Nombre", "Jugador", "Tragos Apostados", "Si gana TONO", "Si gana FRANCO"]],
                 hide_index=True)
else:
    st.info("Aún no hay apuestas en la mesa.")