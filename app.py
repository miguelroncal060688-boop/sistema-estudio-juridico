import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sistema Jurídico PRO", layout="wide")

# ================= LOGIN =================
PASSWORD = "estudio123"

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("Acceso al Sistema Jurídico")
    pwd = st.text_input("Ingrese contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == PASSWORD:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# ================= FUNCIONES =================
def cargar_csv(nombre):
    if os.path.exists(nombre):
        return pd.read_csv(nombre)
    return pd.DataFrame()

def guardar_csv(df, nombre):
    df.to_csv(nombre, index=False)

clientes = cargar_csv("clientes.csv")
casos = cargar_csv("casos.csv")
pagos = cargar_csv("pagos.csv")

menu = st.sidebar.selectbox("Menú", ["Dashboard","Clientes","Casos","Pagos","Contrato"])

# ================= CLIENTES =================
if menu == "Clientes":
    st.title("Gestión de Clientes")
    nombre = st.text_input("Nombre completo")
    dni = st.text_input("DNI")
    celular = st.text_input("Celular")
    correo = st.text_input("Correo")
    direccion = st.text_input("Dirección")

    if st.button("Guardar Cliente"):
        nuevo = pd.DataFrame([{
            "Nombre": nombre,
            "DNI": dni,
            "Celular": celular,
            "Correo": correo,
            "Dirección": direccion
        }])
        clientes = pd.concat([clientes, nuevo], ignore_index=True)
        guardar_csv(clientes,"clientes.csv")
        st.rerun()

    if not clientes.empty:
        st.dataframe(clientes)

# ================= CASOS =================
if menu == "Casos":
    st.title("Gestión de Casos")
    cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
    expediente = st.text_input("Número de expediente")
    año = st.text_input("Año")
    materia = st.text_input("Materia")
    monto = st.number_input("Monto pactado",0.0)
    cuota_litis = st.number_input("Cuota Litis (%)",0.0)
    monot_base = st.number_input("Monto Base",0.0)

    if st.button("Guardar Caso"):
        identificador = f"{expediente}-{año}-{cliente}"
        nuevo = pd.DataFrame([{
            "ID_CASO": identificador,
            "Cliente":cliente,
            "Expediente":expediente,
            "Año":año,
            "Materia":materia,
            "Monto":monto,
            "Cuota_Litis":cuota_litis,
            "Monot_Base":monot_base
        }])
        casos = pd.concat([casos,nuevo],ignore_index=True)
        guardar_csv(casos,"casos.csv")
        st.rerun()

    if not casos.empty:
        st.dataframe(casos)

# ================= PAGOS =================
if menu == "Pagos":
    st.title("Registro de Pagos")
    caso = st.selectbox("Caso", casos["ID_CASO"] if not casos.empty else [])
    fecha = st.date_input("Fecha")
    monto_pago = st.number_input("Monto pagado",0.0)

    if st.button("Registrar Pago"):
        nuevo = pd.DataFrame([{
            "ID_CASO":caso,
            "Fecha":fecha,
            "Monto":monto_pago
        }])
        pagos = pd.concat([pagos,nuevo],ignore_index=True)
        guardar_csv(pagos,"pagos.csv")
        st.rerun()

    if not pagos.empty:
        st.dataframe(pagos)

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("Dashboard Financiero")
    total_clientes = len(clientes)
    total_casos = len(casos)
    total_ingresos = pagos["Monto"].sum() if not pagos.empty else 0
    total_pendiente = 0
    if not casos.empty:
        for i in casos.index:
            id_caso = casos.loc[i,"ID_CASO"]
            total_pagado = pagos[pagos["ID_CASO"]==id_caso]["Monto"].sum() if not pagos.empty else 0
            total_pendiente += casos.loc[i,"Monto"] - total_pagado
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_ingresos}")
    col4.metric("Pendiente", f"S/ {total_pendiente}")

# ================= CONTRATO =================
if menu == "Contrato":
    st.title("Generar Contrato")
    caso = st.selectbox("Caso", casos["ID_CASO"] if not casos.empty else [])
    contraparte = st.text_input("Contraparte")
    if caso:
        c = casos[casos["ID_CASO"]==caso].iloc[0]
        contrato_text = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS

Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en el Psje. Victoria N° 280 – Barrio San Martín, a quien en adelante se denominará EL LOCADOR; y, de la otra parte, {contraparte}, a quien en adelante se denominará EL CLIENTE.

EXPEDIENTE: {c['Expediente']} - AÑO: {c['Año']}
MONTO PACTADO: S/ {c['Monto']}
CUOTA LITIS: {c['Cuota_Litis']}%
MONTO BASE: S/ {c['Monot_Base']}

Firmado a los {datetime.today().day} días del mes de {datetime.today().strftime('%B')} del año {datetime.today().year}.
        """
        st.text_area("Contrato Generado",contrato_text,height=500)
