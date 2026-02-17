import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

st.title("Sistema de Gestión - Estudio Jurídico Roncal Liñán y Asociados")

menu = st.sidebar.selectbox("Menú", ["Clientes", "Casos", "Pagos", "Contrato"])

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=["Nombre", "DNI", "Celular", "Correo", "Dirección"])

if "casos" not in st.session_state:
    st.session_state.casos = pd.DataFrame(columns=["Cliente", "Materia", "Expediente", "Año", "Pretensión", "Monto Pactado"])

if "pagos" not in st.session_state:
    st.session_state.pagos = pd.DataFrame(columns=["Cliente", "Fecha", "Monto"])

# ---------------- CLIENTES ----------------
if menu == "Clientes":
    st.subheader("Registrar Cliente")

    nombre = st.text_input("Nombre completo")
    dni = st.text_input("DNI")
    celular = st.text_input("Celular")
    correo = st.text_input("Correo")
    direccion = st.text_input("Dirección")

    if st.button("Guardar Cliente"):
        nuevo = pd.DataFrame([[nombre, dni, celular, correo, direccion]],
                             columns=st.session_state.clientes.columns)
        st.session_state.clientes = pd.concat([st.session_state.clientes, nuevo], ignore_index=True)
        st.success("Cliente registrado")

    st.dataframe(st.session_state.clientes)

# ---------------- CASOS ----------------
if menu == "Casos":
    st.subheader("Registrar Caso")

    cliente = st.selectbox("Cliente", st.session_state.clientes["Nombre"])
    materia = st.text_input("Materia")
    expediente = st.text_input("Número de Expediente")
    año = st.text_input("Año")
    pretension = st.text_area("Pretensión")
    monto = st.number_input("Monto Pactado", min_value=0.0)

    if st.button("Guardar Caso"):
        nuevo = pd.DataFrame([[cliente, materia, expediente, año, pretension, monto]],
                             columns=st.session_state.casos.columns)
        st.session_state.casos = pd.concat([st.session_state.casos, nuevo], ignore_index=True)
        st.success("Caso registrado")

    st.dataframe(st.session_state.casos)

# ---------------- PAGOS ----------------
if menu == "Pagos":
    st.subheader("Registrar Pago")

    cliente = st.selectbox("Cliente ", st.session_state.clientes["Nombre"])
    fecha = st.date_input("Fecha", date.today())
    monto = st.number_input("Monto Pagado", min_value=0.0)

    if st.button("Guardar Pago"):
        nuevo = pd.DataFrame([[cliente, fecha, monto]],
                             columns=st.session_state.pagos.columns)
        st.session_state.pagos = pd.concat([st.session_state.pagos, nuevo], ignore_index=True)
        st.success("Pago registrado")

    st.dataframe(st.session_state.pagos)

# ---------------- CONTRATO ----------------
if menu == "Contrato":
    st.subheader("Generar Contrato")

    cliente = st.selectbox("Seleccionar Cliente", st.session_state.clientes["Nombre"])
    caso = st.selectbox("Seleccionar Expediente", st.session_state.casos["Expediente"])

    contrato = f"""
    CONTRATO DE PRESTACIÓN DE SERVICIOS LEGALES

    Cliente: {cliente}
    Expediente: {caso}

    El abogado Miguel Roncal Liñán se obliga a prestar servicios legales
    conforme a los términos pactados.

    Honorarios según acuerdo contractual.
    """

    st.text_area("Contrato generado", contrato, height=300)
