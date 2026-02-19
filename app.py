import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="⚖️ Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

# =====================================================
# ARCHIVOS
# =====================================================

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

# =====================================================
# CREAR CSV SI NO EXISTEN (Cloud Safe)
# =====================================================

def init_csv():
    estructuras = {
        "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
        "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
        "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones"],
        "honorarios": ["ID","Caso","Monto Pactado"],
        "pagos_honorarios": ["ID","Caso","Monto"],
        "cuota_litis": ["ID","Caso","Monto Base","Porcentaje"],
        "pagos_litis": ["ID","Caso","Monto"],
        "cronograma": ["ID","Caso","Fecha Programada","Monto","Estado"],
        "usuarios": ["ID","Usuario","Password","Rol","Abogado"]
    }

    for key, cols in estructuras.items():
        if not os.path.exists(FILES[key]):
            df = pd.DataFrame(columns=cols)
            df.to_csv(FILES[key], index=False)

init_csv()

# =====================================================
# CARGAR DATA
# =====================================================

clientes = pd.read_csv(FILES["clientes"])
abogados = pd.read_csv(FILES["abogados"])
casos = pd.read_csv(FILES["casos"])
honorarios = pd.read_csv(FILES["honorarios"])
pagos_honorarios = pd.read_csv(FILES["pagos_honorarios"])
cuota_litis = pd.read_csv(FILES["cuota_litis"])
pagos_litis = pd.read_csv(FILES["pagos_litis"])
cronograma = pd.read_csv(FILES["cronograma"])
usuarios = pd.read_csv(FILES["usuarios"])

# =====================================================
# CREAR ADMIN SI NO EXISTE
# =====================================================

if usuarios.empty:
    usuarios.loc[0] = [1,"admin","estudio123","admin",""]
    usuarios.to_csv(FILES["usuarios"], index=False)
    usuarios = pd.read_csv(FILES["usuarios"])

# =====================================================
# LOGIN
# =====================================================

if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None
    st.session_state.rol = None
    st.session_state.abogado = None

