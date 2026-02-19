import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="⚖️ Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

# ==============================
# ARCHIVOS
# ==============================

FILES = {
    "clientes": "clientes.csv",
    "abogados": "abogados.csv",
    "casos": "casos.csv",
    "honorarios": "honorarios.csv",
    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",
    "cronograma": "cronograma.csv",
    "usuarios": "usuarios.csv"
}

# ==============================
# CREAR CSV SI NO EXISTEN
# ==============================

def init_csv():
    estructura = {
        "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
        "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
        "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones"],
        "honorarios": ["ID","CasoID","Monto Pactado"],
        "pagos_honorarios": ["ID","CasoID","Monto"],
        "cuota_litis": ["ID","CasoID","Monto Base","Porcentaje"],
        "pagos_litis": ["ID","CasoID","Monto"],
        "cronograma": ["ID","CasoID","Fecha","Monto","Estado"],
        "usuarios": ["ID","Usuario","Password","Rol","Abogado"]
    }

    for key, cols in estructura.items():
        if not os.path.exists(FILES[key]):
            pd.DataFrame(columns=cols).to_csv(FILES[key], index=False)

init_csv()

# ==============================
# CARGA DATA
# ==============================

def load(name):
    return pd.read_csv(FILES[name])

def save(name, df):
    df.to_csv(FILES[name], index=False)

clientes = load("clientes")
abogados = load("abogados")
casos = load("casos")
honorarios = load("honorarios")
pagos_honorarios = load("pagos_honorarios")
cuota_litis = load("cuota_litis")
pagos_litis = load("pagos_litis")
cronograma = load("cronograma")
usuarios = load("usuarios")

# ==============================
# CREAR ADMIN SI NO EXISTE
# ==============================

if usuarios.empty:
    usuarios.loc[0] = [1,"admin","estudio123","admin",""]
    save("usuarios", usuarios)

# ==============================
# LOGIN
# ==============================

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.rol = None
    st.session_state.abogado = None

