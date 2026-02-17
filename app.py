import streamlit as st
import pandas as pd
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Table
from reportlab.lib.units import inch

st.set_page_config(page_title="Sistema Jurídico PRO", layout="wide")

# =========================
# LOGIN SIMPLE
# =========================

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

# =========================
# FUNCIONES CSV
# =========================

def cargar_csv(nombre):
    if os.path.exists(nombre):
        return pd.read_csv(nombre)
    return pd.DataFrame()

def guardar_csv(df, nombre):
    df.to_csv(nombre, index=False)

clientes = cargar_csv("clientes.csv")
casos = cargar_csv("casos.csv")
pagos = cargar_csv("pagos.csv")

menu = st.sidebar.selectbox("Menú", ["Dashboard","Clientes","Casos","Pagos","Contrato","Reporte Excel"])

# =========================
# CLIENTES
# =========================

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
        st.success("Cliente guardado")
        st.rerun()

    st.subheader("Lista")
    if not clientes.empty:
        for i in clientes.index:
            col1,col2 = st.columns([4,1])
            col1.write(f"{clientes.loc[i,'Nombre']} | DNI: {clientes.loc[i,'DNI']}")
            if col2.button("Eliminar", key=f"cli{i}"):
                clientes = clientes.drop(i).reset_index(drop=True)
                guardar_csv(clientes,"clientes.csv")
                st.rerun()

# =========================
# CASOS
# =========================

if menu == "Casos":
    st.title("Gestión de Casos")

    cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
    materia = st.text_input("Materia")
    expediente = st.text_input("Expediente")
    año = st.text_input("Año")
    monto = st.number_input("Monto pactado",0.0)
    porcentaje = st.number_input("Cuota litis (%)",0.0)
    etapa = st.text_input("Etapa procesal")
    abogado = st.text_input("Abogado a cargo")

    if st.button("Guardar Caso"):
        nuevo = pd.DataFrame([{
            "Cliente":cliente,
            "Materia":materia,
            "Expediente":expediente,
            "Año":año,
            "Monto":monto,
            "Porcentaje":porcentaje,
            "Etapa":etapa,
            "Abogado":abogado
        }])
        casos = pd.concat([casos,nuevo],ignore_index=True)
        guardar_csv(casos,"casos.csv")
        st.rerun()

    if not casos.empty:
        for i in casos.index:
            exp = casos.loc[i,"Expediente"]
            total_pagado = pagos[pagos["Expediente"]==exp]["Monto"].sum() if not pagos.empty else 0
            saldo = casos.loc[i,"Monto"] - total_pagado
            col1,col2 = st.columns([5,1])
            col1.write(f"{casos.loc[i,'Cliente']} | Exp:{exp} | Saldo:S/ {saldo}")
            if col2.button("Eliminar", key=f"cas{i}"):
                casos = casos.drop(i).reset_index(drop=True)
                guardar_csv(casos,"casos.csv")
                st.rerun()

# =========================
# PAGOS
# =========================

if menu == "Pagos":
    st.title("Registro de Pagos")

    caso = st.selectbox("Caso", casos["Expediente"] if not casos.empty else [])
    fecha = st.date_input("Fecha")
    monto_pago = st.number_input("Monto pagado",0.0)

    if st.button("Registrar Pago"):
        nuevo = pd.DataFrame([{
            "Expediente":caso,
            "Fecha":fecha,
            "Monto":monto_pago
        }])
        pagos = pd.concat([pagos,nuevo],ignore_index=True)
        guardar_csv(pagos,"pagos.csv")
        st.rerun()

    if not pagos.empty:
        st.dataframe(pagos)

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":
    st.title("Dashboard Financiero")

    total_clientes = len(clientes)
    total_casos = len(casos)
    total_ingresos = pagos["Monto"].sum() if not pagos.empty else 0

    total_pendiente = 0
    if not casos.empty:
        for i in casos.index:
            exp = casos.loc[i,"Expediente"]
            total_pagado = pagos[pagos["Expediente"]==exp]["Monto"].sum() if not pagos.empty else 0
            total_pendiente += casos.loc[i,"Monto"] - total_pagado

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_ingresos}")
    col4.metric("Pendiente", f"S/ {total_pendiente}")

# =========================
# CONTRATO PDF
# =========================

if menu == "Contrato":
    st.title("Generar Contrato PDF")

    cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
    caso = st.selectbox("Caso", casos["Expediente"] if not casos.empty else [])

    if st.button("Generar PDF"):
        archivo = f"Contrato_{cliente}.pdf"
        doc = SimpleDocTemplate(archivo,pagesize=A4)
        elementos = []

        estilos = getSampleStyleSheet()
        estilo_normal = estilos["Normal"]

        texto = f"""
        CONTRATO DE PRESTACIÓN DE SERVICIOS LEGALES

        Cliente: {cliente}
        Expediente: {caso}

        El presente contrato regula la prestación de servicios legales,
        conforme a los honorarios pactados entre las partes.

        Fecha: {datetime.today().strftime("%d/%m/%Y")}
        """

        elementos.append(Paragraph(texto, estilo_normal))
        elementos.append(Spacer(1,0.5*inch))

        doc.build(elementos)

        with open(archivo,"rb") as f:
            st.download_button("Descargar Contrato PDF",f,archivo)

# =========================
# REPORTE EXCEL
# =========================

if menu == "Reporte Excel":
    st.title("Exportar Reporte Financiero")

    archivo = "reporte_financiero.xlsx"
    with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
        clientes.to_excel(writer, sheet_name="Clientes", index=False)
        casos.to_excel(writer, sheet_name="Casos", index=False)
        pagos.to_excel(writer, sheet_name="Pagos", index=False)

    with open(archivo,"rb") as f:
        st.download_button("Descargar Reporte Excel",f,archivo)
