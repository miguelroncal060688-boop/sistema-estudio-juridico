import streamlit as st
import pandas as pd
import io
from datetime import date

# ===============================
# CONFIGURACIÓN CSVs
# ===============================
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
USUARIOS_CSV = "usuarios.csv"
HISTORIAL_CSV = "historial.csv"

# ===============================
# FUNCIONES UTILES
# ===============================
def cargar_csv(ruta, columnas):
    try:
        df = pd.read_csv(ruta)
    except FileNotFoundError:
        df = pd.DataFrame(columns=columnas)
        df.to_csv(ruta,index=False)
    return df

def guardar_csv(df,ruta):
    df.to_csv(ruta,index=False)

def registrar_historial(usuario,accion):
    historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    historial_df = pd.concat([historial_df,pd.DataFrame([[usuario,accion,str(date.today())]],columns=historial_df.columns)],ignore_index=True)
    guardar_csv(historial_df,HISTORIAL_CSV)

def export_df_to_excel(df,filename):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.save()
    processed_data = output.getvalue()
    st.download_button(
        label=f"Exportar a Excel",
        data=processed_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ===============================
# SESIÓN
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario = ""
    st.session_state.rol = ""

# ===============================
# LOGIN
# ===============================
if not st.session_state.logged_in:
    st.title("🔐 Login Estudio Jurídico")
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])
    if st.button("Ingresar"):
        if not usuarios_df.empty and not usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)].empty:
            st.session_state.logged_in = True
            st.session_state.usuario = usuario_input
            st.session_state.rol = usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)]["rol"].values[0]
            registrar_historial(usuario_input,"Inicio sesión")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# ===============================
# MENU PRINCIPAL
# ===============================
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menú", ["Clientes","Casos","Pagos","Contratos","Historial","Usuarios","Cerrar Sesión"])
    if menu=="Cerrar Sesión":
        st.session_state.logged_in = False
        st.session_state.usuario = ""
        st.session_state.rol = ""
        st.experimental_rerun()

