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
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.write(f"Usuario: {st.session_state.usuario}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

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
    "Pendientes de Cobro",
    "Resumen Financiero"
])

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":
    st.title("Dashboard General")
    total_honorarios = honorarios["Monto Pactado"].sum()
    total_pagado_h = pagos_honorarios["Monto"].sum()
    total_pendiente_h = total_honorarios - total_pagado_h
    total_litis = (cuota_litis["Monto Base"] * cuota_litis["Porcentaje"] / 100).sum()
    total_pagado_l = pagos_litis["Monto"].sum()
    total_pendiente_l = total_litis - total_pagado_l

    st.metric("Total Clientes", len(clientes))
    st.metric("Total Casos", len(casos))
    st.metric("Total Abogados", len(abogados))
    st.metric("Honorarios Pactados", total_honorarios)
    st.metric("Honorarios Pagados", total_pagado_h)
    st.metric("Honorarios Pendientes", total_pendiente_h)
    st.metric("Cuotas Litis Calculadas", total_litis)
    st.metric("Cuotas Litis Pagadas", total_pagado_l)
    st.metric("Cuotas Litis Pendientes", total_pendiente_l)

# =========================
# FUNCIONES GENERALES
# =========================

def editar_eliminar(df, file, key_cols):
    st.subheader("Editar / Eliminar")
    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"{row[key_cols[0]]}"):
                new_vals = []
                cols = df.columns
                for col in cols[1:]:
                    val = st.text_input(f"{col}", row[col], key=f"{col}_{i}")
                    new_vals.append(val)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Guardar Cambios", key=f"edit_{i}"):
                        for j, col in enumerate(cols[1:]):
                            df.at[i, col] = new_vals[j]
                        df.to_csv(file, index=False)
                        st.success("Registro actualizado")
                        st.experimental_rerun()
                with col2:
                    if st.button("Eliminar", key=f"del_{i}"):
                        df.drop(i, inplace=True)
                        df.to_csv(file, index=False)
                        st.success("Registro eliminado")
                        st.experimental_rerun()

# =========================
# CLIENTES
# =========================

if menu == "Clientes":
    st.title("Clientes")
    with st.form("nuevo_cliente"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")
        if submit:
            new_id = len(clientes) + 1
            clientes.loc[len(clientes)] = [new_id,nombre,dni,celular,correo,direccion,obs]
            clientes.to_csv(FILES["clientes"], index=False)
            st.success("Cliente registrado")
            st.rerun()
    st.subheader("Listado")
    st.dataframe(clientes)
    editar_eliminar(clientes, FILES["clientes"], ["Nombre"])

# =========================
# ABOGADOS
# =========================

if menu == "Abogados":
    st.title("Abogados")
    with st.form("nuevo_abogado"):
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
            new_id = len(abogados) + 1
            abogados.loc[len(abogados)] = [new_id,nombre,dni,celular,correo,coleg,dom,cas_e,cas_j]
            abogados.to_csv(FILES["abogados"], index=False)
            st.success("Abogado registrado")
            st.rerun()
    st.subheader("Listado")
    st.dataframe(abogados)
    editar_eliminar(abogados, FILES["abogados"], ["Nombre"])

# =========================
# CASOS
# =========================

if menu == "Casos":
    st.title("Casos")
    with st.form("nuevo_caso"):
        cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
        abogado = st.selectbox("Abogado", abogados["Nombre"] if not abogados.empty else [])
        expediente = st.text_input("Número de Expediente")
        año = st.text_input("Año")
        materia = st.text_input("Materia")
        pretension = st.text_input("Pretensión")
        obs = st.text_area("Observaciones")
        submit = st.form_submit_button("Guardar")
        if submit:
            new_id = len(casos) + 1
            casos.loc[len(casos)] = [new_id,cliente,abogado,expediente,año,materia,pretension,obs]
            casos.to_csv(FILES["casos"], index=False)
            st.success("Caso registrado")
            st.rerun()
    st.subheader("Listado")
    st.dataframe(casos)
    editar_eliminar(casos, FILES["casos"], ["Expediente"])

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
        st.rerun()
    st.subheader("Listado")
    st.dataframe(honorarios)
    editar_eliminar(honorarios, FILES["honorarios"], ["Caso"])

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
        st.rerun()
    st.subheader("Listado")
    st.dataframe(pagos_honorarios)
    editar_eliminar(pagos_honorarios, FILES["pagos_honorarios"], ["Caso"])

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
        st.rerun()
    st.subheader("Listado")
    st.dataframe(cuota_litis)
    editar_eliminar(cuota_litis, FILES["cuota_litis"], ["Caso"])

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
        st.rerun()
    st.subheader("Listado")
    st.dataframe(pagos_litis)
    editar_eliminar(pagos_litis, FILES["pagos_litis"], ["Caso"])

# =========================
# PENDIENTES DE COBRO
# =========================

if menu == "Pendientes de Cobro":
    st.title("Pendientes de Cobro")
    df_pendientes = []
    for _, c in casos.iterrows():
        expediente = c["Expediente"]
        cliente = c["Cliente"]
        pactado = honorarios[honorarios["Caso"] == expediente]["Monto Pactado"].sum()
        pagado_h = pagos_honorarios[pagos_honorarios["Caso"] == expediente]["Monto"].sum()
        base = cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"].sum()
        porcentaje = cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"].sum()
        calculada = base * porcentaje / 100
        pagado_l = pagos_litis[pagos_litis["Caso"] == expediente]["Monto"].sum()
        pendiente_h = pactado - pagado_h
        pendiente_l = calculada - pagado_l
        df_pendientes.append([expediente, cliente, pendiente_h, pendiente_l])
    df_pend = pd.DataFrame(df_pendientes, columns=["Expediente","Cliente","Honorario Pendiente","Cuota Litis Pendiente"])
    st.dataframe(df_pend)

# =========================
# RESUMEN FINANCIERO
# =========================

if menu == "Resumen Financiero":
    st.title("Resumen Financiero")
    if not casos.empty:
        resumen_h = []
        resumen_l = []
        for _, c in casos.iterrows():
            expediente = c["Expediente"]
            cliente = c["Cliente"]
            pactado = honorarios[honorarios["Caso"] == expediente]["Monto Pactado"].sum()
            pagado_h = pagos_honorarios[pagos_honorarios["Caso"] == expediente]["Monto"].sum()
            pendiente_h = pactado - pagado_h
            resumen_h.append([expediente, cliente, pactado, pagado_h, pendiente_h])

            base = cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"].sum()
            porcentaje = cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"].sum()
            calculada = base * porcentaje / 100
            pagado_l = pagos_litis[pagos_litis["Caso"] == expediente]["Monto"].sum()
            pendiente_l = calculada - pagado_l
            resumen_l.append([expediente, cliente, base, porcentaje, calculada, pagado_l, pendiente_l])

        df_honorarios = pd.DataFrame(resumen_h, columns=["Expediente","Cliente","Pactado","Pagado","Pendiente"])
        df_litis = pd.DataFrame(resumen_l, columns=["Expediente","Cliente","Monto Base","Porcentaje","Calculada","Pagado","Pendiente"])

        st.subheader("Honorarios")
        st.dataframe(df_honorarios)
        st.subheader("Cuotas Litis")
        st.dataframe(df_litis)
