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

menu = st.sidebar.selectbox("Menú", ["Dashboard","Clientes","Casos","Pagos"])

# ================= CLIENTES =================
if menu == "Clientes":
    st.title("Gestión de Clientes")

    # Crear cliente
    nombre = st.text_input("Nombre completo", key="new_cliente_nombre")
    dni = st.text_input("DNI", key="new_cliente_dni")
    celular = st.text_input("Celular", key="new_cliente_cel")
    correo = st.text_input("Correo", key="new_cliente_email")
    direccion = st.text_input("Dirección", key="new_cliente_dir")
    if st.button("Guardar Cliente", key="guardar_cliente"):
        nuevo = pd.DataFrame([{
            "Nombre": nombre,
            "DNI": dni,
            "Celular": celular,
            "Correo": correo,
            "Dirección": direccion
        }])
        clientes = pd.concat([clientes, nuevo], ignore_index=True)
        guardar_csv(clientes,"clientes.csv")
        st.success("Cliente agregado")
        st.experimental_rerun()

    # Mostrar y editar/eliminar
    if not clientes.empty:
        st.subheader("Clientes registrados")
        for i, c in clientes.iterrows():
            cols = st.columns([3,1,1])
            cols[0].write(f"{c['Nombre']} | DNI: {c['DNI']} | Celular: {c['Celular']}")
            if cols[1].button("Editar", key=f"edit_cliente_{i}"):
                st.session_state.edit_cliente = i
            if cols[2].button("Eliminar", key=f"del_cliente_{i}"):
                clientes.drop(i, inplace=True)
                clientes.reset_index(drop=True, inplace=True)
                guardar_csv(clientes,"clientes.csv")
                st.experimental_rerun()

    # Editar cliente
    if "edit_cliente" in st.session_state:
        i = st.session_state.edit_cliente
        c = clientes.loc[i]
        st.subheader(f"Editar Cliente: {c['Nombre']}")
        nombre_e = st.text_input("Nombre completo", c['Nombre'], key="edit_cliente_nombre")
        dni_e = st.text_input("DNI", c['DNI'], key="edit_cliente_dni")
        celular_e = st.text_input("Celular", c['Celular'], key="edit_cliente_cel")
        correo_e = st.text_input("Correo", c['Correo'], key="edit_cliente_email")
        direccion_e = st.text_input("Dirección", c['Dirección'], key="edit_cliente_dir")
        if st.button("Guardar Cambios Cliente", key="save_cliente"):
            clientes.loc[i] = [nombre_e,dni_e,celular_e,correo_e,direccion_e]
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente actualizado")
            del st.session_state.edit_cliente
            st.experimental_rerun()

