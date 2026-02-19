import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados ⚖️", layout="wide")

# ===== LOGIN =====
PASSWORD = "estudio123"
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("Acceso al Sistema")
    pwd = st.text_input("Ingrese contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == PASSWORD:
            st.session_state.login = True
            st.experimental_rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

# ===== FUNCIONES DE CSV =====
def cargar_csv(nombre, columnas):
    if os.path.exists(nombre):
        df = pd.read_csv(nombre)
        # Asegurar columnas
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=columnas)

def guardar_csv(df, nombre):
    df.to_csv(nombre, index=False)

# ===== INICIALIZAR DATOS =====
clientes_cols = ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"]
casos_cols = ["ID","Cliente_ID","Expediente","Año","Materia","Pretension","Estado","Contraparte","Monto_Honorarios","Monto_Base","Cuota_Litis","Observaciones"]
pagos_cols = ["ID","Caso_ID","Fecha","Monto","Observaciones"]
pagos_litis_cols = ["ID","Caso_ID","Fecha","Monto","Observaciones"]
abogados_cols = ["ID","Nombre","DNI","Correo","Celular","Colegiatura","Direccion_Proc","Casilla_E","Casilla_J"]

clientes = cargar_csv("clientes.csv", clientes_cols)
casos = cargar_csv("casos.csv", casos_cols)
pagos = cargar_csv("pagos.csv", pagos_cols)
pagos_litis = cargar_csv("pagos_litis.csv", pagos_litis_cols)
abogados = cargar_csv("abogados.csv", abogados_cols)

# ===== MENÚ =====
menu = st.sidebar.selectbox("Menú", [
    "Dashboard","Clientes","Abogados","Casos","Pagos Honorarios","Pagos Cuota Litis",
    "Cronograma de Pagos","Cuota Litis","Pendientes de Cobrar","Resumen Financiero","Reporte por Cliente"
])

