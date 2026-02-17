import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sistema Jurídico PRO", layout="wide")

# ===== LOGIN =====
PASSWORD = "estudio123"
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("Acceso al Sistema Jurídico")
    pwd = st.text_input("Ingrese contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == PASSWORD:
            st.session_state.login = True
            st.experimental_rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# ===== FUNCIONES =====
def cargar_csv(nombre):
    if os.path.exists(nombre):
        return pd.read_csv(nombre)
    return pd.DataFrame()

def guardar_csv(df, nombre):
    df.to_csv(nombre, index=False)

# ===== DATOS =====
clientes = cargar_csv("clientes.csv")
casos = cargar_csv("casos.csv")
pagos = cargar_csv("pagos.csv")

# ===== MENÚ =====
menu = st.sidebar.selectbox("Menú", ["Dashboard","Clientes","Casos","Pagos","Cuota Litis"])

# ===== CLIENTES =====
if menu == "Clientes":
    st.title("Gestión de Clientes")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        observaciones = st.text_area("Observaciones")  # Nuevo campo
        submitted = st.form_submit_button("Guardar Cliente", key="guardar_cliente")
        if submitted:
            nuevo = pd.DataFrame([{
                "Nombre": nombre,
                "DNI": dni,
                "Celular": celular,
                "Correo": correo,
                "Dirección": direccion,
                "Observaciones": observaciones
            }])
            clientes = pd.concat([clientes, nuevo], ignore_index=True)
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente agregado")
            st.experimental_rerun()

    st.subheader("Clientes registrados")
    if not clientes.empty:
        sel_cliente = st.selectbox("Selecciona Cliente para Editar/Eliminar", clientes["Nombre"], key="sel_cliente")
        idx = clientes[clientes["Nombre"]==sel_cliente].index[0]
        st.write(clientes.loc[idx])
        col1,col2 = st.columns(2)
        if col1.button("Editar Cliente", key=f"edit_cliente_{idx}"):
            with st.form(f"edit_cliente_form_{idx}"):
                nombre_e = st.text_input("Nombre completo", clientes.loc[idx,"Nombre"])
                dni_e = st.text_input("DNI", clientes.loc[idx,"DNI"])
                celular_e = st.text_input("Celular", clientes.loc[idx,"Celular"])
                correo_e = st.text_input("Correo", clientes.loc[idx,"Correo"])
                direccion_e = st.text_input("Dirección", clientes.loc[idx,"Dirección"])
                observaciones_e = st.text_area("Observaciones", clientes.loc[idx,"Observaciones"])
                submit_edit = st.form_submit_button("Guardar Cambios", key=f"submit_edit_cliente_{idx}")
                if submit_edit:
                    clientes.loc[idx] = [nombre_e,dni_e,celular_e,correo_e,direccion_e,observaciones_e]
                    guardar_csv(clientes,"clientes.csv")
                    st.success("Cliente actualizado")
                    st.experimental_rerun()
        if col2.button("Eliminar Cliente", key=f"del_cliente_{idx}"):
            clientes.drop(idx, inplace=True)
            clientes.reset_index(drop=True,inplace=True)
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente eliminado")
            st.experimental_rerun()

# ===== CASOS =====
if menu == "Casos":
    st.title("Gestión de Casos")

    with st.form("form_caso"):
        cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [], key="cliente_nuevo")
        expediente = st.text_input("Número de expediente")
        año = st.text_input("Año")
        materia = st.text_input("Materia")
        monto = st.number_input("Monto pactado", 0.0)
        cuota_litis = st.number_input("Cuota Litis (%)",0.0)
        monot_base = st.number_input("Monto Base",0.0)
        contraparte = st.text_input("Contraparte")
        observaciones = st.text_area("Observaciones")  # Nuevo campo
        submitted = st.form_submit_button("Guardar Caso", key="guardar_caso")
        if submitted:
            identificador = f"{expediente}-{año}-{cliente}"
            nuevo = pd.DataFrame([{
                "ID_CASO": identificador,
                "Cliente": cliente,
                "Expediente": expediente,
                "Año": año,
                "Materia": materia,
                "Monto": monto,
                "Cuota_Litis": cuota_litis,
                "Monot_Base": monot_base,
                "Contraparte": contraparte,
                "Observaciones": observaciones
            }])
            casos = pd.concat([casos,nuevo],ignore_index=True)
            guardar_csv(casos,"casos.csv")
            st.success("Caso agregado")
            st.experimental_rerun()

    st.subheader("Casos registrados")
    if not casos.empty:
        sel_caso = st.selectbox("Selecciona Caso para Editar/Eliminar", casos["ID_CASO"], key="sel_caso")
        idx = casos[casos["ID_CASO"]==sel_caso].index[0]
        st.write(casos.loc[idx])
        col1,col2 = st.columns(2)
        if col1.button("Editar Caso", key=f"edit_caso_{idx}"):
            with st.form(f"edit_caso_form_{idx}"):
                expediente_e = st.text_input("Número de expediente", casos.loc[idx,"Expediente"])
                año_e = st.text_input("Año", casos.loc[idx,"Año"])
                cliente_e = st.selectbox("Cliente", clientes["Nombre"], index=clientes[clientes["Nombre"]==casos.loc[idx,"Cliente"]].index[0], key=f"cliente_edit_{idx}")
                materia_e = st.text_input("Materia", casos.loc[idx,"Materia"])
                monto_e = st.number_input("Monto pactado", casos.loc[idx,"Monto"])
                cuota_litis_e = st.number_input("Cuota Litis (%)", casos.loc[idx,"Cuota_Litis"])
                monot_base_e = st.number_input("Monto Base", casos.loc[idx,"Monot_Base"])
                contraparte_e = st.text_input("Contraparte", casos.loc[idx,"Contraparte"])
                observaciones_e = st.text_area("Observaciones", casos.loc[idx,"Observaciones"])
                submit_edit = st.form_submit_button("Guardar Cambios", key=f"submit_edit_caso_{idx}")
                if submit_edit:
                    casos.loc[idx] = [f"{expediente_e}-{año_e}-{cliente_e}", cliente_e, expediente_e, año_e, materia_e, monto_e, cuota_litis_e, monot_base_e, contraparte_e, observaciones_e]
                    guardar_csv(casos,"casos.csv")
                    st.success("Caso actualizado")
                    st.experimental_rerun()
        if col2.button("Eliminar Caso", key=f"del_caso_{idx}"):
            casos.drop(idx,inplace=True)
            casos.reset_index(drop=True,inplace=True)
            guardar_csv(casos,"casos.csv")
            st.success("Caso eliminado")
            st.experimental_rerun()

