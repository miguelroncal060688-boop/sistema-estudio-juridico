import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Sistema Estudio Jurídico", layout="wide")

# ===============================
# INICIALIZACIÓN
# ===============================

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=[
        "ID","Nombre","Telefono","Email","Observaciones"
    ])

if "abogados" not in st.session_state:
    st.session_state.abogados = pd.DataFrame(columns=[
        "ID","Nombre","DNI","Celular","Email",
        "Colegiatura","Domicilio_Procesal",
        "Casilla_Electronica","Casilla_Judicial",
        "Observaciones"
    ])

if "casos" not in st.session_state:
    st.session_state.casos = pd.DataFrame(columns=[
        "ID","Cliente","Abogado","Expediente","Año",
        "Juzgado","Materia","Estado","Pretension",
        "Contraparte","Fecha_Inicio",
        "Monto_Honorarios","Monto_Base",
        "Porcentaje_Litis","Observaciones"
    ])

if "pagos" not in st.session_state:
    st.session_state.pagos = pd.DataFrame(columns=[
        "ID","ID_CASO","Fecha","Monto","Observaciones"
    ])

if "pagos_litis" not in st.session_state:
    st.session_state.pagos_litis = pd.DataFrame(columns=[
        "ID","ID_CASO","Fecha","Monto","Observaciones"
    ])

# ===============================
# MENÚ
# ===============================

menu = st.sidebar.radio("Menú", [
    "Clientes",
    "Abogados",
    "Casos",
    "Pagos Honorarios",
    "Pagos Cuota Litis",
    "Cuota Litis",
    "Dashboard",
    "Resumen Financiero"
])

# ===============================
# CLIENTES
# ===============================

if menu == "Clientes":
    st.title("Clientes")

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
# ABOGADOS
# ===============================

