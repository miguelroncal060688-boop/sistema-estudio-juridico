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
    if not os.path.exists(FILES["clientes"]):
        pd.DataFrame(columns=["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"]).to_csv(FILES["clientes"], index=False)
    if not os.path.exists(FILES["abogados"]):
        pd.DataFrame(columns=["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"]).to_csv(FILES["abogados"], index=False)
    if not os.path.exists(FILES["casos"]):
        pd.DataFrame(columns=["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones"]).to_csv(FILES["casos"], index=False)
    if not os.path.exists(FILES["honorarios"]):
        pd.DataFrame(columns=["Caso","Monto Pactado"]).to_csv(FILES["honorarios"], index=False)
    if not os.path.exists(FILES["pagos_honorarios"]):
        pd.DataFrame(columns=["Caso","Monto"]).to_csv(FILES["pagos_honorarios"], index=False)
    if not os.path.exists(FILES["cuota_litis"]):
        pd.DataFrame(columns=["Caso","Monto Base","Porcentaje"]).to_csv(FILES["cuota_litis"], index=False)
    if not os.path.exists(FILES["pagos_litis"]):
        pd.DataFrame(columns=["Caso","Monto"]).to_csv(FILES["pagos_litis"], index=False)
init_csv()

# =========================
# LOGIN
# =========================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"admin": {"password": "estudio123", "rol": "admin"}}
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("⚖️ Estudio Jurídico Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user in st.session_state.usuarios and st.session_state.usuarios[user]["password"] == pw:
            st.session_state.usuario = user
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.write(f"Usuario: {st.session_state.usuario}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.experimental_rerun()

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

menu = st.sidebar.selectbox("Menú", [
    "Dashboard",
    "Clientes",
    "Abogados",
    "Casos",
    "Honorarios",
    "Pagos Honorarios",
    "Cuota Litis",
    "Pagos Cuota Litis",
    "Resumen Financiero",
    "Pendientes de Pago"
])

# =========================
# FUNCIONES GENERALES EDITAR/ELIMINAR
# =========================
def editar_eliminar(df, archivo, campos_visibles):
    if not df.empty:
        for i, row in df.iterrows():
            cols = st.columns(len(campos_visibles)+2)
            for j, campo in enumerate(campos_visibles):
                cols[j].write(row[campo])
            if cols[-2].button("Editar", key=f"edit_{i}"):
                for campo in df.columns:
                    row[campo] = st.text_input(f"{campo}", row[campo], key=f"{campo}_{i}")
                df.to_csv(archivo, index=False)
                st.experimental_rerun()
            if cols[-1].button("Eliminar", key=f"del_{i}"):
                df.drop(i, inplace=True)
                df.to_csv(archivo, index=False)
                st.experimental_rerun()

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("Dashboard General")
    total_honorarios = honorarios["Monto Pactado"].sum()
    total_pagado_h = pagos_honorarios["Monto"].sum()
    total_pendiente_h = total_honorarios - total_pagado_h

    total_base = cuota_litis["Monto Base"].sum()
    total_calc = (cuota_litis["Monto Base"] * cuota_litis["Porcentaje"]/100).sum()
    total_pagado_l = pagos_litis["Monto"].sum()
    total_pendiente_l = total_calc - total_pagado_l

    st.metric("Total Clientes", len(clientes))
    st.metric("Total Casos", len(casos))
    st.metric("Total Abogados", len(abogados))

    st.subheader("Resumen Económico")
    col1, col2 = st.columns(2)
    col1.metric("Total Honorarios Pactados", total_honorarios)
    col1.metric("Total Pagado Honorarios", total_pagado_h)
    col1.metric("Pendiente de Cobro Honorarios", total_pendiente_h)
    col2.metric("Total Cuota Litis Base", total_base)
    col2.metric("Cuota Litis Calculada", total_calc)
    col2.metric("Pendiente de Cobro Cuota Litis", total_pendiente_l)

# =========================
# CLIENTES
# =========================
if menu == "Clientes":
    st.title("Clientes")
    with st.form("nuevo_cliente", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")
    if submit:
        if nombre.strip()=="":
            st.error("Debe ingresar el nombre del cliente")
        else:
            new_id = len(clientes)+1
            clientes.loc[len(clientes)] = [new_id,nombre,dni,celular,correo,direccion,obs]
            clientes.to_csv(FILES["clientes"], index=False)
            st.success("Cliente registrado")
            st.experimental_rerun()
    st.subheader("Listado de Clientes")
    st.dataframe(clientes)
    editar_eliminar(clientes, FILES["clientes"], ["Nombre","DNI","Celular"])

# =========================
# ABOGADOS
# =========================
if menu == "Abogados":
    st.title("Abogados")
    with st.form("nuevo_abogado", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        coleg = st.text_input("Colegiatura")
        dom = st.text_input("Domicilio Procesal")
        cas_e = st.text_input("Casilla Electrónica")
        cas_j = st.text_input("Casilla Judicial")
        submit = st.form_submit_button("Guardar")
    if submit:
        new_id = len(abogados)+1
        abogados.loc[len(abogados)] = [new_id,nombre,dni,celular,correo,coleg,dom,cas_e,cas_j]
        abogados.to_csv(FILES["abogados"], index=False)
        st.success("Abogado registrado")
        st.experimental_rerun()
    st.subheader("Listado de Abogados")
    st.dataframe(abogados)
    editar_eliminar(abogados, FILES["abogados"], ["Nombre","DNI","Colegiatura"])

# =========================
# CASOS
# =========================
if menu == "Casos":
    st.title("Casos")
    with st.form("nuevo_caso", clear_on_submit=True):
        cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
        abogado = st.selectbox("Abogado", abogados["Nombre"] if not abogados.empty else [])
        expediente = st.text_input("Número de Expediente")
        año = st.text_input("Año")
        materia = st.text_input("Materia")
        pretension = st.text_input("Pretensión")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")
    if submit:
        new_id = len(casos)+1
        casos.loc[len(casos)] = [new_id,cliente,abogado,expediente,año,materia,pretension,obs]
        casos.to_csv(FILES["casos"], index=False)
        st.success("Caso registrado")
        st.experimental_rerun()
    st.subheader("Listado de Casos")
    st.dataframe(casos)
    editar_eliminar(casos, FILES["casos"], ["Cliente","Abogado","Expediente","Año"])

# =========================
# HONORARIOS
# =========================
if menu == "Honorarios":
    st.title("Honorarios Pactados")
    caso = st.selectbox("Caso", casos["Expediente"] if not casos.empty else [])
    monto = st.number_input("Monto Pactado", min_value=0.0)
    if st.button("Guardar"):
        honorarios.loc[len(honorarios)] = [caso,monto]
        honorarios.to_csv(FILES["honorarios"], index=False)
        st.success("Honorario guardado")
        st.experimental_rerun()
    st.dataframe(honorarios)
    editar_eliminar(honorarios, FILES["honorarios"], ["Caso","Monto Pactado"])

# =========================
# PAGOS HONORARIOS
# =========================
if menu == "Pagos Honorarios":
    st.title("Pagos de Honorarios")
    caso = st.selectbox("Caso", casos["Expediente"] if not casos.empty else [])
    monto = st.number_input("Monto Pagado", min_value=0.0)
    if st.button("Registrar Pago"):
        pagos_honorarios.loc[len(pagos_honorarios)] = [caso,monto]
        pagos_honorarios.to_csv(FILES["pagos_honorarios"], index=False)
        st.success("Pago registrado")
        st.experimental_rerun()
    st.dataframe(pagos_honorarios)
    editar_eliminar(pagos_honorarios, FILES["pagos_honorarios"], ["Caso","Monto"])

# =========================
# CUOTA LITIS
# =========================
if menu == "Cuota Litis":
    st.title("Cuota Litis")
    caso = st.selectbox("Caso", casos["Expediente"] if not casos.empty else [])
    base = st.number_input("Monto Base", min_value=0.0)
    porcentaje = st.number_input("Porcentaje (%)", min_value=0.0)
    if st.button("Guardar Cuota Litis"):
        cuota_litis.loc[len(cuota_litis)] = [caso,base,porcentaje]
        cuota_litis.to_csv(FILES["cuota_litis"], index=False)
        st.success("Cuota Litis guardada")
        st.experimental_rerun()
    st.dataframe(cuota_litis)
    editar_eliminar(cuota_litis, FILES["cuota_litis"], ["Caso","Monto Base","Porcentaje"])

# =========================
# PAGOS CUOTA LITIS
# =========================
if menu == "Pagos Cuota Litis":
    st.title("Pagos Cuota Litis")
    caso = st.selectbox("Caso", casos["Expediente"] if not casos.empty else [])
    monto = st.number_input("Monto Pagado", min_value=0.0)
    if st.button("Registrar Pago Litis"):
        pagos_litis.loc[len(pagos_litis)] = [caso,monto]
        pagos_litis.to_csv(FILES["pagos_litis"], index=False)
        st.success("Pago registrado")
        st.experimental_rerun()
    st.dataframe(pagos_litis)
    editar_eliminar(pagos_litis, FILES["pagos_litis"], ["Caso","Monto"])

# =========================
# RESUMEN FINANCIERO
# =========================
if menu == "Resumen Financiero":
    st.title("Resumen Financiero")
    if not casos.empty:
        resumen_honorarios = []
        resumen_litis = []
        for _, c in casos.iterrows():
            exp = c["Expediente"]
            cliente = c["Cliente"]
            # HONORARIOS
            pactado = honorarios[honorarios["Caso"]==exp]["Monto Pactado"].sum()
            pagado_h = pagos_honorarios[pagos_honorarios["Caso"]==exp]["Monto"].sum()
            pendiente_h = pactado - pagado_h
            resumen_honorarios.append([cliente, exp, pactado, pagado_h, pendiente_h])
            # CUOTA LITIS
            base = cuota_litis[cuota_litis["Caso"]==exp]["Monto Base"].sum()
            porcentaje = cuota_litis[cuota_litis["Caso"]==exp]["Porcentaje"].sum()
            calculada = base*porcentaje/100
            pagado_l = pagos_litis[pagos_litis["Caso"]==exp]["Monto"].sum()
            pendiente_l = calculada - pagado_l
            resumen_litis.append([cliente, exp, base, porcentaje, calculada, pagado_l, pendiente_l])
        st.subheader("Honorarios")
        st.dataframe(pd.DataFrame(resumen_honorarios, columns=["Cliente","Expediente","Pactado","Pagado","Pendiente"]))
        st.subheader("Cuota Litis")
        st.dataframe(pd.DataFrame(resumen_litis, columns=["Cliente","Expediente","Base","Porcentaje","Calculada","Pagado","Pendiente"]))

# =========================
# PENDIENTES DE PAGO
# =========================
if menu == "Pendientes de Pago":
    st.title("Pendientes de Pago")
    pendientes = []
    for _, c in casos.iterrows():
        exp = c["Expediente"]
        cliente = c["Cliente"]
        # Honorarios
        pactado = honorarios[honorarios["Caso"]==exp]["Monto Pactado"].sum()
        pagado_h = pagos_honorarios[pagos_honorarios["Caso"]==exp]["Monto"].sum()
        pendiente_h = pactado - pagado_h
        # Cuota Litis
        base = cuota_litis[cuota_litis["Caso"]==exp]["Monto Base"].sum()
        porcentaje = cuota_litis[cuota_litis["Caso"]==exp]["Porcentaje"].sum()
        calculada = base*porcentaje/100
        pagado_l = pagos_litis[pagos_litis["Caso"]==exp]["Monto"].sum()
        pendiente_l = calculada - pagado_l
        if pendiente_h>0 or pendiente_l>0:
            pendientes.append([cliente, exp, pendiente_h, pendiente_l])
    st.dataframe(pd.DataFrame(pendientes, columns=["Cliente","Expediente","Pendiente Honorarios","Pendiente Cuota Litis"]))
