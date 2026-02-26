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
if col_btn.button("🔄 Actualizar Pizarra"):
    st.rerun()

st.markdown(f"### 📢 Estado: **{estado_actual}**")
st.markdown("💰 **Regla de oro:** 1 Piscola = 12 Tragos.")
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
            if st.button("🚨 Reiniciar todas las apuestas (BORRAR TODO)"):
                datos_limpios = {
                    "estado_apuestas": "Ronda 1 (Pre-partido)",
                    "apuestas": {}
                }
                guardar_datos(datos_limpios)
                st.rerun()

    # --- ZONA DE APUESTAS ---
    if estado_actual == "Apuestas Cerradas":
        st.error("Las apuestas están cerradas. ¡A rezar por esos tragos!")
    else:
        with st.form("formulario_apuesta"):
            st.write("Haz o ajusta tu jugada:")
            apuesta_previa = datos["apuestas"].get(usuario_1, {"jugador": "Tono", "tragos": 0})
            
            jugador_elegido = st.radio("¿A quién le vas?", ["Tono", "Franco"], 
                                       index=0 if apuesta_previa["jugador"] == "Tono" else 1)
            
            tragos_apostados = st.slider(f"Tragos a apostar (Máximo 1 piscola)", 
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

# Inicializar matemática de factores con pozo fantasma para arrancar en 1.5x
total_tono = 0
total_franco = 0

if not df_apuestas.empty:
    total_tono = df_apuestas[df_apuestas['Jugador'] == 'Tono']['Tragos Apostados'].sum()
    total_franco = df_apuestas[df_apuestas['Jugador'] == 'Franco']['Tragos Apostados'].sum()

# Fórmula fantasma: (Total Real + 30) / (Jugador Real + 20) = 1.5x cuando arranca de cero
pozo_calculo = total_tono + total_franco + 30
factor_tono = pozo_calculo / (total_tono + 20)
factor_franco = pozo_calculo / (total_franco + 20)

col_f1, col_f2 = st.columns(2)
col_f1.metric("Factor Tono", f"x{factor_tono:.2f}", f"Apostados: {total_tono} tragos")
col_f2.metric("Factor Franco", f"x{factor_franco:.2f}", f"Apostados: {total_franco} tragos")

st.divider()
st.subheader("🍻 El Día del Juicio (Proyecciones)")

if not df_apuestas.empty:
    df_resultados = df_apuestas.copy()
    
    # Función para dar formato a tragos y piscolas decimales
    def formatear_tragos(tragos_calculados):
        tragos = int(round(tragos_calculados))
        piscolas = round(tragos / 12, 1)
        return f"{tragos} tragos ({piscolas} pisc.)"

    # Regla: Si gana tu jugador, REGALAS tu apuesta x el factor. 
    # Si pierde tu jugador, BEBES tu apuesta x el factor del ganador.
    df_resultados["Si gana TONO"] = df_resultados.apply(
        lambda row: f"🔥 REGALAS {formatear_tragos(row['Tragos Apostados'] * factor_tono)}" 
        if row['Jugador'] == 'Tono' 
        else f"💀 BEBES {formatear_tragos(row['Tragos Apostados'] * factor_tono)}", axis=1
    )
    
    df_resultados["Si gana FRANCO"] = df_resultados.apply(
        lambda row: f"🔥 REGALAS {formatear_tragos(row['Tragos Apostados'] * factor_franco)}" 
        if row['Jugador'] == 'Franco' 
        else f"💀 BEBES {formatear_tragos(row['Tragos Apostados'] * factor_franco)}", axis=1
    )
    
    st.dataframe(df_resultados[["Nombre", "Jugador", "Tragos Apostados", "Si gana TONO", "Si gana FRANCO"]], hide_index=True)
else:
    st.info("Aún no hay apuestas en la mesa. ¡Rompan el hielo!")
