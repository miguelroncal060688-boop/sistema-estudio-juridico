import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="⚖️ Estudio de Abogados Roncal Liñán y Asociados", layout="wide")

# ===============================
# INICIALIZACIÓN SESSION STATE
# ===============================

if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "admin": {
            "password": "admin123",
            "rol": "admin",
            "abogado": None,
            "puede_registrar": True
        }
    }

if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=["ID","Nombre","Telefono","Email","Observaciones"])

if "abogados" not in st.session_state:
    st.session_state.abogados = pd.DataFrame(columns=["ID","Nombre"])

if "casos" not in st.session_state:
    st.session_state.casos = pd.DataFrame(columns=[
        "ID","Cliente","Abogado","Expediente","Juzgado","Materia","Estado",
        "Contraparte","Fecha_Inicio",
        "Monto_Honorarios","Monto_Base","Porcentaje_Litis",
        "Observaciones"
    ])

if "pagos" not in st.session_state:
    st.session_state.pagos = pd.DataFrame(columns=["ID","ID_CASO","Fecha","Monto","Observaciones"])

if "pagos_litis" not in st.session_state:
    st.session_state.pagos_litis = pd.DataFrame(columns=["ID","ID_CASO","Fecha","Monto","Observaciones"])


# ===============================
# LOGIN
# ===============================