if menu == "Abogados":
    st.title("Gestión de Abogados")

    with st.form("form_abogado"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        email = st.text_input("Correo electrónico")
        colegiatura = st.text_input("Número de colegiatura")
        domicilio = st.text_input("Domicilio procesal")
        casilla_e = st.text_input("Casilla electrónica")
        casilla_j = st.text_input("Casilla judicial")
        obs = st.text_area("Observaciones")

        guardar = st.form_submit_button("Guardar Abogado")

        if guardar and nombre:
            new_id = len(st.session_state.abogados) + 1
            st.session_state.abogados.loc[len(st.session_state.abogados)] = [
                new_id,nombre,dni,celular,email,
                colegiatura,domicilio,
                casilla_e,casilla_j,obs
            ]
            st.success("Abogado guardado")

    st.subheader("Lista de Abogados")
    st.dataframe(st.session_state.abogados)

    # REPORTE POR ABOGADO
    st.subheader("Reporte de Casos por Abogado")

    if not st.session_state.abogados.empty and not st.session_state.casos.empty:

        abogado_sel = st.selectbox(
            "Seleccionar abogado",
            st.session_state.abogados["Nombre"]
        )

        casos_abogado = st.session_state.casos[
            st.session_state.casos["Abogado"] == abogado_sel
        ]

        if not casos_abogado.empty:
            df = casos_abogado.copy()
            df["Cuota_Litis_Calculada"] = (
                df["Monto_Base"] *
                (df["Porcentaje_Litis"]/100)
            )

            st.dataframe(df)

            total_honorarios = df["Monto_Honorarios"].sum()
            total_litis = df["Cuota_Litis_Calculada"].sum()

            st.markdown("### Totales")
            st.write("Total Honorarios:", total_honorarios)
            st.write("Total Cuota Litis:", total_litis)
            st.write("Total General:", total_honorarios + total_litis)
        else:
            st.info("Este abogado no tiene casos asignados.")

# ===============================
# CASOS
# ===============================

if menu == "Casos":
    st.title("Expedientes")

    if not st.session_state.clientes.empty and not st.session_state.abogados.empty:

        with st.form("form_caso"):
            cliente = st.selectbox("Cliente", st.session_state.clientes["Nombre"])
            abogado = st.selectbox("Abogado a cargo", st.session_state.abogados["Nombre"])
            expediente = st.text_input("Número de Expediente")
            año = st.number_input("Año", min_value=2000, max_value=2100, step=1)
            juzgado = st.text_input("Juzgado")
            materia = st.text_input("Materia")
            estado = st.text_input("Estado")
            pretension = st.text_input("Pretensión")
            contraparte = st.text_input("Contraparte")
            fecha_inicio = st.date_input("Fecha de inicio", value=date.today())
            monto_honorarios = st.number_input("Monto Honorarios", min_value=0.0)
            monto_base = st.number_input("Monto Base (Cuota Litis)", min_value=0.0)
            porcentaje = st.number_input("Porcentaje Cuota Litis (%)", min_value=0.0)
            obs = st.text_area("Observaciones")

            guardar = st.form_submit_button("Guardar Caso")

            if guardar and expediente:
                new_id = len(st.session_state.casos) + 1
                st.session_state.casos.loc[len(st.session_state.casos)] = [
                    new_id,cliente,abogado,expediente,año,
                    juzgado,materia,estado,pretension,
                    contraparte,fecha_inicio,
                    monto_honorarios,monto_base,
                    porcentaje,obs
                ]
                st.success("Caso guardado")

        st.dataframe(st.session_state.casos)

    else:
        st.warning("Debe registrar clientes y abogados primero")

# ===============================
# PAGOS HONORARIOS
# ===============================

if menu == "Pagos Honorarios":
    st.title("Pagos de Honorarios")

    if not st.session_state.casos.empty:

        with st.form("form_pago"):
            caso = st.selectbox("Expediente", st.session_state.casos["Expediente"])
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
# PAGOS CUOTA LITIS
# ===============================

if menu == "Pagos Cuota Litis":
    st.title("Pagos Cuota Litis")

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
# CUOTA LITIS (REPORTE)
# ===============================

if menu == "Cuota Litis":
    st.title("Reporte Cuota Litis")

    if not st.session_state.casos.empty:
        df = st.session_state.casos.copy()
        df["Cuota_Litis_Calculada"] = (
            df["Monto_Base"] *
            (df["Porcentaje_Litis"]/100)
        )

        st.dataframe(df[[
            "Cliente","Abogado","Expediente",
            "Monto_Base","Porcentaje_Litis",
            "Cuota_Litis_Calculada"
        ]])

# ===============================
# DASHBOARD
# ===============================

if menu == "Dashboard":
    st.title("Dashboard General")

    total_honorarios = st.session_state.casos["Monto_Honorarios"].sum()

    df = st.session_state.casos.copy()
    df["Cuota_Litis_Calculada"] = (
        df["Monto_Base"] *
        (df["Porcentaje_Litis"]/100)
    )

    total_litis = df["Cuota_Litis_Calculada"].sum()
    total_pagado = st.session_state.pagos["Monto"].sum()
    total_pagado_litis = st.session_state.pagos_litis["Monto"].sum()

    col1,col2,col3 = st.columns(3)
    col1.metric("Honorarios Pactados", total_honorarios)
    col2.metric("Cuota Litis Calculada", total_litis)
    col3.metric("Total Pagado General", total_pagado + total_pagado_litis)

# ===============================
# RESUMEN FINANCIERO
# ===============================

if menu == "Resumen Financiero":
    st.title("Resumen Financiero")

    if not st.session_state.casos.empty:

        df = st.session_state.casos.copy()
        df["Cuota_Litis_Calculada"] = (
            df["Monto_Base"] *
            (df["Porcentaje_Litis"]/100)
        )

        def pagos_h(id):
            return st.session_state.pagos[
                st.session_state.pagos["ID_CASO"]==id
            ]["Monto"].sum()

        def pagos_l(id):
            return st.session_state.pagos_litis[
                st.session_state.pagos_litis["ID_CASO"]==id
            ]["Monto"].sum()

        df["Pagado_Honorarios"] = df["ID"].apply(pagos_h)
        df["Saldo_Honorarios"] = df["Monto_Honorarios"] - df["Pagado_Honorarios"]

        df["Pagado_Litis"] = df["ID"].apply(pagos_l)
        df["Saldo_Litis"] = df["Cuota_Litis_Calculada"] - df["Pagado_Litis"]

        st.subheader("HONORARIOS")
        st.dataframe(df[[
            "Cliente","Expediente",
            "Monto_Honorarios",
            "Pagado_Honorarios",
            "Saldo_Honorarios"
        ]])

        st.subheader("CUOTA LITIS")
        st.dataframe(df[[
            "Cliente","Expediente",
            "Monto_Base",
            "Porcentaje_Litis",
            "Cuota_Litis_Calculada",
            "Pagado_Litis",
            "Saldo_Litis"
        ]])