# ===============================
# CLIENTES
# ===============================
if menu=="Clientes":
    st.title("👥 Gestión de Clientes")
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    
    with st.expander("➕ Nuevo Cliente"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI/RUC")
        tipo_persona = st.selectbox("Tipo Persona", ["Natural","Jurídica"])
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        contacto_emergencia = st.text_input("Contacto de Emergencia")
        numero_contacto = st.text_input("Número Contacto")
        observaciones = st.text_area("Observaciones")
        if st.button("Guardar Cliente"):
            nuevo_id = str(int(clientes_df["id"].max())+1 if not clientes_df.empty else 1)
            clientes_df = pd.concat([clientes_df,pd.DataFrame([[nuevo_id,nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones]],columns=clientes_df.columns)],ignore_index=True)
            guardar_csv(clientes_df,CLIENTES_CSV)
            registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
            st.success("Cliente registrado correctamente")
            st.experimental_rerun()

    if not clientes_df.empty:
        st.subheader("Lista de Clientes")
        st.dataframe(clientes_df)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            clientes_df.to_excel(writer, index=False, sheet_name='Clientes')
            writer.save()
        processed_data = output.getvalue()

        st.download_button(
            label="Exportar Clientes a Excel",
            data=processed_data,
            file_name="clientes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
# ===============================
# CASOS
# ===============================
if menu=="Casos":
    st.title("⚖️ Gestión de Casos")
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","contraparte","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","base_cuota","observaciones"])

    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])

    with st.expander("➕ Nuevo Caso"):
        if clientes_df.empty:
            st.warning("Debe registrar clientes primero")
        else:
            seleccion_cliente = st.selectbox("Seleccionar Cliente", clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==seleccion_cliente]["id"].values[0]
            numero_expediente = st.text_input("Número de Expediente")
            anio = st.number_input("Año", min_value=2000, max_value=2100, value=date.today().year)
            materia = st.text_input("Materia")
            contraparte = st.text_input("Contraparte")
            abogado = st.text_input("Abogado a cargo")
            etapa_procesal = st.text_input("Etapa Procesal")
            monto_pactado = st.number_input("Monto Pactado",0.0)
            pretension = st.text_input("Pretensión")
            cuota_litis = st.number_input("Cuota Litis",0.0)
            porcentaje = st.number_input("Porcentaje Cuota Litis",0.0)
            base_cuota = st.number_input("Base para Cálculo de Cuota",0.0)
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar Caso"):
                nuevo_id = str(int(casos_df["id"].max())+1 if not casos_df.empty else 1)
                casos_df = pd.concat([casos_df,pd.DataFrame([[nuevo_id,cliente_id,numero_expediente,anio,materia,contraparte,abogado,etapa_procesal,monto_pactado,pretension,cuota_litis,porcentaje,base_cuota,observaciones]],columns=casos_df.columns)],ignore_index=True)
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró caso {numero_expediente}-{anio}")
                st.success("Caso registrado correctamente")
                st.experimental_rerun()

    if not casos_df.empty:
        st.subheader("Lista de Casos")
        casos_mostrar = casos_df.merge(clientes_df,left_on="cliente_id",right_on="id",suffixes=("","_cliente"))
        st.dataframe(casos_mostrar)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            casos_mostrar.to_excel(writer, index=False, sheet_name='Casos')
            writer.save()
        processed_data = output.getvalue()
        st.download_button(
            label="Exportar Casos a Excel",
            data=processed_data,
            file_name="casos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ===============================
# PAGOS
# ===============================
if menu=="Pagos":
    st.title("💰 Gestión de Pagos")
    pagos_df = cargar_csv(PAGOS_CSV, ["id","caso_id","fecha","tipo","monto","observaciones"])
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","contraparte","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","base_cuota","observaciones"])
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])

    with st.expander("➕ Nuevo Pago"):
        if casos_df.empty:
            st.warning("Debe registrar casos primero")
        else:
            casos_df["descripcion"] = casos_df["numero_expediente"].astype(str) + "-" + casos_df["anio"].astype(str) + " | " + clientes_df.loc[casos_df["cliente_id"].astype(int)-1,"nombre"].values
            seleccion = st.selectbox("Seleccionar Caso", casos_df["descripcion"])
            partes = seleccion.split(" | ")
            expediente,anio = partes[0].split("-")
            caso = casos_df[(casos_df["numero_expediente"]==expediente) & (casos_df["anio"]==int(anio))].iloc[0]
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
            monto = st.number_input("Monto",0.0)
            obs = st.text_area("Observaciones")
            if st.button("Guardar Pago"):
                nuevo_id = str(int(pagos_df["id"].max())+1 if not pagos_df.empty else 1)
                pagos_df = pd.concat([pagos_df,pd.DataFrame([[nuevo_id,caso["id"],str(fecha),tipo,monto,obs]],columns=pagos_df.columns)],ignore_index=True)
                guardar_csv(pagos_df,PAGOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró pago para caso {caso['numero_expediente']}-{caso['anio']}")
                st.success("Pago registrado correctamente")
                st.experimental_rerun()

    if not pagos_df.empty:
        pagos_mostrar = pagos_df.merge(casos_df,left_on="caso_id",right_on="id",suffixes=("","_caso"))
        pagos_mostrar["Cliente"] = pagos_mostrar["cliente_id"].map(lambda x: clientes_df[clientes_df["id"]==x]["nombre"].values[0])
        pagos_mostrar["Expediente"] = pagos_mostrar["numero_expediente"].astype(str) + "-" + pagos_mostrar["anio"].astype(str)
        pagos_mostrar_display = pagos_mostrar[["id","Cliente","Expediente","fecha","tipo","monto","observaciones"]]
        st.dataframe(pagos_mostrar_display)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pagos_mostrar_display.to_excel(writer, index=False, sheet_name='Pagos')
            writer.save()
        processed_data = output.getvalue()
        st.download_button(
            label="Exportar Pagos a Excel",
            data=processed_data,
            file_name="pagos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ===============================
# CONTRATOS
# ===============================
if menu=="Contratos":
    st.title("📄 Contratos Automáticos")
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","contraparte","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","base_cuota","observaciones"])
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    
    if casos_df.empty:
        st.warning("No hay casos registrados")
    else:
        seleccion_cliente = st.selectbox("Seleccionar Cliente", clientes_df["nombre"])
        cliente_id = clientes_df[clientes_df["nombre"]==seleccion_cliente]["id"].values[0]
        casos_cliente = casos_df[casos_df["cliente_id"]==cliente_id]
        seleccion_caso = st.selectbox("Seleccionar Caso", casos_cliente["numero_expediente"].astype(str)+"-"+casos_cliente["anio"].astype(str))
        
        caso = casos_cliente[(casos_cliente["numero_expediente"]==int(seleccion_caso.split("-")[0])) & (casos_cliente["anio"]==int(seleccion_caso.split("-")[1]))].iloc[0]
        cliente = clientes_df[clientes_df["id"]==cliente_id].iloc[0]

        # Plantilla de contrato
        contrato_texto = f"""
CONTRATO DE LOCACIÓN DE SERVICIOS PROFESIONALES N° XXXX - {date.today().year} - CLS

Entre {cliente['nombre']} ({cliente['tipo_persona']}) y el abogado {caso['abogado']}.
Expediente: {caso['numero_expediente']}-{caso['anio']}
Materia: {caso['materia']}
Contraparte: {caso['contraparte']}
Monto Pactado: {caso['monto_pactado']}
Pretensión: {caso['pretension']}
Cuota Litis: {caso['cuota_litis']} ({caso['porcentaje']}% sobre base {caso['base_cuota']})
Observaciones: {caso['observaciones']}
        """
        st.text_area("Contrato Generado", contrato_texto, height=300)
        st.download_button(
            "Descargar Contrato",
            contrato_texto,
            file_name=f"Contrato_{caso['numero_expediente']}-{caso['anio']}.txt"
        )

# ===============================
# HISTORIAL
# ===============================
if menu=="Historial":
    st.title("📝 Historial de Acciones")
    historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    if not historial_df.empty:
        st.dataframe(historial_df)
        export_df_to_excel(historial_df,"historial.xlsx")

# ===============================
# USUARIOS
# ===============================
if menu=="Usuarios" and st.session_state.rol=="admin":
    st.title("👤 Gestión de Usuarios")
    usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])
    with st.expander("➕ Nuevo Usuario"):
        nuevo_usuario = st.text_input("Usuario")
        nueva_contrasena = st.text_input("Contraseña", type="password")
        rol = st.selectbox("Rol", ["admin","abogado"])
        if st.button("Guardar Usuario"):
            usuarios_df = pd.concat([usuarios_df,pd.DataFrame([[nuevo_usuario,nueva_contrasena,rol]],columns=usuarios_df.columns)],ignore_index=True)
            guardar_csv(usuarios_df,USUARIOS_CSV)
            registrar_historial(st.session_state.usuario,f"Registró usuario {nuevo_usuario}")
            st.success("Usuario registrado correctamente")
            st.experimental_rerun()
    if not usuarios_df.empty:
        st.dataframe(usuarios_df)
        export_df_to_excel(usuarios_df,"usuarios.xlsx")
