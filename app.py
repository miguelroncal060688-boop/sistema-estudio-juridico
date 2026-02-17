# ===============================
# SISTEMA DE GESTIÓN JURÍDICA - BLOQUE 1 (CSV)
# ===============================
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os

# ===============================
# RUTAS DE CSV
# ===============================
USUARIOS_CSV = "usuarios.csv"
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
CONTRATOS_CSV = "contratos.csv"
HISTORIAL_CSV = "historial.csv"

# ===============================
# FUNCIONES
# ===============================
def cargar_csv(path, columnas):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=columnas)

def guardar_csv(df, path):
    df.to_csv(path,index=False)

def registrar_historial(usuario, accion):
    df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    df = pd.concat([df, pd.DataFrame([[usuario, accion, date.today()]], columns=df.columns)], ignore_index=True)
    guardar_csv(df,HISTORIAL_CSV)

def export_df_to_excel(df, filename="export.xlsx"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        writer.save()
    st.download_button(label="Descargar Excel", data=output.getvalue(), file_name=filename)

# ===============================
# CARGAR DATOS
# ===============================
usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])
clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
if usuarios_df.empty:
    # Usuario admin por defecto
    usuarios_df = pd.DataFrame([["admin","admin123","admin"]], columns=["usuario","contrasena","rol"])
    guardar_csv(usuarios_df, USUARIOS_CSV)
    st.warning("Se ha creado un usuario ADMIN por defecto: usuario='admin', contraseña='admin123'")

# ===============================
# SESIÓN
# ===============================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None
if "edit_cliente" not in st.session_state:
    st.session_state.edit_cliente = None

# ===============================
# LOGIN
# ===============================
if st.session_state.usuario is None:
    st.sidebar.title("Login")
    usuario_input = st.sidebar.text_input("Usuario")
    contrasena_input = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Ingresar"):
        user = usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)]
        if not user.empty:
            st.session_state.usuario = usuario_input
            st.session_state.rol = user.iloc[0]["rol"]
            st.experimental_rerun()
        else:
            st.sidebar.error("Usuario o contraseña incorrectos")
else:
    st.sidebar.write(f"Usuario: {st.session_state.usuario} ({st.session_state.rol})")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.experimental_rerun()

# ===============================
# MENÚ CLIENTES
# ===============================
if st.session_state.usuario:
    menu = st.sidebar.selectbox("Menú", ["Clientes"])
    if menu=="Clientes":
        st.title("👥 Gestión de Clientes")
        clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
        clientes_df["id"] = clientes_df["id"].astype(str)
        with st.expander("➕ Nuevo Cliente"):
            if st.session_state.edit_cliente:
                c = clientes_df[clientes_df["id"]==st.session_state.edit_cliente].iloc[0]
                nombre = st.text_input("Nombre", c["nombre"])
                dni = st.text_input("DNI", c["dni"])
                tipo_persona = st.selectbox("Tipo de persona", ["Natural","Jurídica"], index=0 if c["tipo_persona"]=="Natural" else 1)
                celular = st.text_input("Celular", c["celular"])
                correo = st.text_input("Correo", c["correo"])
                direccion = st.text_input("Dirección", c["direccion"])
                contacto_emergencia = st.text_input("Contacto emergencia", c["contacto_emergencia"])
                numero_contacto = st.text_input("Número del contacto", c["numero_contacto"])
                observaciones = st.text_area("Observaciones", c["observaciones"])
                if st.button("Guardar Cliente Editado"):
                    idx = clientes_df.index[clientes_df["id"]==st.session_state.edit_cliente][0]
                    clientes_df.loc[idx] = [st.session_state.edit_cliente,nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones]
                    guardar_csv(clientes_df, CLIENTES_CSV)
                    registrar_historial(st.session_state.usuario,f"Editó cliente {nombre}")
                    st.session_state.edit_cliente=None
                    st.experimental_rerun()
            else:
                nombre = st.text_input("Nombre")
                dni = st.text_input("DNI")
                tipo_persona = st.selectbox("Tipo de persona", ["Natural","Jurídica"])
                celular = st.text_input("Celular")
                correo = st.text_input("Correo")
                direccion = st.text_input("Dirección")
                contacto_emergencia = st.text_input("Contacto emergencia")
                numero_contacto = st.text_input("Número del contacto")
                observaciones = st.text_area("Observaciones")
                if st.button("Guardar Cliente"):
                    nuevo_id = str(int(clientes_df["id"].max())+1 if not clientes_df.empty else 1)
                    clientes_df = pd.concat([clientes_df,pd.DataFrame([[nuevo_id,nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones]], columns=clientes_df.columns)], ignore_index=True)
                    guardar_csv(clientes_df, CLIENTES_CSV)
                    registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
                    st.experimental_rerun()

        if not clientes_df.empty:
            st.subheader("Lista de Clientes")
            export_df_to_excel(clientes_df,"clientes.xlsx")
            for i,row in clientes_df.iterrows():
                with st.expander(f"{row['nombre']} - {row['dni']}"):
                    st.write(f"Celular: {row['celular']} / Correo: {row['correo']}")
                    st.write(f"Dirección: {row['direccion']}")
                    st.write(f"Contacto emergencia: {row['contacto_emergencia']} / {row['numero_contacto']}")
                    st.write(f"Observaciones: {row['observaciones']}")
                    col1,col2 = st.columns(2)
                    with col1:
                        if st.button(f"Editar Cliente {row['id']}"):
                            st.session_state.edit_cliente=row['id']
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Eliminar Cliente {row['id']}"):
                            clientes_df = clientes_df[clientes_df["id"]!=row['id']]
                            guardar_csv(clientes_df, CLIENTES_CSV)
                            registrar_historial(st.session_state.usuario,f"Eliminó cliente {row['nombre']}")
                            st.experimental_rerun()
