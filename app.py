import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Sistema Estudio Jurídico", layout="wide")

# ===============================
# INICIALIZACIÓN DE SESSION STATE
# ===============================

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=["ID","Nombre","Telefono","Email","Observaciones"])

if "casos" not in st.session_state:
    st.session_state.casos = pd.DataFrame(columns=[
        "ID","Cliente","Expediente","Juzgado","Materia","Estado",
        "Contraparte","Fecha_Inicio",
        "Monto_Honorarios","Monto_Base","Porcentaje_Litis",
        "Observaciones"
    ])

if "pagos" not in st.session_state:
    st.session_state.pagos = pd.DataFrame(columns=["ID","ID_CASO","Fecha","Monto","Observaciones"])

if "pagos_litis" not in st.session_state:
    st.session_state.pagos_litis = pd.DataFrame(columns=["ID","ID_CASO","Fecha","Monto","Observaciones"])


# ===============================
# MENÚ
# ===============================

menu = st.sidebar.radio("Menú", [
    "Clientes",
    "Casos",
    "Pagos Honorarios",
    "Cuota Litis",
    "Pagos Cuota Litis",
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
            st.success("Cliente guardado correctamente")

    st.dataframe(st.session_state.clientes)


# ===============================
# CASOS / EXPEDIENTES
# ===============================

if menu == "Casos":
    st.title("Expedientes")

    if not st.session_state.clientes.empty:

        with st.form("form_caso"):
            cliente = st.selectbox("Cliente", st.session_state.clientes["Nombre"])
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
                    new_id,cliente,expediente,juzgado,materia,estado,
                    contraparte,fecha_inicio,
                    monto_honorarios,monto_base,porcentaje,
                    obs
                ]
                st.success("Caso guardado correctamente")

        st.dataframe(st.session_state.casos)

    else:
        st.warning("Primero debes registrar un cliente")


# ===============================
# PAGOS HONORARIOS
# ===============================

if menu == "Pagos Honorarios":
    st.title("Pagos de Honorarios")

    if not st.session_state.casos.empty:

        with st.form("form_pago"):
            caso = st.selectbox(
                "Expediente",
                st.session_state.casos["Expediente"]
            )
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
                st.success("Pago registrado correctamente")

        st.dataframe(st.session_state.pagos)

    else:
        st.warning("No hay expedientes registrados")


# ===============================
# CUOTA LITIS (VISUALIZACIÓN)
# ===============================

if menu == "Cuota Litis":
    st.title("Cuota Litis")

    if not st.session_state.casos.empty:

        df = st.session_state.casos.copy()
        df["Cuota_Litis_Calculada"] = df["Monto_Base"] * (df["Porcentaje_Litis"]/100)

        st.dataframe(df[[
            "Cliente","Expediente","Monto_Base",
            "Porcentaje_Litis","Cuota_Litis_Calculada","Observaciones"
        ]])

    else:
        st.warning("No hay expedientes registrados")


# ===============================
# PAGOS CUOTA LITIS
# ===============================

if menu == "Pagos Cuota Litis":
    st.title("Pagos Cuota Litis")

    if not st.session_state.casos.empty:

        with st.form("form_pago_litis"):
            caso = st.selectbox(
                "Expediente",
                st.session_state.casos["Expediente"]
            )
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

    else:
        st.warning("No hay expedientes registrados")


# ===============================
# DASHBOARD
# ===============================

if menu == "Dashboard":
    st.title("Dashboard General")

    total_honorarios = st.session_state.casos["Monto_Honorarios"].sum()
    total_base = st.session_state.casos["Monto_Base"].sum()

    df = st.session_state.casos.copy()
    df["Cuota_Litis_Calculada"] = df["Monto_Base"] * (df["Porcentaje_Litis"]/100)
    total_litis = df["Cuota_Litis_Calculada"].sum()

    total_pagado = st.session_state.pagos["Monto"].sum()
    total_pagado_litis = st.session_state.pagos_litis["Monto"].sum()

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Honorarios Pactados", f"${total_honorarios:,.2f}")
    col2.metric("Total Cuota Litis Calculada", f"${total_litis:,.2f}")
    col3.metric("Total Pagado (General)", f"${total_pagado + total_pagado_litis:,.2f}")


# ===============================
# RESUMEN FINANCIERO
# ===============================

if menu == "Resumen Financiero":
    st.title("Resumen Financiero")

    if not st.session_state.casos.empty:

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
        df["Saldo_Honorarios"] = df["Monto_Honorarios"] - df["Pagado_Honorarios"]

        df["Pagado_Litis"] = df["ID"].apply(pagos_litis)
        df["Saldo_Litis"] = df["Cuota_Litis_Calculada"] - df["Pagado_Litis"]

        df["Total_Pactado"] = df["Monto_Honorarios"] + df["Cuota_Litis_Calculada"]
        df["Total_Pagado"] = df["Pagado_Honorarios"] + df["Pagado_Litis"]
        df["Saldo_Total"] = df["Total_Pactado"] - df["Total_Pagado"]

        st.dataframe(df[[
            "Cliente","Expediente",
            "Monto_Honorarios","Pagado_Honorarios","Saldo_Honorarios",
            "Monto_Base","Porcentaje_Litis","Cuota_Litis_Calculada",
            "Pagado_Litis","Saldo_Litis",
            "Total_Pactado","Total_Pagado","Saldo_Total",
            "Observaciones"
        ]])

    else:
        st.warning("No hay expedientes registrados")
