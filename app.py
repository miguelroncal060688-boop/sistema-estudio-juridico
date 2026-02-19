import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

st.title("⚖️ ESTUDIO JURÍDICO RONCAL LIÑÁN Y ASOCIADOS")

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
        "clientes": ["ID","Nombre"],
        "abogados": ["ID","Nombre"],
        "casos": ["ID","Cliente","Abogado","Expediente","Año"],
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

def load(name):
    df = pd.read_csv(FILES[name])
    if "ID" in df.columns:
        df = df[df["ID"] != 0]
        df["ID"] = df["ID"].astype(int)
    return df

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
# ADMIN POR DEFECTO
# ==============================

if usuarios.empty:
    usuarios.loc[0] = [1,"admin","estudio123","admin",""]
    save("usuarios", usuarios)
    usuarios = load("usuarios")

# ==============================
# LOGIN
# ==============================

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.rol = None
    st.session_state.abogado = None

if st.session_state.user is None:
    st.subheader("Ingreso al Sistema")
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

st.sidebar.write(f"Usuario: {st.session_state.user}")
st.sidebar.write(f"Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

menu = st.sidebar.selectbox("Menú", [
    "Dashboard","Clientes","Abogados","Casos",
    "Honorarios","Pagos Honorarios",
    "Cuota Litis","Pagos Cuota Litis",
    "Pendientes","Resumen Financiero","Reporte por Cliente"
])

# ==============================
# FUNCION ELIMINAR
# ==============================

def eliminar_registro(df, nombre):
    if df.empty:
        st.info("No hay registros.")
        return df

    st.dataframe(df, use_container_width=True)
    id_sel = st.selectbox("Seleccionar ID a eliminar", df["ID"])
    if st.button("Eliminar"):
        df = df[df["ID"] != id_sel]
        save(nombre, df)
        st.success("Eliminado correctamente")
        st.rerun()
    return df

# ==============================
# DASHBOARD
# ==============================

if menu == "Dashboard":

    total_pactado = honorarios["Monto Pactado"].sum() if not honorarios.empty else 0
    total_pagado = pagos_honorarios["Monto"].sum() if not pagos_honorarios.empty else 0
    pendiente = total_pactado - total_pagado

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Pactado", f"S/ {total_pactado:,.2f}")
    col2.metric("Total Cobrado", f"S/ {total_pagado:,.2f}")
    col3.metric("Pendiente", f"S/ {pendiente:,.2f}")

# ==============================
# CLIENTES
# ==============================

if menu == "Clientes":
    nombre = st.text_input("Nombre Cliente")
    if st.button("Guardar Cliente"):
        nuevo = clientes["ID"].max()+1 if not clientes.empty else 1
        clientes.loc[len(clientes)] = [nuevo,nombre]
        save("clientes", clientes)
        st.rerun()
    clientes = eliminar_registro(clientes,"clientes")

# ==============================
# ABOGADOS
# ==============================

if menu == "Abogados":
    nombre = st.text_input("Nombre Abogado")
    if st.button("Guardar Abogado"):
        nuevo = abogados["ID"].max()+1 if not abogados.empty else 1
        abogados.loc[len(abogados)] = [nuevo,nombre]
        save("abogados", abogados)
        st.rerun()
    abogados = eliminar_registro(abogados,"abogados")

# ==============================
# CASOS
# ==============================

if menu == "Casos":
    cliente = st.selectbox("Cliente", clientes["Nombre"])
    abogado = st.selectbox("Abogado", abogados["Nombre"])
    expediente = st.text_input("Expediente")
    año = st.text_input("Año")

    if st.button("Guardar Caso"):
        nuevo = casos["ID"].max()+1 if not casos.empty else 1
        casos.loc[len(casos)] = [nuevo,cliente,abogado,expediente,año]
        save("casos", casos)
        st.rerun()

    casos = eliminar_registro(casos,"casos")

# ==============================
# HONORARIOS + CRONOGRAMA
# ==============================

if menu == "Honorarios":

    casos_merge = casos.copy()
    casos_merge["Descripcion"] = (
        casos_merge["ID"].astype(str) + " | " +
        casos_merge["Cliente"] + " | Exp: " +
        casos_merge["Expediente"] + " | Año: " +
        casos_merge["Año"]
    )

    caso_sel = st.selectbox("Seleccionar Caso", casos_merge["Descripcion"])
    caso_id = casos_merge[casos_merge["Descripcion"]==caso_sel]["ID"].values[0]

    monto = st.number_input("Monto Pactado", min_value=0.0)

    if st.button("Registrar Honorario"):
        nuevo = honorarios["ID"].max()+1 if not honorarios.empty else 1
        honorarios.loc[len(honorarios)] = [nuevo,caso_id,monto]
        save("honorarios", honorarios)
        st.rerun()

    st.subheader("Cronograma")
    fecha = st.date_input("Fecha")
    monto_crono = st.number_input("Monto Cuota", min_value=0.0)
    estado = st.selectbox("Estado",["Pendiente","Pagado"])

    if st.button("Agregar Cuota"):
        nuevo = cronograma["ID"].max()+1 if not cronograma.empty else 1
        cronograma.loc[len(cronograma)] = [nuevo,caso_id,fecha,monto_crono,estado]
        save("cronograma", cronograma)
        st.rerun()

    honorarios = eliminar_registro(honorarios,"honorarios")

# ==============================
# PAGOS HONORARIOS
# ==============================

if menu == "Pagos Honorarios":
    caso = st.selectbox("Caso", casos["ID"])
    monto = st.number_input("Monto Pagado", min_value=0.0)
    if st.button("Registrar Pago"):
        nuevo = pagos_honorarios["ID"].max()+1 if not pagos_honorarios.empty else 1
        pagos_honorarios.loc[len(pagos_honorarios)] = [nuevo,caso,monto]
        save("pagos_honorarios", pagos_honorarios)
        st.rerun()
    pagos_honorarios = eliminar_registro(pagos_honorarios,"pagos_honorarios")

# ==============================
# CUOTA LITIS
# ==============================

if menu == "Cuota Litis":
    caso = st.selectbox("Caso", casos["ID"])
    base = st.number_input("Monto Base", min_value=0.0)
    porc = st.number_input("Porcentaje", min_value=0.0)
    if st.button("Guardar Cuota Litis"):
        nuevo = cuota_litis["ID"].max()+1 if not cuota_litis.empty else 1
        cuota_litis.loc[len(cuota_litis)] = [nuevo,caso,base,porc]
        save("cuota_litis", cuota_litis)
        st.rerun()
    cuota_litis = eliminar_registro(cuota_litis,"cuota_litis")

# ==============================
# PAGOS CUOTA LITIS
# ==============================

if menu == "Pagos Cuota Litis":
    caso = st.selectbox("Caso", casos["ID"])
    monto = st.number_input("Monto Pagado", min_value=0.0)
    if st.button("Registrar Pago"):
        nuevo = pagos_litis["ID"].max()+1 if not pagos_litis.empty else 1
        pagos_litis.loc[len(pagos_litis)] = [nuevo,caso,monto]
        save("pagos_litis", pagos_litis)
        st.rerun()
    pagos_litis = eliminar_registro(pagos_litis,"pagos_litis")

# ==============================
# PENDIENTES
# ==============================

if menu == "Pendientes":

    st.subheader("Pendientes Cronograma")
    pendientes_crono = cronograma[cronograma["Estado"]=="Pendiente"]
    st.dataframe(pendientes_crono)

    st.subheader("Pendientes Honorarios")
    if not honorarios.empty:
        total_pactado = honorarios.groupby("CasoID")["Monto Pactado"].sum()
        total_pagado = pagos_honorarios.groupby("CasoID")["Monto"].sum()
        resumen = pd.DataFrame({
            "Pactado": total_pactado,
            "Pagado": total_pagado
        }).fillna(0)
        resumen["Pendiente"] = resumen["Pactado"] - resumen["Pagado"]
        st.dataframe(resumen)

# ==============================
# RESUMEN FINANCIERO
# ==============================

if menu == "Resumen Financiero":

    st.subheader("Resumen Honorarios")
    if not honorarios.empty:
        tabla = honorarios.merge(casos, left_on="CasoID", right_on="ID")
        st.dataframe(tabla[["Cliente","Expediente","Año","Monto Pactado"]])

    st.subheader("Resumen Cuota Litis")
    if not cuota_litis.empty:
        tabla2 = cuota_litis.merge(casos, left_on="CasoID", right_on="ID")
        st.dataframe(tabla2[["Cliente","Expediente","Monto Base","Porcentaje"]])

# ==============================
# REPORTE POR CLIENTE
# ==============================

if menu == "Reporte por Cliente":
    cliente_sel = st.selectbox("Seleccionar Cliente", clientes["Nombre"])
    casos_cli = casos[casos["Cliente"]==cliente_sel]
    st.dataframe(casos_cli)