if st.session_state.usuario_logueado is None:
    st.title("⚖️ Estudio Jurídico Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")

    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        fila = usuarios[(usuarios["Usuario"]==user) & (usuarios["Password"]==pw)]
        if not fila.empty:
            st.session_state.usuario_logueado = user
            st.session_state.rol = fila.iloc[0]["Rol"]
            st.session_state.abogado = fila.iloc[0]["Abogado"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

st.sidebar.write(f"Usuario: {st.session_state.usuario_logueado}")
st.sidebar.write(f"Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario_logueado = None
    st.session_state.rol = None
    st.session_state.abogado = None
    st.rerun()

# =====================================================
# FILTRO POR ABOGADO (SI NO ES ADMIN)
# =====================================================

if st.session_state.rol == "abogado":
    casos = casos[casos["Abogado"] == st.session_state.abogado]

# =====================================================
# MENU DINÁMICO POR ROL
# =====================================================

if st.session_state.rol == "admin":
    menu = st.sidebar.selectbox("Menú", [
        "Dashboard",
        "Clientes",
        "Abogados",
        "Casos",
        "Honorarios",
        "Pagos Honorarios",
        "Cuota Litis",
        "Pagos Cuota Litis",
        "Cronograma",
        "Pendientes",
        "Resumen Financiero",
        "Usuarios"
    ])
else:
    menu = st.sidebar.selectbox("Menú", [
        "Dashboard",
        "Casos",
        "Honorarios",
        "Pagos Honorarios",
        "Cronograma",
        "Pendientes"
    ])
# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":

    st.title("📊 Dashboard General")

    total_honorarios = honorarios["Monto Pactado"].sum() if not honorarios.empty else 0
    total_pagado = pagos_honorarios["Monto"].sum() if not pagos_honorarios.empty else 0
    total_pendiente = total_honorarios - total_pagado

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Total Honorarios Pactados", f"S/ {total_honorarios:,.2f}")
    col2.metric("💵 Total Cobrado", f"S/ {total_pagado:,.2f}")
    col3.metric("⏳ Total Pendiente", f"S/ {total_pendiente:,.2f}")

# =====================================================
# CLIENTES (SOLO ADMIN)
# =====================================================

if menu == "Clientes" and st.session_state.rol == "admin":

    st.title("👥 Clientes")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo_id = len(clientes)+1
            clientes.loc[len(clientes)] = [nuevo_id,nombre,dni,celular,correo,direccion,obs]
            clientes.to_csv(FILES["clientes"], index=False)
            st.success("Cliente guardado")
            st.rerun()

    st.dataframe(clientes)

# =====================================================
# ABOGADOS (SOLO ADMIN)
# =====================================================

if menu == "Abogados" and st.session_state.rol == "admin":

    st.title("👨‍⚖️ Abogados")

    with st.form("form_abogado"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        coleg = st.text_input("Colegiatura")
        dom = st.text_input("Domicilio Procesal")
        ce = st.text_input("Casilla Electrónica")
        cj = st.text_input("Casilla Judicial")
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo_id = len(abogados)+1
            abogados.loc[len(abogados)] = [nuevo_id,nombre,dni,celular,correo,coleg,dom,ce,cj]
            abogados.to_csv(FILES["abogados"], index=False)
            st.success("Abogado guardado")
            st.rerun()

    st.dataframe(abogados)

# =====================================================
# CASOS
# =====================================================

if menu == "Casos":

    st.title("📂 Casos")

    if st.session_state.rol == "admin":
        lista_abogados = abogados["Nombre"].tolist()
    else:
        lista_abogados = [st.session_state.abogado]

    lista_clientes = clientes["Nombre"].tolist()

    with st.form("form_caso"):
        cliente = st.selectbox("Cliente", lista_clientes)
        abogado = st.selectbox("Abogado", lista_abogados)
        expediente = st.text_input("N° Expediente")
        año = st.text_input("Año")
        materia = st.text_input("Materia")
        pretension = st.text_area("Pretensión")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo_id = len(casos)+1
            casos.loc[len(casos)] = [nuevo_id,cliente,abogado,expediente,año,materia,pretension,obs]
            casos.to_csv(FILES["casos"], index=False)
            st.success("Caso guardado")
            st.rerun()

    st.dataframe(casos)
# =====================================================
# HONORARIOS
# =====================================================

if menu == "Honorarios":

    st.title("💼 Honorarios")

    lista_casos = casos["ID"].tolist()

    with st.form("form_honorarios"):
        caso = st.selectbox("Caso ID", lista_casos)
        monto = st.number_input("Monto Pactado", min_value=0.0)
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo_id = len(honorarios)+1
            honorarios.loc[len(honorarios)] = [nuevo_id,caso,monto]
            honorarios.to_csv(FILES["honorarios"], index=False)
            st.success("Honorario registrado")
            st.rerun()

    st.dataframe(honorarios)

# =====================================================
# PAGOS HONORARIOS
# =====================================================

if menu == "Pagos Honorarios":

    st.title("💵 Pagos Honorarios")

    lista_casos = casos["ID"].tolist()

    with st.form("form_pagos"):
        caso = st.selectbox("Caso ID", lista_casos)
        monto = st.number_input("Monto Pagado", min_value=0.0)
        submit = st.form_submit_button("Registrar Pago")

        if submit:
            nuevo_id = len(pagos_honorarios)+1
            pagos_honorarios.loc[len(pagos_honorarios)] = [nuevo_id,caso,monto]
            pagos_honorarios.to_csv(FILES["pagos_honorarios"], index=False)
            st.success("Pago registrado")
            st.rerun()

    st.dataframe(pagos_honorarios)

# =====================================================
# CRONOGRAMA DE CUOTAS
# =====================================================

if menu == "Cronograma":

    st.title("📅 Cronograma de Pagos")

    lista_casos = casos["ID"].tolist()

    with st.form("form_cronograma"):
        caso = st.selectbox("Caso ID", lista_casos)
        fecha = st.date_input("Fecha Programada", value=date.today())
        monto = st.number_input("Monto Programado", min_value=0.0)
        estado = st.selectbox("Estado", ["Pendiente","Pagado"])
        submit = st.form_submit_button("Guardar")

        if submit:
            nuevo_id = len(cronograma)+1
            cronograma.loc[len(cronograma)] = [nuevo_id,caso,fecha,monto,estado]
            cronograma.to_csv(FILES["cronograma"], index=False)
            st.success("Cuota programada")
            st.rerun()

    st.dataframe(cronograma)

# =====================================================
# PENDIENTES DE COBRAR
# =====================================================

if menu == "Pendientes":

    st.title("⏳ Pendientes de Cobro")

    pendientes = cronograma[cronograma["Estado"]=="Pendiente"]

    if not pendientes.empty:
        st.dataframe(pendientes)
        total = pendientes["Monto"].sum()
        st.metric("Total Pendiente Programado", f"S/ {total:,.2f}")
    else:
        st.success("No hay pendientes")

# =====================================================
# RESUMEN FINANCIERO (SOLO ADMIN)
# =====================================================

if menu == "Resumen Financiero" and st.session_state.rol == "admin":

    st.title("📊 Resumen Financiero General")

    total_honorarios = honorarios["Monto Pactado"].sum() if not honorarios.empty else 0
    total_pagado = pagos_honorarios["Monto"].sum() if not pagos_honorarios.empty else 0
    total_litis = pagos_litis["Monto"].sum() if not pagos_litis.empty else 0

    st.metric("Total Honorarios Pactados", f"S/ {total_honorarios:,.2f}")
    st.metric("Total Cobrado Honorarios", f"S/ {total_pagado:,.2f}")
    st.metric("Total Cobrado Cuota Litis", f"S/ {total_litis:,.2f}")

# =====================================================
# USUARIOS (SOLO ADMIN)
# =====================================================

if menu == "Usuarios" and st.session_state.rol == "admin":

    st.title("👤 Gestión de Usuarios")

    lista_abogados = abogados["Nombre"].tolist()

    with st.form("form_usuario"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña")
        rol = st.selectbox("Rol", ["admin","abogado"])
        abogado = ""

        if rol == "abogado":
            abogado = st.selectbox("Asignar Abogado", lista_abogados)

        submit = st.form_submit_button("Crear Usuario")

        if submit:
            nuevo_id = len(usuarios)+1
            usuarios.loc[len(usuarios)] = [nuevo_id,usuario,password,rol,abogado]
            usuarios.to_csv(FILES["usuarios"], index=False)
            st.success("Usuario creado")
            st.rerun()

    st.dataframe(usuarios)
