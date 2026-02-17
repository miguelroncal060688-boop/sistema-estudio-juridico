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

    # Mostrar y editar/eliminar
    if not clientes.empty:
        st.subheader("Clientes registrados")
        for i in clientes.index:
            c = clientes.loc[i]
            st.write(f"{c['Nombre']} | DNI: {c['DNI']} | Celular: {c['Celular']}")
            col_edit, col_del = st.columns([1,1])
            if col_edit.button("Editar",key=f"edit_c{i}"):
                st.session_state.edit_cliente = i
            if col_del.button("Eliminar",key=f"del_c{i}"):
                clientes.drop(i,inplace=True)
                clientes.reset_index(drop=True,inplace=True)
                guardar_csv(clientes,"clientes.csv")
                st.rerun()

    # Editar cliente
    if "edit_cliente" in st.session_state:
        i = st.session_state.edit_cliente
        c = clientes.loc[i]
        st.subheader(f"Editar Cliente: {c['Nombre']}")
        nombre_e = st.text_input("Nombre completo",c['Nombre'])
        dni_e = st.text_input("DNI",c['DNI'])
        celular_e = st.text_input("Celular",c['Celular'])
        correo_e = st.text_input("Correo",c['Correo'])
        direccion_e = st.text_input("Dirección",c['Dirección'])
        if st.button("Guardar Cambios Cliente"):
            clientes.loc[i] = [nombre_e,dni_e,celular_e,correo_e,direccion_e]
            guardar_csv(clientes,"clientes.csv")
            del st.session_state.edit_cliente
            st.rerun()

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
        st.subheader("Casos registrados")
        for i in casos.index:
            c = casos.loc[i]
            st.write(f"{c['Cliente']} | {c['ID_CASO']} | S/ {c['Monto']}")
            col_edit, col_del = st.columns([1,1])
            if col_edit.button("Editar",key=f"edit_case{i}"):
                st.session_state.edit_caso = i
            if col_del.button("Eliminar",key=f"del_case{i}"):
                casos.drop(i,inplace=True)
                casos.reset_index(drop=True,inplace=True)
                guardar_csv(casos,"casos.csv")
                st.rerun()

    # Editar caso
    if "edit_caso" in st.session_state:
        i = st.session_state.edit_caso
        c = casos.loc[i]
        st.subheader(f"Editar Caso: {c['ID_CASO']}")
        expediente_e = st.text_input("Número de expediente",c['Expediente'])
        año_e = st.text_input("Año",c['Año'])
        cliente_e = st.selectbox("Cliente", clientes["Nombre"], index=clientes[clientes["Nombre"]==c['Cliente']].index[0])
        materia_e = st.text_input("Materia",c['Materia'])
        monto_e = st.number_input("Monto pactado",c['Monto'])
        cuota_litis_e = st.number_input("Cuota Litis (%)",c['Cuota_Litis'])
        monot_base_e = st.number_input("Monto Base",c['Monot_Base'])
        if st.button("Guardar Cambios Caso"):
            casos.loc[i] = [f"{expediente_e}-{año_e}-{cliente_e}",cliente_e,expediente_e,año_e,materia_e,monto_e,cuota_litis_e,monot_base_e]
            guardar_csv(casos,"casos.csv")
            del st.session_state.edit_caso
            st.rerun()

# ================= PAGOS =================
if menu == "Pagos":
    st.title("Registro de Pagos")

    caso_sel = st.selectbox("Caso", casos["ID_CASO"] if not casos.empty else [])
    cliente_sel = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
    fecha = st.date_input("Fecha")
    monto_pago = st.number_input("Monto pagado",0.0)

    if st.button("Registrar Pago"):
        nuevo = pd.DataFrame([{
            "ID_CASO":caso_sel,
            "Cliente":cliente_sel,
            "Fecha":fecha,
            "Monto":monto_pago
        }])
        pagos = pd.concat([pagos,nuevo],ignore_index=True)
        guardar_csv(pagos,"pagos.csv")
        st.rerun()

    if not pagos.empty:
        st.subheader("Pagos registrados")
        for i in pagos.index:
            p = pagos.loc[i]
            st.write(f"{p['Cliente']} | {p['ID_CASO']} | S/ {p['Monto']} | {p['Fecha']}")
            col_del = st.columns([1])
            if st.button("Eliminar",key=f"del_pago{i}"):
                pagos.drop(i,inplace=True)
                pagos.reset_index(drop=True,inplace=True)
                guardar_csv(pagos,"pagos.csv")
                st.rerun()

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

    st.subheader("Saldos por Caso")
    st.dataframe(df_saldo[["ID_CASO","Cliente","Monto","Pagado","Saldo"]])
