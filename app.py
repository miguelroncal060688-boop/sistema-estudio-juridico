import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados ⚖️", layout="wide")

# ===============================
# LOGIN DE USUARIOS / ABOGADOS
# ===============================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = pd.DataFrame(columns=[
        "Usuario","Contraseña","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio_Procesal","Casilla_Electronica","Casilla_Judicial"
    ])

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.usuario_actual = None

if not st.session_state.login:
    st.title("Acceso al Sistema - Estudio Jurídico Roncal Liñán y Asociados ⚖️")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        df = st.session_state.usuarios
        if not df.empty and ((df["Usuario"]==usuario) & (df["Contraseña"]==clave)).any():
            st.session_state.login = True
            st.session_state.usuario_actual = usuario
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ===============================
# FUNCIONES DE CSV
# ===============================
def cargar_csv(nombre, columnas):
    if os.path.exists(nombre):
        df = pd.read_csv(nombre)
        # Asegurar columnas
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=columnas)

def guardar_csv(df, nombre):
    df.to_csv(nombre, index=False)

# ===============================
# CARGA DE DATOS
# ===============================
clientes = cargar_csv("clientes.csv", ["ID","Nombre","DNI","Celular","Correo","Dirección","Observaciones"])
abogados = cargar_csv("abogados.csv", ["Usuario","Contraseña","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio_Procesal","Casilla_Electronica","Casilla_Judicial"])
casos = cargar_csv("casos.csv", ["ID_CASO","Cliente","Abogado","Expediente","Año","Materia","Pretension","Estado","Contraparte","Monto_Honorarios","Monto_Base","Porcentaje_Litis","Observaciones"])
pagos = cargar_csv("pagos.csv", ["ID_PAGO","ID_CASO","Fecha","Monto","Observaciones"])
pagos_litis = cargar_csv("pagos_litis.csv", ["ID_PAGO","ID_CASO","Fecha","Monto","Observaciones"])
cronogramas = cargar_csv("cronogramas.csv", ["ID_CRON","ID_CASO","Fecha_Tentativa","Monto","Observaciones"])

# ===============================
# MENÚ
# ===============================
menu = st.sidebar.radio("Menú", [
    "Dashboard",
    "Clientes",
    "Abogados",
    "Casos",
    "Pagos Honorarios",
    "Cuota Litis",
    "Pagos Cuota Litis",
    "Cronograma de Pagos",
    "Pendientes de Cobro",
    "Resumen Financiero",
    "Reporte por Cliente",
    "Panel de Usuarios"
])

# ===============================
# CLIENTES
# ===============================
if menu == "Clientes":
    st.title("Gestión de Clientes")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        observaciones = st.text_area("Observaciones")
        guardar = st.form_submit_button("Guardar Cliente")
        if guardar:
            new_id = len(clientes)+1
            clientes.loc[len(clientes)] = [new_id,nombre,dni,celular,correo,direccion,observaciones]
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente guardado")
            st.experimental_rerun()

    st.subheader("Clientes Registrados")
    if not clientes.empty:
        for idx,row in clientes.iterrows():
            col1,col2 = st.columns([3,1])
            with col1:
                st.write(f"{row['ID']} - {row['Nombre']} | {row['DNI']} | {row['Correo']} | {row['Celular']} | {row['Dirección']}")
                st.write(f"Observaciones: {row['Observaciones']}")
            with col2:
                if st.button("Editar", key=f"edit_cliente_{idx}"):
                    with st.form(f"form_edit_cliente_{idx}"):
                        nombre_e = st.text_input("Nombre", row["Nombre"])
                        dni_e = st.text_input("DNI", row["DNI"])
                        celular_e = st.text_input("Celular", row["Celular"])
                        correo_e = st.text_input("Correo", row["Correo"])
                        direccion_e = st.text_input("Dirección", row["Dirección"])
                        observaciones_e = st.text_area("Observaciones", row["Observaciones"])
                        submit = st.form_submit_button("Guardar Cambios")
                        if submit:
                            clientes.loc[idx] = [row['ID'],nombre_e,dni_e,celular_e,correo_e,direccion_e,observaciones_e]
                            guardar_csv(clientes,"clientes.csv")
                            st.success("Cliente actualizado")
                            st.experimental_rerun()
                if st.button("Eliminar", key=f"del_cliente_{idx}"):
                    clientes.drop(idx,inplace=True)
                    clientes.reset_index(drop=True,inplace=True)
                    guardar_csv(clientes,"clientes.csv")
                    st.success("Cliente eliminado")
                    st.experimental_rerun()

