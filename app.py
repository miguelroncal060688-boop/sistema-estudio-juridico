import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="⚖️ Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

# =========================
# ARCHIVOS
# =========================

FILES = {
    "clientes": "clientes.csv",
    "abogados": "abogados.csv",
    "casos": "casos.csv",
    "honorarios": "honorarios.csv",
    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv"
}

# =========================
# CREAR CSV SI NO EXISTEN
# =========================

def init_csv():
    estructuras = {
        "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
        "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
        "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones"],
        "honorarios": ["Caso","Monto Pactado"],
        "pagos_honorarios": ["Caso","Monto"],
        "cuota_litis": ["Caso","Monto Base","Porcentaje"],
        "pagos_litis": ["Caso","Monto"]
    }

    for key, cols in estructuras.items():
        if not os.path.exists(FILES[key]):
            pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_csv()

# =========================
# USUARIOS
# =========================

if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "admin": {"password": "estudio123", "rol": "admin"}
    }

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# LOGIN
if st.session_state.usuario is None:
    st.title("⚖️ Estudio Jurídico Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")

    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in st.session_state.usuarios and st.session_state.usuarios[user]["password"] == pw:
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

st.sidebar.write(f"Usuario: {st.session_state.usuario}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

# =========================
# CARGAR DATA
# =========================

clientes = pd.read_csv(FILES["clientes"])
abogados = pd.read_csv(FILES["abogados"])
casos = pd.read_csv(FILES["casos"])
honorarios = pd.read_csv(FILES["honorarios"])
pagos_honorarios = pd.read_csv(FILES["pagos_honorarios"])
cuota_litis = pd.read_csv(FILES["cuota_litis"])
pagos_litis = pd.read_csv(FILES["pagos_litis"])

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox("Menú", [
    "Dashboard",
    "Clientes",
    "Abogados",
    "Casos",
    "Honorarios",
    "Pagos Honorarios",
    "Cuota Litis",
    "Pagos Cuota Litis",
    "Pendientes de Cobro",
    "Resumen Financiero",
    "Usuarios"
])

# =========================
# CALCULOS GENERALES
# =========================

total_pactado = honorarios["Monto Pactado"].sum()
total_pagado_h = pagos_honorarios["Monto"].sum()
total_pendiente_h = total_pactado - total_pagado_h

total_base = cuota_litis["Monto Base"].sum()
total_calculada = (cuota_litis["Monto Base"] * cuota_litis["Porcentaje"] / 100).sum()
total_pagado_l = pagos_litis["Monto"].sum()
total_pendiente_l = total_calculada - total_pagado_l

total_general_pendiente = total_pendiente_h + total_pendiente_l

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":
    st.title("Dashboard General")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Honorarios Pactados", f"S/ {total_pactado:,.2f}")
    col2.metric("Total Cobrado Honorarios", f"S/ {total_pagado_h:,.2f}")
    col3.metric("Pendiente Honorarios", f"S/ {total_pendiente_h:,.2f}")

    st.divider()

    col4, col5, col6 = st.columns(3)
    col4.metric("Cuota Litis Calculada", f"S/ {total_calculada:,.2f}")
    col5.metric("Cobrado Cuota Litis", f"S/ {total_pagado_l:,.2f}")
    col6.metric("Pendiente Cuota Litis", f"S/ {total_pendiente_l:,.2f}")

    st.divider()

    st.metric("TOTAL GENERAL PENDIENTE", f"S/ {total_general_pendiente:,.2f}")

# =========================
# PENDIENTES DE COBRO
# =========================

if menu == "Pendientes de Cobro":
    st.title("Pendientes de Cobro por Expediente")

    data = []

    for _, c in casos.iterrows():
        exp = c["Expediente"]

        pactado = honorarios[honorarios["Caso"] == exp]["Monto Pactado"].sum()
        pagado_h = pagos_honorarios[pagos_honorarios["Caso"] == exp]["Monto"].sum()
        pendiente_h = pactado - pagado_h

        base = cuota_litis[cuota_litis["Caso"] == exp]["Monto Base"].sum()
        porcentaje = cuota_litis[cuota_litis["Caso"] == exp]["Porcentaje"].sum()
        calculada = base * porcentaje / 100
        pagado_l = pagos_litis[pagos_litis["Caso"] == exp]["Monto"].sum()
        pendiente_l = calculada - pagado_l

        total_pend = pendiente_h + pendiente_l

        if total_pend > 0:
            data.append([exp, pendiente_h, pendiente_l, total_pend])

    df = pd.DataFrame(data, columns=[
        "Expediente",
        "Pendiente Honorarios",
        "Pendiente Cuota Litis",
        "Total Pendiente"
    ])

    st.dataframe(df)

    st.metric("TOTAL GENERAL PENDIENTE", f"S/ {df['Total Pendiente'].sum():,.2f}")