# ===== PAGOS =====
if menu == "Pagos":
    st.title("Registro de Pagos")

    if not clientes.empty and not casos.empty:
        with st.form("form_pago"):
            caso_sel = st.selectbox("Caso", casos["ID_CASO"], key="caso_pago")
            cliente_sel = st.selectbox("Cliente", clientes["Nombre"], key="cliente_pago")
            fecha = st.date_input("Fecha")
            monto_pago = st.number_input("Monto pagado",0.0)
            observaciones = st.text_area("Observaciones")  # Nuevo campo
            submitted = st.form_submit_button("Registrar Pago", key="guardar_pago")
            if submitted:
                nuevo = pd.DataFrame([{
                    "ID_CASO": caso_sel,
                    "Cliente": cliente_sel,
                    "Fecha": fecha,
                    "Monto": monto_pago,
                    "Observaciones": observaciones
                }])
                pagos = pd.concat([pagos,nuevo],ignore_index=True)
                guardar_csv(pagos,"pagos.csv")
                st.success("Pago registrado")
                st.experimental_rerun()

    st.subheader("Pagos registrados")
    if not pagos.empty:
        sel_pago = st.selectbox("Selecciona Pago para eliminar", pagos.index, key="sel_pago")
        p = pagos.loc[sel_pago]
        st.write(p)
        if st.button("Eliminar Pago", key=f"del_pago_{sel_pago}"):
            pagos.drop(sel_pago,inplace=True)
            pagos.reset_index(drop=True,inplace=True)
            guardar_csv(pagos,"pagos.csv")
            st.success("Pago eliminado")
            st.experimental_rerun()

# ===== DASHBOARD =====
if menu == "Dashboard":
    st.title("Dashboard Financiero")
    
    total_clientes = len(clientes)
    total_casos = len(casos)
    total_ingresos = pagos["Monto"].sum() if not pagos.empty else 0

    if not casos.empty:
        df_saldo = casos.copy()
        for col in ["Contraparte","Monto"]:
            if col not in df_saldo.columns:
                df_saldo[col] = "" if col=="Contraparte" else 0.0
        df_saldo["Pagado"] = df_saldo["ID_CASO"].apply(
            lambda x: pagos[pagos["ID_CASO"]==x]["Monto"].sum() if not pagos.empty else 0
        )
        df_saldo["Saldo"] = df_saldo["Monto"] - df_saldo["Pagado"]
        total_pendiente = df_saldo["Saldo"].sum()
    else:
        df_saldo = pd.DataFrame(columns=["ID_CASO","Cliente","Contraparte","Monto","Pagado","Saldo"])
        total_pendiente = 0

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_ingresos:.2f}")
    col4.metric("Pendiente", f"S/ {total_pendiente:.2f}")

    st.subheader("Seguimiento de Pagos por Caso")
    if not df_saldo.empty:
        st.dataframe(df_saldo[["ID_CASO","Cliente","Contraparte","Monto","Pagado","Saldo","Observaciones"]])
    else:
        st.write("No hay casos registrados.")

# ===== PESTAÑA CUOTA LITIS SIMPLE =====
if menu == "Cuota Litis":
    st.title("Cuota Litis por Caso")
    if not casos.empty:
        df_litis = casos.copy()
        df_litis["Monto_Cuota_Litis"] = df_litis["Monto"] * df_litis["Cuota_Litis"]/100
        st.dataframe(df_litis[["Cliente","Expediente","Cuota_Litis","Monto_Cuota_Litis","Observaciones"]])
    else:
        st.write("No hay casos registrados.")