# ===============================
# BLOQUE 2 – Casos, Pagos, Contratos, Historial y Usuarios (CSV)
# ===============================

# ===============================
# CARGAR CSV
# ===============================
casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","pretension","abogado","etapa_procesal","contraparte","monto_pactado","cuota_litis","porcentaje","base_cuota","observaciones"])
pagos_df = cargar_csv(PAGOS_CSV, ["id","caso_id","fecha","tipo","monto","observaciones"])
contratos_df = cargar_csv(CONTRATOS_CSV, ["id","caso_id","numero","fecha","contenido"])
historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])

if "edit_caso" not in st.session_state:
    st.session_state.edit_caso = None

# ===============================
# MENÚ CASOS
# ===============================
menu_options = ["Clientes","Casos","Pagos","Contratos","Historial","Usuarios"]
if st.session_state.rol != "admin":
    menu_options.remove("Usuarios")  # abogados no ven usuarios

menu = st.sidebar.selectbox("Menú", menu_options)

if menu=="Casos":
    st.title("📁 Gestión de Casos")
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","pretension","abogado","etapa_procesal","contraparte","monto_pactado","cuota_litis","porcentaje","base_cuota","observaciones"])

    with st.expander("➕ Nuevo Caso"):
        if st.session_state.edit_caso:
            c = casos_df[casos_df["id"]==st.session_state.edit_caso].iloc[0]
            cliente_selec = clientes_df[clientes_df["id"]==c["cliente_id"]]["nombre"].values[0]
            numero_expediente = st.text_input("Número de expediente", c["numero_expediente"])
            anio = st.number_input("Año", 2000,2100,value=int(c["anio"]))
            materia = st.text_input("Materia", c["materia"])
            pretension = st.text_input("Pretensión", c["pretension"])
            abogado = st.text_input("Abogado a cargo", c["abogado"])
            etapa_procesal = st.text_input("Etapa procesal", c["etapa_procesal"])
            contraparte = st.text_input("Contraparte", c["contraparte"])
            monto_pactado = st.number_input("Monto pactado",float(c["monto_pactado"]))
            cuota_litis = st.number_input("Cuota Litis",float(c["cuota_litis"]))
            porcentaje = st.number_input("Porcentaje",float(c["porcentaje"]))
            base_cuota = st.number_input("Base para cuota litis",float(c["base_cuota"]))
            observaciones = st.text_area("Observaciones", c["observaciones"])
            if st.button("Guardar Caso Editado"):
                idx = casos_df.index[casos_df["id"]==st.session_state.edit_caso][0]
                casos_df.loc[idx] = [st.session_state.edit_caso, c["cliente_id"], numero_expediente, anio, materia, pretension, abogado, etapa_procesal, contraparte, monto_pactado, cuota_litis, porcentaje, base_cuota, observaciones]
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Editó caso {numero_expediente}-{anio}")
                st.session_state.edit_caso = None
                st.experimental_rerun()
        else:
            cliente_selec = st.selectbox("Cliente", clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==cliente_selec]["id"].values[0]
            numero_expediente = st.text_input("Número de expediente")
            anio = st.number_input("Año",2000,2100,value=date.today().year)
            materia = st.text_input("Materia")
            pretension = st.text_input("Pretensión")
            abogado = st.text_input("Abogado a cargo")
            etapa_procesal = st.text_input("Etapa procesal")
            contraparte = st.text_input("Contraparte")
            monto_pactado = st.number_input("Monto pactado",0.0)
            cuota_litis = st.number_input("Cuota Litis",0.0)
            porcentaje = st.number_input("Porcentaje",0.0)
            base_cuota = st.number_input("Base para cuota litis",0.0)
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar Caso"):
                nuevo_id = str(int(casos_df["id"].max())+1 if not casos_df.empty else 1)
                casos_df = pd.concat([casos_df,pd.DataFrame([[nuevo_id,cliente_id,numero_expediente,anio,materia,pretension,abogado,etapa_procesal,contraparte,monto_pactado,cuota_litis,porcentaje,base_cuota,observaciones]],columns=casos_df.columns)],ignore_index=True)
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró caso {numero_expediente}-{anio}")
                st.experimental_rerun()

    if not casos_df.empty:
        st.subheader("Lista de Casos")
        export_df_to_excel(casos_df,"casos.xlsx")
        for i,row in casos_df.iterrows():
            cliente_nombre = clientes_df[clientes_df["id"]==row["cliente_id"]]["nombre"].values[0]
            with st.expander(f"{cliente_nombre} - {row['numero_expediente']}-{row['anio']}"):
                st.write(f"Monto pactado: S/ {row['monto_pactado']}, Cuota Litis: S/ {row['cuota_litis']} ({row['porcentaje']}%)")
                st.write(f"Abogado: {row['abogado']}, Etapa: {row['etapa_procesal']}")
                st.write(f"Contraparte: {row['contraparte']}")
                st.write(f"Pretensión: {row['pretension']}")
                st.write(f"Observaciones: {row['observaciones']}")
                col1,col2,col3 = st.columns(3)
                with col1:
                    if st.button(f"Editar Caso {row['id']}"):
                        st.session_state.edit_caso = row['id']
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Eliminar Caso {row['id']}"):
                        casos_df = casos_df[casos_df["id"]!=row["id"]]
                        pagos_df = pagos_df[pagos_df["caso_id"]!=row["id"]]
                        contratos_df = contratos_df[contratos_df["caso_id"]!=row["id"]]
                        guardar_csv(casos_df,CASOS_CSV)
                        guardar_csv(pagos_df,PAGOS_CSV)
                        guardar_csv(contratos_df,CONTRATOS_CSV)
                        registrar_historial(st.session_state.usuario,f"Eliminó caso {row['numero_expediente']}-{row['anio']}")
                        st.experimental_rerun()
                with col3:
                    if st.button(f"Generar Contrato {row['id']}"):
                        numero_contrato = f"{row['id']}-{row['anio']}-CLS"
                        cliente = clientes_df[clientes_df["id"]==row["cliente_id"]].iloc[0]
                        contenido = f"""
CONTRATO DE LOCACIÓN DE SERVICIOS PROFESIONALES N° {numero_contrato}

Abogado: {row['abogado']}
Cliente: {cliente['nombre']}
Expediente: {row['numero_expediente']}-{row['anio']}
Pretensión: {row['pretension']}
Contraparte: {row['contraparte']}
Monto pactado: S/ {row['monto_pactado']}
Cuota Litis: S/ {row['cuota_litis']} ({row['porcentaje']}% sobre base S/ {row['base_cuota']})
Observaciones: {row['observaciones']}
"""
                        nuevo_id = str(int(contratos_df["id"].max())+1 if not contratos_df.empty else 1)
                        contratos_df = pd.concat([contratos_df,pd.DataFrame([[nuevo_id,row["id"],numero_contrato,str(date.today()),contenido]],columns=contratos_df.columns)],ignore_index=True)
                        guardar_csv(contratos_df,CONTRATOS_CSV)
                        registrar_historial(st.session_state.usuario,f"Generó contrato {numero_contrato}")
                        st.success(f"Contrato generado: N° {numero_contrato}")
