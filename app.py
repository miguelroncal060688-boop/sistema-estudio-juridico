import streamlit as st
import pandas as pd
import os
import io
from datetime import date

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán", layout="wide")

# ===============================
# ARCHIVOS CSV
# ===============================
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
USUARIOS_CSV = "usuarios.csv"
HISTORIAL_CSV = "historial.csv"

# ===============================
# FUNCIONES AUXILIARES
# ===============================
def cargar_csv(path, columnas):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        return df[columnas]
    else:
        return pd.DataFrame(columns=columnas)

def guardar_csv(df, path):
    df.to_csv(path, index=False)

def export_df_to_excel(df,nombre_archivo):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer,index=False)
        writer.save()
    processed_data = output.getvalue()
    st.download_button(
        label=f"Exportar a Excel",
        data=processed_data,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def registrar_historial(usuario,accion):
    historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    historial_df = pd.concat([historial_df,pd.DataFrame([[usuario,accion,str(date.today())]],columns=historial_df.columns)],ignore_index=True)
    guardar_csv(historial_df,HISTORIAL_CSV)

# ===============================
# LOGIN
# ===============================
if "login" not in st.session_state:
    st.session_state.login = False

usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])
if usuarios_df.empty:
    # Crear usuario admin por defecto
    usuarios_df = pd.DataFrame([["admin","admin","admin"]],columns=usuarios_df.columns)
    guardar_csv(usuarios_df,USUARIOS_CSV)

if not st.session_state.login:
    st.title("🔒 Login")
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        user = usuarios_df[(usuarios_df["usuario"]==usuario_input)&(usuarios_df["contrasena"]==contrasena_input)]
        if not user.empty:
            st.session_state.login = True
            st.session_state.usuario = usuario_input
            st.session_state.rol = user.iloc[0]["rol"]
            st.success(f"Bienvenido {usuario_input}")
        else:
            st.error("Usuario o contraseña incorrectos")

