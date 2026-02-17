import streamlit as st
import pandas as pd
from datetime import date
import os

# ===============================
# RUTAS CSV
# ===============================
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
CONTRATOS_CSV = "contratos.csv"
USUARIOS_CSV = "usuarios.csv"
HISTORIAL_CSV = "historial.csv"

# ===============================
# FUNCIONES GENERALES
# ===============================
def cargar_csv(path, columnas):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=columnas)

def guardar_csv(df,path):
    df.to_csv(path,index=False)

def registrar_historial(usuario,accion):
    historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    historial_df = pd.concat([historial_df,pd.DataFrame([[usuario,accion,str(date.today())]],columns=historial_df.columns)],ignore_index=True)
    guardar_csv(historial_df,HISTORIAL_CSV)

def export_df_to_excel(df,nombre_archivo):
    df.to_excel(nombre_archivo,index=False)

# ===============================
# SESIÓN SEGURA
# ===============================
for key in ["usuario","rol","edit_caso","edit_pago","login_ok"]:
    if key not in st.session_state:
        st.session_state[key] = None if key!="login_ok" else False

# ===============================
# LOGIN
# ===============================
if not st.session_state.login_ok:
    st.title("🔒 Ingreso al Sistema")
    usuarios_df = cargar_csv(USUARIOS_CSV, ["usuario","contrasena","rol"])
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña", type="password")
    login_pressed = st.button("Ingresar")
    
    if login_pressed:
        user = usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)]
        if not user.empty:
            st.session_state.usuario = usuario_input
            st.session_state.rol = user.iloc[0]["rol"]
            st.session_state.login_ok = True
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# ===============================
# MENÚ PRINCIPAL
# ===============================
if st.session_state.login_ok:
    menu_options = ["Clientes","Casos","Pagos","Contratos","Historial"]
    if st.session_state.rol=="admin":
        menu_options.append("Usuarios")
    menu = st.sidebar.selectbox("Menú", menu_options)

    # ===============================
    # CLIENTES
    # ===============================
    if menu=="Clientes":
        st.title("👥 Gestión de Clientes")
        clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
        with st.expander("➕ Nuevo Cliente"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI/RUC")
            tipo_persona = st.selectbox("Tipo de persona",["Natural","Jurídica"])
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            direccion = st.text_input("Dirección")
            contacto_emergencia = st.text_input("Contacto de emergencia")
            numero_contacto = st.text_input("Número de contacto")
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar Cliente"):
                nuevo_id = str(int(clientes_df["id"].max())+1 if not clientes_df.empty else 1)
                clientes_df = pd.concat([clientes_df,pd.DataFrame([[nuevo_id,nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones]],columns=clientes_df.columns)],ignore_index=True)
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
                st.success("Cliente registrado")
                st.experimental_rerun()

        if not clientes_df.empty:
            st.subheader("Lista de Clientes")
            st.dataframe(clientes_df)
            st.download_button("Exportar Clientes a Excel", clientes_df.to_excel(index=False), file_name="clientes.xlsx")

    # ===============================
    # CASOS
    # ===============================
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
                    st.success("Caso registrado")
                    st.experimental_rerun()
# ===============================
# PAGOS
# ===============================
if menu=="Pagos":
    st.title("💰 Gestión de Pagos")
    pagos_df = cargar_csv(PAGOS_CSV, ["id","caso_id","fecha","tipo","monto","observaciones"])
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","pretension","abogado","etapa_procesal","contraparte","monto_pactado","cuota_litis","porcentaje","base_cuota","observaciones"])
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])

    if casos_df.empty:
        st.warning("No hay casos registrados")
    else:
        casos_df["descripcion"] = casos_df.apply(lambda x: f"{clientes_df[clientes_df['id']==x['cliente_id']]['nombre'].values[0]} | Exp: {x['numero_expediente']}-{x['anio']}", axis=1)
        seleccion = st.selectbox("Seleccionar Caso", casos_df["descripcion"])
        caso_id = casos_df[casos_df["descripcion"]==seleccion]["id"].values[0]

        fecha = st.date_input("Fecha", date.today())
        tipo = st.selectbox("Tipo", ["Honorarios","Cuota Litis"])
        monto = st.number_input("Monto",0.0)
        obs = st.text_area("Observaciones")
        if st.button("Guardar Pago"):
            nuevo_id = str(int(pagos_df["id"].max())+1 if not pagos_df.empty else 1)
            pagos_df = pd.concat([pagos_df,pd.DataFrame([[nuevo_id,caso_id,str(fecha),tipo,monto,obs]],columns=pagos_df.columns)],ignore_index=True)
            guardar_csv(pagos_df,PAGOS_CSV)
            registrar_historial(st.session_state.usuario,f"Registró pago de S/ {monto} al caso {seleccion}")
            st.success("Pago registrado")
            st.experimental_rerun()

    # Mostrar pagos
    if not pagos_df.empty:
        pagos_mostrar = pagos_df.merge(casos_df, left_on="caso_id", right_on="id", suffixes=("","_caso"))
        pagos_mostrar["Cliente"] = pagos_mostrar["cliente_id"].map(lambda x: clientes_df[clientes_df["id"]==x]["nombre"].values[0])
        pagos_mostrar["Expediente"] = pagos_mostrar["numero_expediente"].astype(str) + "-" + pagos_mostrar["anio"].astype(str)
        pagos_mostrar_display = pagos_mostrar[["id","Cliente","Expediente","fecha","tipo","monto","observaciones"]]
        st.dataframe(pagos_mostrar_display)
        export_df_to_excel(pagos_mostrar_display,"pagos.xlsx")

        # Editar/Eliminar pagos
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
# CONTRATOS AUTOMÁTICOS
# ===============================
if menu=="Contratos":
    st.title("📝 Generar Contrato")
    casos_df = cargar_csv(CASOS_CSV, ["id","cliente_id","numero_expediente","anio","materia","pretension","abogado","etapa_procesal","contraparte","monto_pactado","cuota_litis","porcentaje","base_cuota","observaciones"])
    clientes_df = cargar_csv(CLIENTES_CSV, ["id","nombre","dni","tipo_persona","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    if casos_df.empty:
        st.warning("No hay casos para generar contrato")
    else:
        seleccion = st.selectbox("Seleccionar Caso para Contrato", casos_df["id"].astype(str))
        caso = casos_df[casos_df["id"]==int(seleccion)].iloc[0]
        cliente = clientes_df[clientes_df["id"]==caso["cliente_id"]].iloc[0]

        # Formato de contrato
        contrato_texto = f"""
CONTRATO DE LOCACIÓN DE SERVICIOS PROFESIONALES N° XXXX - {caso['anio']} - CLS

Entre {cliente['nombre']} ({cliente['tipo_persona']}) y el abogado {caso['abogado']}, se acuerda:

Objeto: {caso['pretension']}
Monto pactado: S/ {caso['monto_pactado']}
Cuota litis: S/ {caso['cuota_litis']} ({caso['porcentaje']}% sobre S/ {caso['base_cuota']})
Expediente: {caso['numero_expediente']}-{caso['anio']}
Contraparte: {caso['contraparte']}
Etapa procesal: {caso['etapa_procesal']}
Observaciones: {caso['observaciones']}
        """
        st.text_area("Contrato Generado", contrato_texto, height=300)
        st.download_button("Descargar Contrato", contrato_texto, file_name=f"contrato_{caso['numero_expediente']}.txt")

# ===============================
# HISTORIAL
# ===============================
if menu=="Historial":
    st.title("📜 Historial de acciones")
    historial_df = cargar_csv(HISTORIAL_CSV, ["usuario","accion","fecha"])
    st.dataframe(historial_df)
    export_df_to_excel(historial_df,"historial.xlsx")

# ===============================
# USUARIOS Y ROLES (solo admin)
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
    export_df_to_excel(usuarios_df,"usuarios.xlsx")