# ===============================
# BLOQUE 3 – Pagos, Historial y Usuarios (CSV)
# ===============================

pagos_df = cargar_csv(PAGOS_CSV, ["id","caso_id","fecha","tipo","monto","observaciones"])
historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])

if "edit_pago" not in st.session_state:
    st.session_state.edit_pago = None

if menu=="Pagos":
    st.title("💰 Gestión de Pagos")
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","pretension","abogado","etapa_procesal","contraparte","monto_pactado","cuota_litis","porcentaje","base_cuota","observaciones"])
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])

    if casos_df.empty:
        st.warning("No hay casos registrados")
    else:
        with st.expander("➕ Nuevo Pago"):
            casos_df["descripcion"] = casos_df.apply(lambda x: f"{clientes_df[clientes_df['id']==x['cliente_id']]['nombre'].values[0]} | Exp: {x['numero_expediente']}-{x['anio']}", axis=1)
            seleccion = st.selectbox("Seleccionar Caso", casos_df["descripcion"])
            caso_id = casos_df[casos_df["descripcion"]==seleccion]["id"].values[0]
            fecha = st.date_input("Fecha", date.today())
            tipo = st.selectbox("Tipo", ["Honorarios","Cuota Litis"])
            monto = st.number_input("Monto",0.0)
            obs = st.text_area("Observaciones")
            if st.button("Guardar Pago"):
                nuevo_id = str(int(pagos_df["id"].max())+1 if not pagos_df.empty else 1)
                pagos_df = pd.concat([pagos_df,pd.DataFrame([[nuevo_id,caso_id,str(fecha),tipo,monto,obs]], columns=pagos_df.columns)], ignore_index=True)
                guardar_csv(pagos_df,PAGOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró pago de S/ {monto} al caso {seleccion}")
                st.success("Pago registrado correctamente")
                st.experimental_rerun()

    if not pagos_df.empty:
        st.subheader("Lista de Pagos")
        pagos_mostrar = pagos_df.merge(casos_df, left_on="caso_id", right_on="id", suffixes=("","_caso"))
        pagos_mostrar["Cliente"] = pagos_mostrar["cliente_id"].map(lambda x: clientes_df[clientes_df["id"]==x]["nombre"].values[0])
        pagos_mostrar["Expediente"] = pagos_mostrar["numero_expediente"].astype(str) + "-" + pagos_mostrar["anio"].astype(str)
        pagos_mostrar_display = pagos_mostrar[["id","Cliente","Expediente","fecha","tipo","monto","observaciones"]]
        st.dataframe(pagos_mostrar_display)
        export_df_to_excel(pagos_mostrar_display,"pagos.xlsx")

        for i,row in pagos_mostrar.iterrows():
            with st.expander(f"{row['Cliente']} | {row['numero_expediente']}-{row['anio']} | Pago: S/ {row['monto']}"):
                st.write(f"Fecha: {row['fecha']}, Tipo: {row['tipo']}")
                st.write(f"Observaciones: {row['observaciones']}")
                col1,col2 = st.columns(2)
                with col1:
                    if st.button(f"Editar Pago {row['id']}"):
                        st.session_state.edit_pago = row['id']
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Eliminar Pago {row['id']}"):
                        pagos_df = pagos_df[pagos_df["id"]!=row['id']]
                        guardar_csv(pagos_df,PAGOS_CSV)
                        registrar_historial(st.session_state.usuario,f"Eliminó pago {row['id']} al caso {row['Expediente']}")
                        st.experimental_rerun()

# ===============================
# HISTORIAL
# ===============================
if menu=="Historial":
    st.title("📜 Historial de acciones")
    historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    st.dataframe(historial_df)
    export_df_to_excel(historial_df,"historial.xlsx")

# ===============================
# USUARIOS Y ROLES
# ===============================
if menu=="Usuarios" and st.session_state.rol=="admin":
    st.title("👤 Gestión de Usuarios")
    usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])
    with st.expander("➕ Nuevo Usuario"):
        usuario_nuevo = st.text_input("Usuario")
        contrasena_nueva = st.text_input("Contraseña", type="password")
        rol_nuevo = st.selectbox("Rol", ["admin","abogado"])
        if st.button("Guardar Usuario"):
            if usuario_nuevo and contrasena_nueva:
                usuarios_df = pd.concat([usuarios_df,pd.DataFrame([[usuario_nuevo,contrasena_nueva,rol_nuevo]],columns=usuarios_df.columns)],ignore_index=True)
                guardar_csv(usuarios_df,USUARIOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró usuario {usuario_nuevo}")
                st.success(f"Usuario {usuario_nuevo} creado")
                st.experimental_rerun()
    st.subheader("Usuarios existentes")
    st.dataframe(usuarios_df)