if st.session_state.login:
    # ===============================
    # MENU
    # ===============================
    menu_items = ["Clientes","Casos","Pagos","Contratos","Historial"]
    if st.session_state.rol=="admin":
        menu_items.append("Usuarios")
    menu = st.selectbox("Menú", menu_items)
    
    # ===============================
    # CLIENTES
    # ===============================
    if menu=="Clientes":
        st.title("👥 Gestión de Clientes")
        clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
        with st.expander("➕ Nuevo Cliente"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI/RUC")
            tipo_persona = st.selectbox("Tipo",["Natural","Jurídica"])
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            direccion = st.text_input("Dirección")
            contacto_emergencia = st.text_input("Contacto de Emergencia")
            numero_contacto = st.text_input("Número de Contacto")
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar Cliente"):
                nuevo_id = str(int(clientes_df["id"].max())+1 if not clientes_df.empty else 1)
                clientes_df = pd.concat([clientes_df,pd.DataFrame([[nuevo_id,nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones]],columns=clientes_df.columns)],ignore_index=True)
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
                st.success("Cliente registrado correctamente")
        
        if not clientes_df.empty:
            st.subheader("Lista de Clientes")
            st.dataframe(clientes_df)
            export_df_to_excel(clientes_df,"clientes.xlsx")
    # ===============================
    # CASOS
    # ===============================
    if menu=="Casos":
        st.title("⚖️ Gestión de Casos")
        casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","contraparte","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","base_cuota","observaciones"])
        clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre"])
        
        with st.expander("➕ Nuevo Caso"):
            cliente_sel = st.selectbox("Cliente",clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==cliente_sel]["id"].values[0]
            numero_expediente = st.text_input("Número de Expediente")
            anio = st.number_input("Año", min_value=2000,max_value=2100,value=date.today().year)
            materia = st.text_input("Materia")
            contraparte = st.text_input("Contraparte")
            abogado = st.text_input("Abogado a cargo", value=st.session_state.usuario)
            etapa = st.text_input("Etapa procesal")
            monto_pactado = st.number_input("Monto pactado",0.0)
            pretension = st.text_input("Pretensión")
            cuota_litis = st.number_input("Cuota Litis",0.0)
            porcentaje = st.number_input("Porcentaje (%)",0.0)
            base_cuota = st.number_input("Base para cuota",0.0)
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar Caso"):
                nuevo_id = str(int(casos_df["id"].max())+1 if not casos_df.empty else 1)
                casos_df = pd.concat([casos_df,pd.DataFrame([[nuevo_id,cliente_id,numero_expediente,anio,materia,contraparte,abogado,etapa,monto_pactado,pretension,cuota_litis,porcentaje,base_cuota,observaciones]],columns=casos_df.columns)],ignore_index=True)
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró caso {numero_expediente}-{anio}")
                st.success("Caso registrado correctamente")
        
        if not casos_df.empty:
            st.subheader("Lista de Casos")
            casos_display = casos_df.merge(clientes_df, left_on="cliente_id", right_on="id",suffixes=("","_cliente"))
            st.dataframe(casos_display[["id","nombre","numero_expediente","anio","materia","contraparte","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","base_cuota","observaciones"]])
            
            # Eliminar caso
            id_eliminar = st.number_input("ID Caso a eliminar", step=1)
            if st.button("Eliminar Caso"):
                if str(id_eliminar) in casos_df["id"].values:
                    casos_df = casos_df[casos_df["id"]!=str(id_eliminar)]
                    guardar_csv(casos_df,CASOS_CSV)
                    st.success(f"Caso {id_eliminar} eliminado")
            
    # ===============================
    # PAGOS
    # ===============================
    if menu=="Pagos":
        st.title("💰 Gestión de Pagos")
        pagos_df = cargar_csv(PAGOS_CSV, ["id","caso_id","fecha","tipo","monto","observaciones"])
        casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio"])
        clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre"])
        
        with st.expander("➕ Nuevo Pago"):
            # Seleccionar caso
            casos_df["descripcion"] = casos_df["numero_expediente"].astype(str)+"-"+casos_df["anio"].astype(str)+" | "+clientes_df.set_index("id").loc[casos_df["cliente_id"].astype(str)]["nombre"].values
            seleccion = st.selectbox("Seleccionar Caso",casos_df["descripcion"])
            partes = seleccion.split("|")
            expediente_info = partes[0].strip().split("-")
            expediente = expediente_info[0]
            anio_caso = int(expediente_info[1])
            caso_sel = casos_df[(casos_df["numero_expediente"]==expediente)&(casos_df["anio"]==anio_caso)]
            if not caso_sel.empty:
                caso_id = caso_sel.iloc[0]["id"]
                fecha = st.date_input("Fecha")
                tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
                monto = st.number_input("Monto",0.0)
                obs = st.text_area("Observaciones")
                if st.button("Guardar Pago"):
                    nuevo_id = str(int(pagos_df["id"].max())+1 if not pagos_df.empty else 1)
                    pagos_df = pd.concat([pagos_df,pd.DataFrame([[nuevo_id,caso_id,str(fecha),tipo,monto,obs]],columns=pagos_df.columns)],ignore_index=True)
                    guardar_csv(pagos_df,PAGOS_CSV)
                    registrar_historial(st.session_state.usuario,f"Registró pago caso {expediente}-{anio_caso}")
                    st.success("Pago registrado correctamente")
        
        if not pagos_df.empty:
            pagos_display = pagos_df.merge(casos_df,left_on="caso_id",right_on="id",suffixes=("","_caso"))
            pagos_display = pagos_display.merge(clientes_df,left_on="cliente_id",right_on="id",suffixes=("","_cliente"))
            st.subheader("Lista de Pagos")
            st.dataframe(pagos_display[["id","nombre","numero_expediente","anio","fecha","tipo","monto","observaciones"]])
            export_df_to_excel(pagos_display,"pagos.xlsx")
            
            # Eliminar pago
            id_eliminar = st.number_input("ID Pago a eliminar", step=1,key="pago_elim")
            if st.button("Eliminar Pago",key="elim_pago"):
                if str(id_eliminar) in pagos_df["id"].values:
                    pagos_df = pagos_df[pagos_df["id"]!=str(id_eliminar)]
                    guardar_csv(pagos_df,PAGOS_CSV)
                    st.success(f"Pago {id_eliminar} eliminado")