# ===== CLIENTES =====
if menu=="Clientes":
    st.title("Gestión de Clientes")
    with st.form("form_cliente"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        observaciones = st.text_area("Observaciones")
        submitted = st.form_submit_button("Guardar Cliente")
        if submitted:
            new_id = len(clientes)+1
            clientes.loc[len(clientes)] = [new_id,nombre,dni,celular,correo,direccion,observaciones]
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente agregado")
            st.experimental_rerun()

    st.subheader("Clientes registrados")
    if not clientes.empty:
        for idx,row in clientes.iterrows():
            st.write(row)
            col1,col2 = st.columns(2)
            if col1.button(f"Editar {row['Nombre']}", key=f"edit_cliente_{idx}"):
                with st.form(f"edit_form_cliente_{idx}"):
                    nombre_e = st.text_input("Nombre",row["Nombre"])
                    dni_e = st.text_input("DNI",row["DNI"])
                    celular_e = st.text_input("Celular",row["Celular"])
                    correo_e = st.text_input("Correo",row["Correo"])
                    direccion_e = st.text_input("Dirección",row["Direccion"])
                    obs_e = st.text_area("Observaciones",row["Observaciones"])
                    submit_edit = st.form_submit_button("Guardar cambios")
                    if submit_edit:
                        clientes.loc[idx] = [row["ID"],nombre_e,dni_e,celular_e,correo_e,direccion_e,obs_e]
                        guardar_csv(clientes,"clientes.csv")
                        st.success("Cliente actualizado")
                        st.experimental_rerun()
            if col2.button(f"Eliminar {row['Nombre']}", key=f"del_cliente_{idx}"):
                clientes.drop(idx,inplace=True)
                clientes.reset_index(drop=True,inplace=True)
                guardar_csv(clientes,"clientes.csv")
                st.success("Cliente eliminado")
                st.experimental_rerun()

# ===== ABOGADOS =====
if menu=="Abogados":
    st.title("Gestión de Abogados")
    with st.form("form_abogado"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        correo = st.text_input("Correo")
        celular = st.text_input("Celular")
        colegiatura = st.text_input("Colegiatura")
        direccion_proc = st.text_input("Dirección Procesal")
        casilla_e = st.text_input("Casilla Electrónica")
        casilla_j = st.text_input("Casilla Judicial")
        submitted = st.form_submit_button("Guardar Abogado")
        if submitted:
            new_id = len(abogados)+1
            abogados.loc[len(abogados)] = [new_id,nombre,dni,correo,celular,colegiatura,direccion_proc,casilla_e,casilla_j]
            guardar_csv(abogados,"abogados.csv")
            st.success("Abogado agregado")
            st.experimental_rerun()

    st.subheader("Abogados registrados")
    if not abogados.empty:
        for idx,row in abogados.iterrows():
            st.write(row)
            col1,col2 = st.columns(2)
            if col1.button(f"Editar {row['Nombre']}", key=f"edit_abogado_{idx}"):
                with st.form(f"edit_form_abogado_{idx}"):
                    nombre_e = st.text_input("Nombre",row["Nombre"])
                    dni_e = st.text_input("DNI",row["DNI"])
                    correo_e = st.text_input("Correo",row["Correo"])
                    celular_e = st.text_input("Celular",row["Celular"])
                    colegiatura_e = st.text_input("Colegiatura",row["Colegiatura"])
                    direccion_proc_e = st.text_input("Dirección Procesal",row["Direccion_Proc"])
                    casilla_e_e = st.text_input("Casilla Electrónica",row["Casilla_E"])
                    casilla_j_e = st.text_input("Casilla Judicial",row["Casilla_J"])
                    submit_edit = st.form_submit_button("Guardar cambios")
                    if submit_edit:
                        abogados.loc[idx] = [row["ID"],nombre_e,dni_e,correo_e,celular_e,colegiatura_e,direccion_proc_e,casilla_e_e,casilla_j_e]
                        guardar_csv(abogados,"abogados.csv")
                        st.success("Abogado actualizado")
                        st.experimental_rerun()
            if col2.button(f"Eliminar {row['Nombre']}", key=f"del_abogado_{idx}"):
                abogados.drop(idx,inplace=True)
                abogados.reset_index(drop=True,inplace=True)
                guardar_csv(abogados,"abogados.csv")
                st.success("Abogado eliminado")
                st.experimental_rerun()

# ===== CASOS =====
if menu=="Casos":
    st.title("Gestión de Casos")
    if not clientes.empty:
        with st.form("form_caso"):
            cliente_sel = st.selectbox("Cliente", clientes["Nombre"])
            expediente = st.text_input("Número de expediente")
            año = st.text_input("Año")
            materia = st.text_input("Materia")
            pretension = st.text_input("Pretensión")
            estado = st.text_input("Estado")
            contraparte = st.text_input("Contraparte")
            monto = st.number_input("Monto honorarios",0.0)
            monto_base = st.number_input("Monto Base",0.0)
            cuota_litis = st.number_input("Cuota Litis (%)",0.0)
            observaciones = st.text_area("Observaciones")
            submitted = st.form_submit_button("Guardar Caso")
            if submitted:
                new_id = len(casos)+1
                cliente_id = clientes[clientes["Nombre"]==cliente_sel]["ID"].values[0]
                casos.loc[len(casos)] = [new_id,cliente_id,expediente,año,materia,pretension,estado,contraparte,monto,monto_base,cuota_litis,observaciones]
                guardar_csv(casos,"casos.csv")
                st.success("Caso agregado")
                st.experimental_rerun()
        st.subheader("Casos registrados")
        if not casos.empty:
            for idx,row in casos.iterrows():
                cliente_nombre = clientes[clientes["ID"]==row["Cliente_ID"]]["Nombre"].values[0]
                st.write({
                    "Expediente": row["Expediente"],
                    "Año": row["Año"],
                    "Cliente": cliente_nombre,
                    "Materia": row["Materia"],
                    "Pretensión": row["Pretension"],
                    "Estado": row["Estado"],
                    "Contraparte": row["Contraparte"],
                    "Monto Honorarios": row["Monto_Honorarios"],
                    "Monto Base": row["Monto_Base"],
                    "Cuota Litis (%)": row["Cuota_Litis"],
                    "Observaciones": row["Observaciones"]
                })
                col1,col2 = st.columns(2)
                if col1.button(f"Editar {row['Expediente']}", key=f"edit_caso_{idx}"):
                    with st.form(f"edit_form_caso_{idx}"):
                        expediente_e = st.text_input("Expediente",row["Expediente"])
                        año_e = st.text_input("Año",row["Año"])
                        cliente_idx = clientes[clientes["ID"]==row["Cliente_ID"]].index[0]
                        cliente_e = st.selectbox("Cliente", clientes["Nombre"], index=cliente_idx)
                        materia_e = st.text_input("Materia",row["Materia"])
                        pretension_e = st.text_input("Pretensión",row["Pretension"])
                        estado_e = st.text_input("Estado",row["Estado"])
                        contraparte_e = st.text_input("Contraparte",row["Contraparte"])
                        monto_e = st.number_input("Monto honorarios",row["Monto_Honorarios"])
                        monto_base_e = st.number_input("Monto Base",row["Monto_Base"])
                        cuota_litis_e = st.number_input("Cuota Litis (%)",row["Cuota_Litis"])
                        observaciones_e = st.text_area("Observaciones",row["Observaciones"])
                        submit_edit = st.form_submit_button("Guardar cambios")
                        if submit_edit:
                            cliente_id_e = clientes[clientes["Nombre"]==cliente_e]["ID"].values[0]
                            casos.loc[idx] = [row["ID"],cliente_id_e,expediente_e,año_e,materia_e,pretension_e,estado_e,contraparte_e,monto_e,monto_base_e,cuota_litis_e,observaciones_e]
                            guardar_csv(casos,"casos.csv")
                            st.success("Caso actualizado")
                            st.experimental_rerun()
                if col2.button(f"Eliminar {row['Expediente']}", key=f"del_caso_{idx}"):
                    casos.drop(idx,inplace=True)
                    casos.reset_index(drop=True,inplace=True)
                    guardar_csv(casos,"casos.csv")
                    st.success("Caso eliminado")
                    st.experimental_rerun()

# ===== PAGOS HONORARIOS =====
if menu=="Pagos Honorarios":
    st.title("Pagos de Honorarios")
    if not casos.empty:
        with st.form("form_pago"):
            caso_sel = st.selectbox("Caso", casos["ID"])
            fecha = st.date_input("Fecha", value=date.today())
            monto = st.number_input("Monto",0.0)
            observaciones = st.text_area("Observaciones")
            submitted = st.form_submit_button("Registrar Pago")
            if submitted:
                new_id = len(pagos)+1
                pagos.loc[len(pagos)] = [new_id,caso_sel,fecha,monto,observaciones]
                guardar_csv(pagos,"pagos.csv")
                st.success("Pago registrado")
                st.experimental_rerun()
        st.subheader("Pagos registrados")
        if not pagos.empty:
            for idx,row in pagos.iterrows():
                caso_info = casos[casos["ID"]==row["Caso_ID"]]
                cliente_nombre = clientes[clientes["ID"]==caso_info["Cliente_ID"].values[0]]["Nombre"].values[0]
                st.write({
                    "Caso": row["Caso_ID"],
                    "Cliente": cliente_nombre,
                    "Fecha": row["Fecha"],
                    "Monto": row["Monto"],
                    "Observaciones": row["Observaciones"]
                })
                if st.button(f"Eliminar pago {row['ID']}", key=f"del_pago_{idx}"):
                    pagos.drop(idx,inplace=True)
                    pagos.reset_index(drop=True,inplace=True)
                    guardar_csv(pagos,"pagos.csv")
                    st.success("Pago eliminado")
                    st.experimental_rerun()

# ===== PAGOS CUOTA LITIS =====
if menu=="Pagos Cuota Litis":
    st.title("Pagos de Cuota Litis")
    if not casos.empty:
        with st.form("form_pago_litis"):
            caso_sel = st.selectbox("Caso", casos["ID"])
            fecha = st.date_input("Fecha", value=date.today())
            monto = st.number_input("Monto",0.0)
            observaciones = st.text_area("Observaciones")
            submitted = st.form_submit_button("Registrar Pago Cuota Litis")
            if submitted:
                new_id = len(pagos_litis)+1
                pagos_litis.loc[len(pagos_litis)] = [new_id,caso_sel,fecha,monto,observaciones]
                guardar_csv(pagos_litis,"pagos_litis.csv")
                st.success("Pago de cuota litis registrado")
                st.experimental_rerun()
        st.subheader("Pagos registrados")
        if not pagos_litis.empty:
            for idx,row in pagos_litis.iterrows():
                caso_info = casos[casos["ID"]==row["Caso_ID"]]
                cliente_nombre = clientes[clientes["ID"]==caso_info["Cliente_ID"].values[0]]["Nombre"].values[0]
                st.write({
                    "Caso": row["Caso_ID"],
                    "Cliente": cliente_nombre,
                    "Fecha": row["Fecha"],
                    "Monto": row["Monto"],
                    "Observaciones": row["Observaciones"]
                })
                if st.button(f"Eliminar pago {row['ID']}", key=f"del_pago_litis_{idx}"):
                    pagos_litis.drop(idx,inplace=True)
                    pagos_litis.reset_index(drop=True,inplace=True)
                    guardar_csv(pagos_litis,"pagos_litis.csv")
                    st.success("Pago eliminado")
                    st.experimental_rerun()