# ================= CASOS =================
if menu == "Casos":
    st.title("Gestión de Casos")

    cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [], key="new_case_cliente")
    expediente = st.text_input("Número de expediente", key="new_case_expediente")
    año = st.text_input("Año", key="new_case_year")
    materia = st.text_input("Materia", key="new_case_materia")
    monto = st.number_input("Monto pactado", 0.0, key="new_case_monto")
    cuota_litis = st.number_input("Cuota Litis (%)", 0.0, key="new_case_cuota")
    monot_base = st.number_input("Monto Base", 0.0, key="new_case_base")
    contraparte = st.text_input("Contraparte", key="new_case_contraparte")

    if st.button("Guardar Caso", key="guardar_caso"):
        identificador = f"{expediente}-{año}-{cliente}"
        nuevo = pd.DataFrame([{
            "ID_CASO": identificador,
            "Cliente": cliente,
            "Expediente": expediente,
            "Año": año,
            "Materia": materia,
            "Monto": monto,
            "Cuota_Litis": cuota_litis,
            "Monot_Base": monot_base,
            "Contraparte": contraparte
        }])
        casos = pd.concat([casos,nuevo],ignore_index=True)
        guardar_csv(casos,"casos.csv")
        st.success("Caso agregado")
        st.experimental_rerun()

    # Mostrar casos
    if not casos.empty:
        st.subheader("Casos registrados")
        for i, c in casos.iterrows():
            cols = st.columns([3,1,1])
            cols[0].write(f"{c['Cliente']} | {c['ID_CASO']} | S/ {c['Monto']} | Contraparte: {c['Contraparte']}")
            if cols[1].button("Editar", key=f"edit_caso_{i}"):
                st.session_state.edit_caso = i
            if cols[2].button("Eliminar", key=f"del_caso_{i}"):
                casos.drop(i, inplace=True)
                casos.reset_index(drop=True, inplace=True)
                guardar_csv(casos,"casos.csv")
                st.experimental_rerun()

    # Editar caso
    if "edit_caso" in st.session_state:
        i = st.session_state.edit_caso
        c = casos.loc[i]
        st.subheader(f"Editar Caso: {c['ID_CASO']}")
        expediente_e = st.text_input("Número de expediente", c['Expediente'], key="edit_case_exp")
        año_e = st.text_input("Año", c['Año'], key="edit_case_year")
        cliente_e = st.selectbox("Cliente", clientes["Nombre"], index=clientes[clientes["Nombre"]==c['Cliente']].index[0], key="edit_case_cliente")
        materia_e = st.text_input("Materia", c['Materia'], key="edit_case_materia")
        monto_e = st.number_input("Monto pactado", c['Monto'], key="edit_case_monto")
        cuota_litis_e = st.number_input("Cuota Litis (%)", c['Cuota_Litis'], key="edit_case_cuota")
        monot_base_e = st.number_input("Monto Base", c['Monot_Base'], key="edit_case_base")
        contraparte_e = st.text_input("Contraparte", c['Contraparte'], key="edit_case_contraparte")
        if st.button("Guardar Cambios Caso", key="save_case"):
            casos.loc[i] = [f"{expediente_e}-{año_e}-{cliente_e}", cliente_e, expediente_e, año_e, materia_e, monto_e, cuota_litis_e, monot_base_e, contraparte_e]
            guardar_csv(casos,"casos.csv")
            st.success("Caso actualizado")
            del st.session_state.edit_caso
            st.experimental_rerun()

# ================= PAGOS =================
if menu == "Pagos":
    st.title("Registro de Pagos")

    if not casos.empty and not clientes.empty:
        caso_sel = st.selectbox("Caso", casos["ID_CASO"], key="pago_caso")
        cliente_sel = st.selectbox("Cliente", clientes["Nombre"], key="pago_cliente")
        fecha = st.date_input("Fecha", key="pago_fecha")
        monto_pago = st.number_input("Monto pagado",0.0, key="pago_monto")

        if st.button("Registrar Pago", key="guardar_pago"):
            nuevo = pd.DataFrame([{
                "ID_CASO": caso_sel,
                "Cliente": cliente_sel,
                "Fecha": fecha,
                "Monto": monto_pago
            }])
            pagos = pd.concat([pagos,nuevo], ignore_index=True)
            guardar_csv(pagos,"pagos.csv")
            st.success("Pago registrado")
            st.experimental_rerun()

    if not pagos.empty:
        st.subheader("Pagos registrados")
        for i, p in pagos.iterrows():
            cols = st.columns([3,1])
            cols[0].write(f"{p['Cliente']} | {p['ID_CASO']} | S/ {p['Monto']} | {p['Fecha']}")
            if cols[1].button("Eliminar", key=f"del_pago_{i}"):
                pagos.drop(i, inplace=True)
                pagos.reset_index(drop=True, inplace=True)
                guardar_csv(pagos,"pagos.csv")
                st.experimental_rerun()

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("Dashboard Financiero")

    total_clientes = len(clientes)
    total_casos = len(casos)
    total_ingresos = pagos["Monto"].sum() if not pagos.empty else 0

    # Saldo pendiente por caso
    df_saldo = casos.copy()
    df_saldo["Pagado"] = df_saldo["ID_CASO"].apply(lambda x: pagos[pagos["ID_CASO"]==x]["Monto"].sum() if not pagos.empty else 0)
    df_saldo["Saldo"] = df_saldo["Monto"] - df_saldo["Pagado"]
    total_pendiente = df_saldo["Saldo"].sum() if not df_saldo.empty else 0

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_ingresos}")
    col4.metric("Pendiente", f"S/ {total_pendiente}")

    st.subheader("Seguimiento de Pagos por Caso")
    st.dataframe(df_saldo[["ID_CASO","Cliente","Contraparte","Monto","Pagado","Saldo"]])