if st.session_state.user is None:
    st.title("⚖️ Sistema Jurídico")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        fila = usuarios[(usuarios.Usuario==u)&(usuarios.Password==p)]
        if not fila.empty:
            st.session_state.user = u
            st.session_state.rol = fila.iloc[0]["Rol"]
            st.session_state.abogado = fila.iloc[0]["Abogado"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

# ==============================
# SIDEBAR
# ==============================

st.sidebar.write(f"Usuario: {st.session_state.user}")
st.sidebar.write(f"Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

if st.session_state.rol == "admin":
    menu = st.sidebar.selectbox("Menú", [
        "Dashboard","Clientes","Abogados","Casos",
        "Honorarios","Pagos Honorarios",
        "Cuota Litis","Pagos Cuota Litis",
        "Cronograma","Pendientes",
        "Resumen Financiero","Usuarios"
    ])
else:
    menu = st.sidebar.selectbox("Menú", [
        "Dashboard","Casos","Honorarios",
        "Pagos Honorarios","Cronograma","Pendientes"
    ])

# ==============================
# FILTRO ABOGADO
# ==============================

if st.session_state.rol == "abogado":
    casos = casos[casos["Abogado"] == st.session_state.abogado]

# ==============================
# FUNCION TABLA CON ELIMINAR
# ==============================

def tabla_editable(df, nombre):
    st.dataframe(df)
    if not df.empty:
        eliminar = st.number_input(f"ID a eliminar ({nombre})", min_value=1, step=1)
        if st.button(f"Eliminar {nombre}"):
            df = df[df.ID != eliminar]
            save(nombre, df)
            st.success("Eliminado")
            st.rerun()

# ==============================
# DASHBOARD
# ==============================

if menu == "Dashboard":

    total_honorarios = honorarios["Monto Pactado"].sum() if not honorarios.empty else 0
    total_pagado = pagos_honorarios["Monto"].sum() if not pagos_honorarios.empty else 0
    pendiente = total_honorarios - total_pagado

    col1,col2,col3 = st.columns(3)
    col1.metric("💰 Total Pactado", f"S/ {total_honorarios:,.2f}")
    col2.metric("💵 Total Cobrado", f"S/ {total_pagado:,.2f}")
    col3.metric("⏳ Pendiente", f"S/ {pendiente:,.2f}")

# ==============================
# CLIENTES
# ==============================

if menu == "Clientes" and st.session_state.rol=="admin":
    st.title("Clientes")
    nombre = st.text_input("Nombre")
    if st.button("Guardar Cliente"):
        nuevo = len(clientes)+1
        clientes.loc[len(clientes)] = [nuevo,nombre,"","","","",""]
        save("clientes", clientes)
        st.rerun()
    tabla_editable(clientes,"clientes")

# ==============================
# ABOGADOS
# ==============================

if menu == "Abogados" and st.session_state.rol=="admin":
    st.title("Abogados")
    nombre = st.text_input("Nombre Abogado")
    if st.button("Guardar Abogado"):
        nuevo = len(abogados)+1
        abogados.loc[len(abogados)] = [nuevo,nombre,"","","","","",""]
        save("abogados", abogados)
        st.rerun()
    tabla_editable(abogados,"abogados")

# ==============================
# CASOS
# ==============================

if menu == "Casos":
    st.title("Casos")

    lista_clientes = clientes["Nombre"].tolist()
    lista_abogados = abogados["Nombre"].tolist()

    cliente = st.selectbox("Cliente", lista_clientes)
    abogado = st.selectbox("Abogado", lista_abogados)
    expediente = st.text_input("Expediente")
    año = st.text_input("Año")

    if st.button("Guardar Caso"):
        nuevo = len(casos)+1
        casos.loc[len(casos)] = [nuevo,cliente,abogado,expediente,año,"","",""]
        save("casos", casos)
        st.rerun()

    tabla_editable(casos,"casos")

# ==============================
# HONORARIOS
# ==============================

if menu == "Honorarios":
    st.title("Honorarios")

    for _,c in casos.iterrows():
        st.write(f"ID {c.ID} | Exp: {c.Expediente} | Año: {c.Año} | Cliente: {c.Cliente}")

    caso = st.number_input("ID Caso", min_value=1, step=1)
    monto = st.number_input("Monto Pactado", min_value=0.0)

    if st.button("Registrar Honorario"):
        nuevo = len(honorarios)+1
        honorarios.loc[len(honorarios)] = [nuevo,caso,monto]
        save("honorarios", honorarios)
        st.rerun()

    tabla_editable(honorarios,"honorarios")

# ==============================
# CUOTA LITIS
# ==============================

if menu == "Cuota Litis" and st.session_state.rol=="admin":
    st.title("Cuota Litis")

    caso = st.number_input("ID Caso", min_value=1)
    base = st.number_input("Monto Base", min_value=0.0)
    porc = st.number_input("Porcentaje", min_value=0.0)

    if st.button("Guardar Cuota"):
        nuevo = len(cuota_litis)+1
        cuota_litis.loc[len(cuota_litis)] = [nuevo,caso,base,porc]
        save("cuota_litis", cuota_litis)
        st.rerun()

    tabla_editable(cuota_litis,"cuota_litis")

# ==============================
# PAGOS CUOTA LITIS
# ==============================

if menu == "Pagos Cuota Litis" and st.session_state.rol=="admin":
    st.title("Pagos Cuota Litis")

    caso = st.number_input("ID Caso", min_value=1)
    monto = st.number_input("Monto Pago", min_value=0.0)

    if st.button("Registrar Pago"):
        nuevo = len(pagos_litis)+1
        pagos_litis.loc[len(pagos_litis)] = [nuevo,caso,monto]
        save("pagos_litis", pagos_litis)
        st.rerun()

    tabla_editable(pagos_litis,"pagos_litis")

# ==============================
# CRONOGRAMA
# ==============================

if menu == "Cronograma":
    st.title("Cronograma")

    caso = st.number_input("ID Caso", min_value=1)
    fecha = st.date_input("Fecha")
    monto = st.number_input("Monto", min_value=0.0)
    estado = st.selectbox("Estado",["Pendiente","Pagado"])

    if st.button("Guardar Cuota"):
        nuevo = len(cronograma)+1
        cronograma.loc[len(cronograma)] = [nuevo,caso,fecha,monto,estado]
        save("cronograma", cronograma)
        st.rerun()

    tabla_editable(cronograma,"cronograma")

# ==============================
# PENDIENTES
# ==============================

if menu == "Pendientes":
    st.title("Pendientes")

    pendientes = cronograma[cronograma["Estado"]=="Pendiente"]
    st.dataframe(pendientes)

# ==============================
# RESUMEN FINANCIERO
# ==============================

if menu == "Resumen Financiero" and st.session_state.rol=="admin":
    st.title("Resumen Financiero")

    total_litis = pagos_litis["Monto"].sum() if not pagos_litis.empty else 0
    st.metric("Total Cuota Litis Cobrado", f"S/ {total_litis:,.2f}")

# ==============================
# USUARIOS
# ==============================

if menu == "Usuarios" and st.session_state.rol=="admin":
    st.title("Usuarios")

    lista_abogados = abogados["Nombre"].tolist()

    usuario = st.text_input("Usuario")
    password = st.text_input("Password")
    rol = st.selectbox("Rol",["admin","abogado"])
    abogado = ""

    if rol=="abogado":
        abogado = st.selectbox("Asignar Abogado", lista_abogados)

    if st.button("Crear Usuario"):
        nuevo = len(usuarios)+1
        usuarios.loc[len(usuarios)] = [nuevo,usuario,password,rol,abogado]
        save("usuarios", usuarios)
        st.rerun()

    tabla_editable(usuarios,"usuarios")
