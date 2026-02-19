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
    st.session_state.usuarios = {
        "admin": {"password": "estudio123", "rol": "admin"}
    }

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
    "Resumen Financiero"
])

# =========================
# DASHBOARD
# =========================

if menu == "Dashboard":
    st.title("Dashboard General")

    st.metric("Total Clientes", len(clientes))
    st.metric("Total Casos", len(casos))
    st.metric("Total Abogados", len(abogados))

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

    st.dataframe(honorarios)

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

    st.dataframe(pagos_honorarios)

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

    st.dataframe(cuota_litis)

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

    st.dataframe(pagos_litis)

# =========================
# RESUMEN FINANCIERO
# =========================

if menu == "Resumen Financiero":
    st.title("Resumen Financiero")

    if not casos.empty:
        resumen = []

        for _, c in casos.iterrows():
            expediente = c["Expediente"]

            pactado = honorarios[honorarios["Caso"] == expediente]["Monto Pactado"].sum()
            pagado_h = pagos_honorarios[pagos_honorarios["Caso"] == expediente]["Monto"].sum()

            base = cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"].sum()
            porcentaje = cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"].sum()
            calculada = base * porcentaje / 100
            pagado_l = pagos_litis[pagos_litis["Caso"] == expediente]["Monto"].sum()

            resumen.append([
                expediente,
                pactado,
                pagado_h,
                pactado - pagado_h,
                base,
                porcentaje,
                calculada,
                pagado_l,
                calculada - pagado_l
            ])

        df_resumen = pd.DataFrame(resumen, columns=[
            "Expediente",
            "Honorario Pactado",
            "Honorario Pagado",
            "Honorario Pendiente",
            "Monto Base",
            "Porcentaje",
            "Cuota Litis Calculada",
            "Pagado Litis",
            "Saldo Litis"
        ])

        st.dataframe(df_resumen)