# ===============================
# ABOGADOS
# ===============================
if menu == "Abogados":
    st.title("Gestión de Abogados / Usuarios")
    with st.form("form_abogado"):
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        nombre = st.text_input("Nombre Completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        colegiatura = st.text_input("Colegiatura")
        domicilio = st.text_input("Domicilio Procesal")
        casilla_e = st.text_input("Casilla Electrónica")
        casilla_j = st.text_input("Casilla Judicial")
        guardar = st.form_submit_button("Guardar Abogado")
        if guardar:
            abogados.loc[len(abogados)] = [usuario,contraseña,nombre,dni,celular,correo,colegiatura,domicilio,casilla_e,casilla_j]
            guardar_csv(abogados,"abogados.csv")
            st.success("Abogado registrado")
            st.experimental_rerun()

    st.subheader("Abogados Registrados")
    if not abogados.empty:
        for idx,row in abogados.iterrows():
            col1,col2 = st.columns([3,1])
            with col1:
                st.write(f"{row['Nombre']} | Usuario: {row['Usuario']} | DNI: {row['DNI']} | Correo: {row['Correo']} | Celular: {row['Celular']}")
                st.write(f"Colegiatura: {row['Colegiatura']} | Domicilio: {row['Domicilio_Procesal']} | Casilla Electrónica: {row['Casilla_Electronica']} | Casilla Judicial: {row['Casilla_Judicial']}")
            with col2:
                if st.button("Eliminar", key=f"del_abogado_{idx}"):
                    abogados.drop(idx,inplace=True)
                    abogados.reset_index(drop=True,inplace=True)
                    guardar_csv(abogados,"abogados.csv")
                    st.success("Abogado eliminado")
                    st.experimental_rerun()

# ===============================
# CASOS / EXPEDIENTES
# ===============================
if menu == "Casos":
    st.title("Gestión de Casos / Expedientes")
    if clientes.empty or abogados.empty:
        st.warning("Debe existir al menos un cliente y un abogado registrado.")
    else:
        with st.form("form_caso"):
            cliente = st.selectbox("Cliente", clientes["Nombre"])
            abogado = st.selectbox("Abogado a Cargo", abogados["Nombre"])
            expediente = st.text_input("Número de Expediente")
            año = st.text_input("Año")
            materia = st.text_input("Materia")
            pretension = st.text_input("Pretensión")
            estado = st.text_input("Estado del proceso")
            contraparte = st.text_input("Contraparte")
            monto = st.number_input("Monto Honorarios Pactados", 0.0)
            monto_base = st.number_input("Monto Base Cuota Litis", 0.0)
            porcentaje_litis = st.number_input("Porcentaje Cuota Litis (%)", 0.0)
            observaciones = st.text_area("Observaciones")
            guardar = st.form_submit_button("Guardar Caso")
            if guardar:
                id_caso = f"{expediente}-{año}-{cliente}"
                casos.loc[len(casos)] = [id_caso,cliente,abogado,expediente,año,materia,pretension,estado,contraparte,monto,monto_base,porcentaje_litis,observaciones]
                guardar_csv(casos,"casos.csv")
                st.success("Caso registrado")
                st.experimental_rerun()

        st.subheader("Casos Registrados")
        if not casos.empty:
            for idx,row in casos.iterrows():
                col1,col2 = st.columns([3,1])
                with col1:
                    st.write(f"{row['ID_CASO']} | Cliente: {row['Cliente']} | Abogado: {row['Abogado']} | Expediente: {row['Expediente']} | Año: {row['Año']} | Materia: {row['Materia']} | Pretensión: {row['Pretension']}")
                    st.write(f"Estado: {row['Estado']} | Contraparte: {row['Contraparte']} | Monto Honorarios: {row['Monto_Honorarios']} | Monto Base: {row['Monto_Base']} | % Cuota Litis: {row['Porcentaje_Litis']} | Observaciones: {row['Observaciones']}")
                with col2:
                    if st.button("Editar", key=f"edit_caso_{idx}"):
                        with st.form(f"form_edit_caso_{idx}"):
                            cliente_e = st.selectbox("Cliente", clientes["Nombre"], index=clientes[clientes["Nombre"]==row["Cliente"]].index[0])
                            abogado_e = st.selectbox("Abogado a Cargo", abogados["Nombre"], index=abogados[abogados["Nombre"]==row["Abogado"]].index[0])
                            expediente_e = st.text_input("Número de Expediente", row["Expediente"])
                            año_e = st.text_input("Año", row["Año"])
                            materia_e = st.text_input("Materia", row["Materia"])
                            pretension_e = st.text_input("Pretensión", row["Pretension"])
                            estado_e = st.text_input("Estado del proceso", row["Estado"])
                            contraparte_e = st.text_input("Contraparte", row["Contraparte"])
                            monto_e = st.number_input("Monto Honorarios Pactados", row["Monto_Honorarios"])
                            monto_base_e = st.number_input("Monto Base Cuota Litis", row["Monto_Base"])
                            porcentaje_litis_e = st.number_input("Porcentaje Cuota Litis (%)", row["Porcentaje_Litis"])
                            observaciones_e = st.text_area("Observaciones", row["Observaciones"])
                            submit = st.form_submit_button("Guardar Cambios")
                            if submit:
                                casos.loc[idx] = [row['ID_CASO'],cliente_e,abogado_e,expediente_e,año_e,materia_e,pretension_e,estado_e,contraparte_e,monto_e,monto_base_e,porcentaje_litis_e,observaciones_e]
                                guardar_csv(casos,"casos.csv")
                                st.success("Caso actualizado")
                                st.experimental_rerun()
                    if st.button("Eliminar", key=f"del_caso_{idx}"):
                        casos.drop(idx,inplace=True)
                        casos.reset_index(drop=True,inplace=True)
                        guardar_csv(casos,"casos.csv")
                        st.success("Caso eliminado")
                        st.experimental_rerun()

# ===============================
# PAGOS HONORARIOS
# ===============================
if menu == "Pagos Honorarios":
    st.title("Pagos de Honorarios")
    if casos.empty:
        st.warning("No hay casos registrados.")
    else:
        with st.form("form_pago"):
            caso_sel = st.selectbox("Caso", casos["ID_CASO"])
            fecha = st.date_input("Fecha de Pago", date.today())
            monto_pago = st.number_input("Monto Pagado",0.0)
            observaciones = st.text_area("Observaciones")
            guardar = st.form_submit_button("Registrar Pago")
            if guardar:
                id_pago = len(pagos)+1
                pagos.loc[len(pagos)] = [id_pago,caso_sel,fecha,monto_pago,observaciones]
                guardar_csv(pagos,"pagos.csv")
                st.success("Pago registrado")
                st.experimental_rerun()
        st.subheader("Pagos Registrados")
        if not pagos.empty:
            for idx,row in pagos.iterrows():
                st.write(f"{row['ID_PAGO']} | Caso: {row['ID_CASO']} | Fecha: {row['Fecha']} | Monto: {row['Monto']} | Observaciones: {row['Observaciones']}")
                if st.button("Eliminar", key=f"del_pago_{idx}"):
                    pagos.drop(idx,inplace=True)
                    pagos.reset_index(drop=True,inplace=True)
                    guardar_csv(pagos,"pagos.csv")
                    st.success("Pago eliminado")
                    st.experimental_rerun()

# ===============================
# CUOTA LITIS
# ===============================
if menu == "Cuota Litis":
    st.title("Cuota Litis por Caso")
    if casos.empty:
        st.warning("No hay casos registrados.")
    else:
        df = casos.copy()
        df["Monto_Cuota_Litis"] = df["Monto_Base"]*df["Porcentaje_Litis"]/100
        df["Pagado_Cuota"] = df["ID_CASO"].apply(lambda x: pagos_litis[pagos_litis["ID_CASO"]==x]["Monto"].sum() if not pagos_litis.empty else 0)
        df["Saldo_Cuota"] = df["Monto_Cuota_Litis"]-df["Pagado_Cuota"]
        st.dataframe(df[["ID_CASO","Cliente","Expediente","Monto_Base","Porcentaje_Litis","Monto_Cuota_Litis","Pagado_Cuota","Saldo_Cuota","Observaciones"]])

# ===============================
# PAGOS CUOTA LITIS
# ===============================
if menu == "Pagos Cuota Litis":
    st.title("Pagos Cuota Litis")
    if casos.empty:
        st.warning("No hay casos registrados.")
    else:
        with st.form("form_pago_litis"):
            caso_sel = st.selectbox("Caso", casos["ID_CASO"])
            fecha = st.date_input("Fecha de Pago", date.today())
            monto_pago = st.number_input("Monto Pagado",0.0)
            observaciones = st.text_area("Observaciones")
            guardar = st.form_submit_button("Registrar Pago")
            if guardar:
                id_pago = len(pagos_litis)+1
                pagos_litis.loc[len(pagos_litis)] = [id_pago,caso_sel,fecha,monto_pago,observaciones]
                guardar_csv(pagos_litis,"pagos_litis.csv")
                st.success("Pago registrado")
                st.experimental_rerun()
        st.subheader("Pagos Registrados")
        if not pagos_litis.empty:
            for idx,row in pagos_litis.iterrows():
                st.write(f"{row['ID_PAGO']} | Caso: {row['ID_CASO']} | Fecha: {row['Fecha']} | Monto: {row['Monto']} | Observaciones: {row['Observaciones']}")
                if st.button("Eliminar", key=f"del_pago_litis_{idx}"):
                    pagos_litis.drop(idx,inplace=True)
                    pagos_litis.reset_index(drop=True,inplace=True)
                    guardar_csv(pagos_litis,"pagos_litis.csv")
                    st.success("Pago eliminado")
                    st.experimental_rerun()

# ===============================
# CRONOGRAMA DE PAGOS
# ===============================
if menu == "Cronograma de Pagos":
    st.title("Cronograma de Pagos por Caso")
    if casos.empty:
        st.warning("No hay casos registrados.")
    else:
        with st.form("form_cronograma"):
            caso_sel = st.selectbox("Caso", casos["ID_CASO"])
            fecha = st.date_input("Fecha Tentativa")
            monto = st.number_input("Monto")
            observaciones = st.text_area("Observaciones")
            guardar = st.form_submit_button("Agregar al Cronograma")
            if guardar:
                id_cron = len(cronogramas)+1
                cronogramas.loc[len(cronogramas)] = [id_cron,caso_sel,fecha,monto,observaciones]
                guardar_csv(cronogramas,"cronogramas.csv")
                st.success("Registro agregado al cronograma")
                st.experimental_rerun()
        st.subheader("Cronograma Registrado")
        if not cronogramas.empty:
            st.dataframe(cronogramas)

# ===============================
# DASHBOARD
# ===============================
if menu == "Dashboard":
    st.title("Dashboard Financiero - Estudio Jurídico Roncal Liñán y Asociados ⚖️")
    total_honorarios = casos["Monto_Honorarios"].sum() if not casos.empty else 0
    total_pagado = pagos["Monto"].sum() if not pagos.empty else 0
    total_base = casos["Monto_Base"].sum() if not casos.empty else 0
    total_litis = (casos["Monto_Base"]*casos["Porcentaje_Litis"]/100).sum() if not casos.empty else 0
    total_pagado_litis = pagos_litis["Monto"].sum() if not pagos_litis.empty else 0
    total_pendiente = total_honorarios - total_pagado + total_litis - total_pagado_litis
    col1,col2,col3 = st.columns(3)
    col1.metric("Total Honorarios Pactados", f"S/ {total_honorarios:.2f}")
    col2.metric("Total Cobrado", f"S/ {total_pagado+total_pagado_litis:.
