import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

st.title("⚖️ ESTUDIO JURÍDICO RONCAL LIÑÁN Y ASOCIADOS")

# =====================================================
# CONFIG ARCHIVOS
# =====================================================

FILES = {
    "clientes": "clientes.csv",
    "abogados": "abogados.csv",
    "casos": "casos.csv",
    "honorarios": "honorarios.csv",
    "pagos": "pagos.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",
    "cronograma": "cronograma.csv",
    "usuarios": "usuarios.csv"
}

# =====================================================
# CREAR ARCHIVOS LIMPIOS
# =====================================================

def create_if_not_exists():
    estructuras = {
        "clientes": ["ID","Nombre","DNI","Telefono","Correo"],
        "abogados": ["ID","Nombre","Colegiatura","Correo"],
        "casos": ["ID","ClienteID","AbogadoID","Expediente","Año","Materia"],
        "honorarios": ["ID","CasoID","MontoPactado"],
        "pagos": ["ID","CasoID","Monto","Fecha"],
        "cuota_litis": ["ID","CasoID","MontoBase","Porcentaje"],
        "pagos_litis": ["ID","CasoID","Monto","Fecha"],
        "cronograma": ["ID","CasoID","Fecha","Monto","Estado"],
        "usuarios": ["ID","Usuario","Password","Rol","AbogadoID"]
    }

    for k,v in estructuras.items():
        if not os.path.exists(FILES[k]):
            pd.DataFrame(columns=v).to_csv(FILES[k], index=False)

create_if_not_exists()

def load(name):
    return pd.read_csv(FILES[name])

def save(name, df):
    df.to_csv(FILES[name], index=False)

def next_id(df):
    return int(df["ID"].max()+1) if not df.empty else 1

clientes = load("clientes")
abogados = load("abogados")
casos = load("casos")
honorarios = load("honorarios")
pagos = load("pagos")
cuota_litis = load("cuota_litis")
pagos_litis = load("pagos_litis")
cronograma = load("cronograma")
usuarios = load("usuarios")

# =====================================================
# ADMIN POR DEFECTO
# =====================================================

if usuarios.empty:
    usuarios.loc[0] = [1,"admin","estudio123","admin",""]
    save("usuarios", usuarios)
    usuarios = load("usuarios")

# =====================================================
# LOGIN
# =====================================================

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.rol = None
    st.session_state.abogado_id = None

if st.session_state.user is None:
    st.subheader("Ingreso al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        fila = usuarios[(usuarios.Usuario==u)&(usuarios.Password==p)]
        if not fila.empty:
            st.session_state.user = u
            st.session_state.rol = fila.iloc[0]["Rol"]
            st.session_state.abogado_id = fila.iloc[0]["AbogadoID"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.write(f"Usuario: {st.session_state.user}")
st.sidebar.write(f"Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

menu = st.sidebar.selectbox("Menú", [
    "Dashboard","Clientes","Abogados","Casos",
    "Honorarios","Pagos","Cuota Litis",
    "Pendientes","Resumen Financiero","Reporte Cliente"
])

# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":

    total_pactado = honorarios["MontoPactado"].sum()
    total_pagado = pagos["Monto"].sum()
    pendiente = total_pactado - total_pagado

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Pactado", f"S/ {total_pactado:,.2f}")
    col2.metric("Total Cobrado", f"S/ {total_pagado:,.2f}")
    col3.metric("Pendiente", f"S/ {pendiente:,.2f}")

# =====================================================
# CLIENTES
# =====================================================

if menu == "Clientes":
    st.subheader("Registrar Cliente")
    nombre = st.text_input("Nombre")
    dni = st.text_input("DNI")
    telefono = st.text_input("Teléfono")
    correo = st.text_input("Correo")

    if st.button("Guardar Cliente"):
        nuevo = next_id(clientes)
        clientes.loc[len(clientes)] = [nuevo,nombre,dni,telefono,correo]
        save("clientes", clientes)
        st.success("Cliente guardado")
        st.rerun()

    st.dataframe(clientes)

# =====================================================
# ABOGADOS
# =====================================================

if menu == "Abogados":
    st.subheader("Registrar Abogado")
    nombre = st.text_input("Nombre")
    col = st.text_input("Colegiatura")
    correo = st.text_input("Correo")

    if st.button("Guardar Abogado"):
        nuevo = next_id(abogados)
        abogados.loc[len(abogados)] = [nuevo,nombre,col,correo]
        save("abogados", abogados)
        st.success("Abogado guardado")
        st.rerun()

    st.dataframe(abogados)