if st.session_state.usuario_logueado is None:

    st.title("⚖️ Estudio de Abogados Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario in st.session_state.usuarios:
            if st.session_state.usuarios[usuario]["password"] == password:
                st.session_state.usuario_logueado = usuario
                st.success("Ingreso correcto")
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        else:
            st.error("Usuario no existe")

    st.stop()


usuario_actual = st.session_state.usuario_logueado
datos_usuario = st.session_state.usuarios[usuario_actual]
rol = datos_usuario["rol"]
puede_registrar = datos_usuario["puede_registrar"]

# ===============================
# TÍTULO
# ===============================

st.title("⚖️ Estudio de Abogados Roncal Liñán y Asociados")
st.write(f"Usuario: {usuario_actual} | Rol: {rol}")

if st.button("Cerrar Sesión"):
    st.session_state.usuario_logueado = None
    st.rerun()

# ===============================
# MENÚ SEGÚN ROL
# ===============================

if rol == "admin":
    menu = st.sidebar.radio("Menú", [
        "Panel Usuarios",
        "Abogados",
        "Clientes",
        "Casos",
        "Pagos Honorarios",
        "Cuota Litis",
        "Pagos Cuota Litis",
        "Dashboard",
        "Resumen Financiero"
    ])
else:
    menu = st.sidebar.radio("Menú", [
        "Casos",
        "Pagos Honorarios",
        "Dashboard"
    ])


# ===============================
# PANEL USUARIOS (ADMIN)
# ===============================

if menu == "Panel Usuarios" and rol == "admin":

    st.header("Gestión de Usuarios")

    with st.form("crear_usuario"):
        nuevo_usuario = st.text_input("Nuevo Usuario")
        nueva_password = st.text_input("Contraseña", type="password")
        abogado_vinculado = st.selectbox("Abogado vinculado", ["Ninguno"] + list(st.session_state.abogados["Nombre"]))
        crear = st.form_submit_button("Crear Usuario")

        if crear:
            if nuevo_usuario not in st.session_state.usuarios:
                st.session_state.usuarios[nuevo_usuario] = {
                    "password": nueva_password,
                    "rol": "abogado",
                    "abogado": None if abogado_vinculado=="Ninguno" else abogado_vinculado,
                    "puede_registrar": False
                }
                st.success("Usuario creado")
            else:
                st.error("El usuario ya existe")

    st.subheader("Administrar Usuarios")

    for user, datos in st.session_state.usuarios.items():
        if user != "admin":
            st.write(f"Usuario: {user}")

            nueva_pass = st.text_input(f"Nueva contraseña para {user}", type="password", key=f"pass_{user}")
            if st.button(f"Cambiar contraseña {user}"):
                st.session_state.usuarios[user]["password"] = nueva_pass
                st.success("Contraseña actualizada")

            permiso = st.checkbox(
                f"Permitir registrar información ({user})",
                value=datos["puede_registrar"],
                key=f"perm_{user}"
            )
            st.session_state.usuarios[user]["puede_registrar"] = permiso

            st.markdown("---")


# ===============================
# ABOGADOS (ADMIN)
# ===============================

if menu == "Abogados" and rol == "admin":

    st.header("Registro de Abogados")

    with st.form("form_abogado"):
        nombre = st.text_input("Nombre Abogado")
        guardar = st.form_submit_button("Guardar")

        if guardar and nombre:
            new_id = len(st.session_state.abogados) + 1
            st.session_state.abogados.loc[len(st.session_state.abogados)] = [new_id,nombre]
            st.success("Abogado registrado")

    st.dataframe(st.session_state.abogados)


# ===============================
# CLIENTES
# ===============================

if menu == "Clientes" and rol == "admin":

    st.header("Clientes")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre")
        telefono = st.text_input("Teléfono")
        email = st.text_input("Email")
        obs = st.text_area("Observaciones")
        guardar = st.form_submit_button("Guardar")

        if guardar and nombre:
            new_id = len(st.session_state.clientes) + 1
            st.session_state.clientes.loc[len(st.session_state.clientes)] = [
                new_id,nombre,telefono,email,obs
            ]
            st.success("Cliente guardado")

    st.dataframe(st.session_state.clientes)


# ===============================
# FILTRO CASOS POR ROL
# ===============================

def obtener_casos_visibles():
    if rol == "admin":
        return st.session_state.casos
    else:
        abogado = datos_usuario["abogado"]
        return st.session_state.casos[st.session_state.casos["Abogado"]==abogado]


# ===============================
# CASOS
# ===============================

if menu == "Casos":

    st.header("Expedientes")

    casos_visibles = obtener_casos_visibles()

    if rol == "admin" or puede_registrar:

        if not st.session_state.clientes.empty:

            with st.form("form_caso"):
                cliente = st.selectbox("Cliente", st.session_state.clientes["Nombre"])
                abogado = st.selectbox("Abogado", st.session_state.abogados["Nombre"])
                expediente = st.text_input("Número de Expediente")
                juzgado = st.text_input("Juzgado")
                materia = st.text_input("Materia")
                estado = st.text_input("Estado del proceso")
                contraparte = st.text_input("Contraparte")
                fecha_inicio = st.date_input("Fecha de inicio", value=date.today())
                monto_honorarios = st.number_input("Monto Pactado Honorarios", min_value=0.0)
                monto_base = st.number_input("Monto Base (Cuota Litis)", min_value=0.0)
                porcentaje = st.number_input("Porcentaje Cuota Litis (%)", min_value=0.0)
                obs = st.text_area("Observaciones")

                guardar = st.form_submit_button("Guardar Caso")

                if guardar and expediente:
                    new_id = len(st.session_state.casos) + 1
                    st.session_state.casos.loc[len(st.session_state.casos)] = [
                        new_id,cliente,abogado,expediente,juzgado,materia,estado,
                        contraparte,fecha_inicio,
                        monto_honorarios,monto_base,porcentaje,
                        obs
                    ]
                    st.success("Caso guardado")

    st.dataframe(casos_visibles)


# ===============================
# PAGOS HONORARIOS
# ===============================

if menu == "Pagos Honorarios":

    casos_visibles = obtener_casos_visibles()

    if rol == "admin" or puede_registrar:

        if not casos_visibles.empty:

            with st.form("form_pago"):
                caso = st.selectbox("Expediente", casos_visibles["Expediente"])
                fecha = st.date_input("Fecha", value=date.today())
                monto = st.number_input("Monto", min_value=0.0)
                obs = st.text_area("Observaciones")

                guardar = st.form_submit_button("Registrar Pago")

                if guardar:
                    id_caso = st.session_state.casos[
                        st.session_state.casos["Expediente"]==caso
                    ]["ID"].values[0]

                    new_id = len(st.session_state.pagos) + 1
                    st.session_state.pagos.loc[len(st.session_state.pagos)] = [
                        new_id,id_caso,fecha,monto,obs
                    ]
                    st.success("Pago registrado")

    st.dataframe(st.session_state.pagos)


# ===============================
# CUOTA LITIS (SOLO ADMIN)
# ===============================

if menu == "Cuota Litis" and rol == "admin":

    st.header("Cuota Litis")

    df = st.session_state.casos.copy()
    df["Cuota_Litis_Calculada"] = df["Monto_Base"] * (df["Porcentaje_Litis"]/100)

    st.dataframe(df[[
        "Cliente","Abogado","Expediente","Monto_Base",
        "Porcentaje_Litis","Cuota_Litis_Calculada","Observaciones"
    ]])


# ===============================
# PAGOS CUOTA LITIS (ADMIN)
# ===============================

if menu == "Pagos Cuota Litis" and rol == "admin":

    if not st.session_state.casos.empty:

        with st.form("form_pago_litis"):
            caso = st.selectbox("Expediente", st.session_state.casos["Expediente"])
            fecha = st.date_input("Fecha", value=date.today())
            monto = st.number_input("Monto", min_value=0.0)
            obs = st.text_area("Observaciones")

            guardar = st.form_submit_button("Registrar Pago")

            if guardar:
                id_caso = st.session_state.casos[
                    st.session_state.casos["Expediente"]==caso
                ]["ID"].values[0]

                new_id = len(st.session_state.pagos_litis) + 1
                st.session_state.pagos_litis.loc[len(st.session_state.pagos_litis)] = [
                    new_id,id_caso,fecha,monto,obs
                ]
                st.success("Pago de cuota litis registrado")

    st.dataframe(st.session_state.pagos_litis)


# ===============================
# DASHBOARD
# ===============================

if menu == "Dashboard":

    casos_visibles = obtener_casos_visibles()

    total_honorarios = casos_visibles["Monto_Honorarios"].sum()

    df = casos_visibles.copy()
    df["Cuota_Litis_Calculada"] = df["Monto_Base"] * (df["Porcentaje_Litis"]/100)
    total_litis = df["Cuota_Litis_Calculada"].sum()

    total_pagado = st.session_state.pagos["Monto"].sum()

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Honorarios Pactados", f"${total_honorarios:,.2f}")
    col2.metric("Total Cuota Litis Calculada", f"${total_litis:,.2f}")
    col3.metric("Total Pagado Honorarios", f"${total_pagado:,.2f}")


# ===============================
# RESUMEN FINANCIERO (ADMIN)
# ===============================

if menu == "Resumen Financiero" and rol == "admin":

    df = st.session_state.casos.copy()
    df["Cuota_Litis_Calculada"] = df["Monto_Base"] * (df["Porcentaje_Litis"]/100)

    def pagos_honorarios(id_caso):
        return st.session_state.pagos[
            st.session_state.pagos["ID_CASO"]==id_caso
        ]["Monto"].sum()

    def pagos_litis(id_caso):
        return st.session_state.pagos_litis[
            st.session_state.pagos_litis["ID_CASO"]==id_caso
        ]["Monto"].sum()

    df["Pagado_Honorarios"] = df["ID"].apply(pagos_honorarios)
    df["Pagado_Litis"] = df["ID"].apply(pagos_litis)

    st.dataframe(df)
