import streamlit as st
import pandas as pd
import os
from datetime import date
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados", layout="wide")
st.title("Sistema de Gestión – Estudio Jurídico Roncal Liñán y Asociados")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def load_data(name, columns):
    path = os.path.join(DATA_DIR, f"{name}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df, name):
    path = os.path.join(DATA_DIR, f"{name}.csv")
    df.to_csv(path, index=False)

# ---------------- CARGA ----------------
clientes_cols = ["ID","Nombre","DNI","Celular","Correo","Direccion","Contacto_Emergencia","Celular_Emergencia","Observaciones"]
casos_cols = ["ID","Cliente_ID","Materia","Expediente","Año","Distrito","Juzgado","Pretension","Etapa","Abogado","Riesgo"]
honorarios_cols = ["Caso_ID","Tipo","Monto_Pactado","Porcentaje_Cuota_Litis"]
pagos_cols = ["Caso_ID","Fecha","Monto"]

clientes = load_data("clientes", clientes_cols)
casos = load_data("casos", casos_cols)
honorarios = load_data("honorarios", honorarios_cols)
pagos = load_data("pagos", pagos_cols)

menu = st.sidebar.selectbox("Menú", ["Dashboard","Clientes","Casos","Honorarios","Pagos","Contrato"])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.subheader("Resumen General")

    total_clientes = len(clientes)
    total_casos = len(casos)
    total_pagado = pagos["Monto"].sum() if not pagos.empty else 0
    total_pactado = honorarios["Monto_Pactado"].sum() if not honorarios.empty else 0
    saldo = total_pactado - total_pagado

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_pagado:,.2f}")
    col4.metric("Saldo pendiente", f"S/ {saldo:,.2f}")

# ---------------- CLIENTES ----------------
if menu == "Clientes":
    st.subheader("Registrar Cliente")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        contacto = st.text_input("Contacto de emergencia")
        cel_em = st.text_input("Celular emergencia")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")

    if submit:
        nuevo = pd.DataFrame([[len(clientes)+1,nombre,dni,celular,correo,direccion,contacto,cel_em,obs]],
                             columns=clientes_cols)
        clientes = pd.concat([clientes,nuevo],ignore_index=True)
        save_data(clientes,"clientes")
        st.success("Cliente guardado")

    st.dataframe(clientes)

# ---------------- CASOS ----------------
if menu == "Casos":
    st.subheader("Registrar Caso")

    if clientes.empty:
        st.warning("Primero registra un cliente")
    else:
        with st.form("form_caso"):
            cliente = st.selectbox("Cliente", clientes["Nombre"])
            materia = st.text_input("Materia")
            expediente = st.text_input("Número de expediente")
            año = st.text_input("Año")
            distrito = st.text_input("Distrito Judicial")
            juzgado = st.text_input("Juzgado")
            pretension = st.text_area("Pretensión")
            etapa = st.selectbox("Etapa procesal", ["Postulatoria","Probatoria","Decisión","Apelación","Casación","Ejecución"])
            abogado = st.text_input("Abogado a cargo", value="Miguel Roncal Liñán")
            riesgo = st.selectbox("Riesgo", ["Bajo","Medio","Alto"])
            submit = st.form_submit_button("Guardar")

        if submit:
            cliente_id = clientes[clientes["Nombre"]==cliente]["ID"].values[0]
            nuevo = pd.DataFrame([[len(casos)+1,cliente_id,materia,expediente,año,distrito,juzgado,pretension,etapa,abogado,riesgo]],
                                 columns=casos_cols)
            casos = pd.concat([casos,nuevo],ignore_index=True)
            save_data(casos,"casos")
            st.success("Caso guardado")

    st.dataframe(casos)

# ---------------- HONORARIOS ----------------
if menu == "Honorarios":
    st.subheader("Registrar Honorarios")

    if casos.empty:
        st.warning("Primero registra un caso")
    else:
        with st.form("form_honorarios"):
            caso = st.selectbox("Caso", casos["ID"])
            tipo = st.selectbox("Tipo", ["Fijo","Cuota Litis","Mixto"])
            monto = st.number_input("Monto pactado", min_value=0.0)
            porcentaje = st.number_input("Porcentaje cuota litis", min_value=0.0)
            submit = st.form_submit_button("Guardar")

        if submit:
            nuevo = pd.DataFrame([[caso,tipo,monto,porcentaje]],
                                 columns=honorarios_cols)
            honorarios = pd.concat([honorarios,nuevo],ignore_index=True)
            save_data(honorarios,"honorarios")
            st.success("Honorarios guardados")

    st.dataframe(honorarios)

# ---------------- PAGOS ----------------
if menu == "Pagos":
    st.subheader("Registrar Pago")

    if casos.empty:
        st.warning("Primero registra un caso")
    else:
        with st.form("form_pago"):
            caso = st.selectbox("Caso", casos["ID"])
            fecha = st.date_input("Fecha", date.today())
            monto = st.number_input("Monto", min_value=0.0)
            submit = st.form_submit_button("Guardar")

        if submit:
            nuevo = pd.DataFrame([[caso,fecha,monto]],
                                 columns=pagos_cols)
            pagos = pd.concat([pagos,nuevo],ignore_index=True)
            save_data(pagos,"pagos")
            st.success("Pago registrado")

    st.dataframe(pagos)

# ---------------- CONTRATO PDF ----------------
if menu == "Contrato":
    st.subheader("Generar Contrato en PDF")

    if casos.empty:
        st.warning("No hay casos registrados")
    else:
        caso_id = st.selectbox("Seleccionar Caso", casos["ID"])
        caso = casos[casos["ID"]==caso_id].iloc[0]
        cliente = clientes[clientes["ID"]==caso["Cliente_ID"]].iloc[0]

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        style = styles["Normal"]

        texto = f"""
        CONTRATO DE PRESTACIÓN DE SERVICIOS LEGALES

        Cliente: {cliente['Nombre']} - DNI: {cliente['DNI']}
        Expediente: {caso['Expediente']} - Año {caso['Año']}

        PRIMERA: Objeto del contrato.
        Defensa legal en proceso sobre {caso['Materia']}.

        SEGUNDA: Honorarios conforme acuerdo pactado.

        TERCERA: Gastos judiciales asumidos por el cliente.

        CUARTA: Penalidad por mora según interés legal.

        QUINTA: Protección de datos personales conforme normativa vigente.

        Firmado en señal de conformidad.
        """

        elements.append(Paragraph(texto.replace("\n","<br/>"), style))
        doc.build(elements)

        st.download_button(
            "Descargar Contrato PDF",
            buffer.getvalue(),
