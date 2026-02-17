# ===============================
# SISTEMA DE GESTIÓN JURÍDICA – BLOQUE 1
# ===============================
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Archivos CSV
CLIENTES_FILE = "clientes.csv"
CASOS_FILE = "casos.csv"
PAGOS_FILE = "pagos.csv"
USUARIOS_FILE = "usuarios.csv"
HISTORIAL_FILE = "historial.csv"

# Crear CSV vacíos si no existen
for file, cols in [
    (CLIENTES_FILE, ["id","nombre","dni","celular","correo","direccion","contacto_emergencia","num_contacto","tipo_persona","observaciones"]),
    (CASOS_FILE, ["id","cliente_id","expediente","anio","materia","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","contraparte","observaciones"]),
    (PAGOS_FILE, ["id","caso_id","fecha","tipo","monto","observaciones"]),
    (USUARIOS_FILE, ["id","usuario","contrasena","rol"]),
    (HISTORIAL_FILE, ["id","usuario","accion","fecha"])
]:
    if not os.path.exists(file):
        pd.DataFrame(columns=cols).to_csv(file,index=False)

# ===============================
# Funciones comunes
# ===============================

def cargar_csv(file):
    return pd.read_csv(file)

def guardar_csv(df, file):
    df.to_csv(file,index=False)

def registrar_historial(usuario,accion):
    df = cargar_csv(HISTORIAL_FILE)
    new_id = df["id"].max()+1 if not df.empty else 1
    df = pd.concat([df, pd.DataFrame([{"id":new_id,"usuario":usuario,"accion":accion,"fecha":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])],ignore_index=True)
    guardar_csv(df,HISTORIAL_FILE)

# ===============================
# Sesión y login
# ===============================
st.set_page_config(page_title="Estudio Jurídico", layout="wide")

if "login" not in st.session_state:
    st.session_state.login = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

# Login
if not st.session_state.login:
    st.title("🔐 Login Sistema Estudio Jurídico")
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña",type="password")
    if st.button("Ingresar"):
        usuarios_df = cargar_csv(USUARIOS_FILE)
        user = usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)]
        if not user.empty:
            st.session_state.login = True
            st.session_state.usuario = usuario_input
            st.session_state.rol = user.iloc[0]["rol"]
            registrar_historial(usuario_input,"Inicio de sesión")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrecta")
    st.stop()

# Menú principal
menu = st.sidebar.selectbox("Menú", ["Clientes","Casos","Pagos","Contratos","Usuarios","Historial","Cerrar sesión"])

if menu == "Cerrar sesión":
    st.session_state.login = False
    st.session_state.usuario = ""
    st.session_state.rol = ""
    st.experimental_rerun()
# ===============================
# BLOQUE 2 – Clientes, Casos y Pagos
# ===============================

# ---------- CLIENTES ----------
if menu == "Clientes":
    st.title("👥 Gestión de Clientes")

    clientes_df = cargar_csv(CLIENTES_FILE)

    with st.expander("➕ Nuevo Cliente"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        contacto_emergencia = st.text_input("Contacto de emergencia")
        num_contacto = st.text_input("Número de contacto")
        tipo_persona = st.selectbox("Tipo de persona",["Natural","Jurídica"])
        observaciones = st.text_area("Observaciones")
        if st.button("Guardar Cliente"):
            new_id = clientes_df["id"].max()+1 if not clientes_df.empty else 1
            clientes_df = pd.concat([clientes_df, pd.DataFrame([{
                "id":new_id,"nombre":nombre,"dni":dni,"celular":celular,
                "correo":correo,"direccion":direccion,"contacto_emergencia":contacto_emergencia,
                "num_contacto":num_contacto,"tipo_persona":tipo_persona,"observaciones":observaciones
            }])],ignore_index=True)
            guardar_csv(clientes_df,CLIENTES_FILE)
            registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
            st.success("Cliente registrado")
            st.experimental_rerun()

    if not clientes_df.empty:
        st.subheader("Lista de Clientes")
        for i,row in clientes_df.iterrows():
            with st.expander(f"{row['nombre']} | DNI: {row['dni']}"):
                st.write(f"Celular: {row['celular']}")
                st.write(f"Correo: {row['correo']}")
                st.write(f"Dirección: {row['direccion']}")
                st.write(f"Contacto emergencia: {row['contacto_emergencia']} ({row['num_contacto']})")
                st.write(f"Tipo: {row['tipo_persona']}")
                st.write(f"Observaciones: {row['observaciones']}")
                # Editar cliente
                if st.button(f"Editar {row['nombre']}",key=f"edit_cliente_{i}"):
                    nombre_n = st.text_input("Nombre completo",value=row["nombre"])
                    dni_n = st.text_input("DNI",value=row["dni"])
                    celular_n = st.text_input("Celular",value=row["celular"])
                    correo_n = st.text_input("Correo",value=row["correo"])
                    direccion_n = st.text_input("Dirección",value=row["direccion"])
                    contacto_emergencia_n = st.text_input("Contacto emergencia",value=row["contacto_emergencia"])
                    num_contacto_n = st.text_input("Número contacto",value=row["num_contacto"])
                    tipo_persona_n = st.selectbox("Tipo de persona",["Natural","Jurídica"],index=0 if row["tipo_persona"]=="Natural" else 1)
                    observaciones_n = st.text_area("Observaciones",value=row["observaciones"])
                    if st.button("Guardar cambios",key=f"save_cliente_{i}"):
                        clientes_df.loc[i] = [row["id"],nombre_n,dni_n,celular_n,correo_n,direccion_n,contacto_emergencia_n,num_contacto_n,tipo_persona_n,observaciones_n]
                        guardar_csv(clientes_df,CLIENTES_FILE)
                        registrar_historial(st.session_state.usuario,f"Editó cliente {nombre_n}")
                        st.success("Cambios guardados")
                        st.experimental_rerun()
                # Eliminar cliente
                if st.button(f"Eliminar {row['nombre']}",key=f"del_cliente_{i}"):
                    clientes_df = clientes_df.drop(i)
                    guardar_csv(clientes_df,CLIENTES_FILE)
                    registrar_historial(st.session_state.usuario,f"Eliminó cliente {row['nombre']}")
                    st.success("Cliente eliminado")
                    st.experimental_rerun()

# ---------- CASOS ----------
if menu == "Casos":
    st.title("📂 Gestión de Casos")
    clientes_df = cargar_csv(CLIENTES_FILE)
    casos_df = cargar_csv(CASOS_FILE)

    if clientes_df.empty:
        st.warning("Registre clientes antes de agregar casos")
    else:
        with st.expander("➕ Nuevo Caso"):
            seleccion = st.selectbox("Seleccionar Cliente", clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==seleccion]["id"].values[0]
            expediente = st.text_input("Número de expediente")
            anio = st.text_input("Año")
            materia = st.text_input("Materia")
            abogado = st.text_input("Abogado a cargo")
            etapa_procesal = st.text_input("Etapa procesal")
            monto_pactado = st.number_input("Monto pactado",0.0)
            pretension = st.text_input("Pretensión")
            cuota_litis = st.number_input("Cuota Litis",0.0)
            porcentaje = st.number_input("Porcentaje",0.0)
            contraparte = st.text_input("Contraparte")
            observaciones = st.text_area("Observaciones")
            if st.button("Guardar Caso"):
                new_id = casos_df["id"].max()+1 if not casos_df.empty else 1
                casos_df = pd.concat([casos_df,pd.DataFrame([{
                    "id":new_id,"cliente_id":cliente_id,"expediente":expediente,"anio":anio,"materia":materia,
                    "abogado":abogado,"etapa_procesal":etapa_procesal,"monto_pactado":monto_pactado,
                    "pretension":pretension,"cuota_litis":cuota_litis,"porcentaje":porcentaje,
                    "contraparte":contraparte,"observaciones":observaciones
                }])],ignore_index=True)
                guardar_csv(casos_df,CASOS_FILE)
                registrar_historial(st.session_state.usuario,f"Registró caso {expediente}-{anio}")
                st.success("Caso registrado")
                st.experimental_rerun()

        if not casos_df.empty:
            st.subheader("Lista de Casos")
            for i,row in casos_df.iterrows():
                cliente_nombre = clientes_df[clientes_df["id"]==row["cliente_id"]]["nombre"].values[0]
                with st.expander(f"{row['expediente']}-{row['anio']} | {cliente_nombre}"):
                    st.write(f"Materia: {row['materia']}")
                    st.write(f"Abogado: {row['abogado']}")
                    st.write(f"Etapa procesal: {row['etapa_procesal']}")
                    st.write(f"Monto pactado: {row['monto_pactado']}")
                    st.write(f"Pretensión: {row['pretension']}")
                    st.write(f"Cuota Litis: {row['cuota_litis']} ({row['porcentaje']}%)")
                    st.write(f"Contraparte: {row['contraparte']}")
                    st.write(f"Observaciones: {row['observaciones']}")
                    if st.button(f"Editar Caso {row['expediente']}-{row['anio']}",key=f"edit_caso_{i}"):
                        # se puede añadir edición similar a clientes
                        st.info("Edición disponible en próxima versión")
                    if st.button(f"Eliminar Caso {row['expediente']}-{row['anio']}",key=f"del_caso_{i}"):
                        casos_df = casos_df.drop(i)
                        guardar_csv(casos_df,CASOS_FILE)
                        registrar_historial(st.session_state.usuario,f"Eliminó caso {row['expediente']}-{row['anio']}")
                        st.success("Caso eliminado")
                        st.experimental_rerun()

# ---------- PAGOS ----------
if menu == "Pagos":
    st.title("💰 Gestión de Pagos")
    clientes_df = cargar_csv(CLIENTES_FILE)
    casos_df = cargar_csv(CASOS_FILE)
    pagos_df = cargar_csv(PAGOS_FILE)

    if casos_df.empty:
        st.warning("No hay casos registrados")
    else:
        with st.expander("➕ Nuevo Pago"):
            casos_df["desc"] = casos_df["expediente"].astype(str) + "-" + casos_df["anio"].astype(str) + " | " + clientes_df.set_index("id").loc[casos_df["cliente_id"],"nombre"].values
            seleccion = st.selectbox("Seleccionar Caso", casos_df["desc"])
            caso_id = casos_df[casos_df["desc"]==seleccion]["id"].values[0]
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
            monto = st.number_input("Monto",0.0)
            obs = st.text_area("Observaciones")
            if st.button("Guardar Pago"):
                new_id = pagos_df["id"].max()+1 if not pagos_df.empty else 1
                pagos_df = pd.concat([pagos_df,pd.DataFrame([{
                    "id":new_id,"caso_id":caso_id,"fecha":fecha,"tipo":tipo,"monto":monto,"observaciones":obs
                }])],ignore_index=True)
                guardar_csv(pagos_df,PAGOS_FILE)
                registrar_historial(st.session_state.usuario,f"Registró pago {monto} para caso {seleccion}")
                st.success("Pago registrado")
                st.experimental_rerun()

        if not pagos_df.empty:
            st.subheader("Lista de Pagos")
            pagos_df = pagos_df.merge(casos_df[["id","expediente","anio","cliente_id"]],left_on="caso_id",right_on="id",suffixes=("","_caso"))
            pagos_df["cliente"] = pagos_df["cliente_id"].map(clientes_df.set_index("id")["nombre"])
            st.dataframe(pagos_df[["id","cliente","expediente","anio","fecha","tipo","monto","observaciones"]])
            id_eliminar = st.number_input("ID Pago a eliminar", step=1)
            if st.button("Eliminar Pago"):
                pagos_df = pagos_df[pagos_df["id"]!=id_eliminar]
                guardar_csv(pagos_df,PAGOS_FILE)
                registrar_historial(st.session_state.usuario,f"Eliminó pago {id_eliminar}")
                st.success("Pago eliminado")
                st.experimental_rerun()
# ===============================
# BLOQUE 3 – Contratos, Usuarios, Roles y Historial
# ===============================

# ---------- CONTRATOS ----------
if menu == "Contratos":
    st.title("📄 Contratos")

    clientes_df = cargar_csv(CLIENTES_FILE)
    contratos_df = cargar_csv(CONTRATOS_FILE)

    # Selección de cliente para generar contrato
    if not clientes_df.empty:
        seleccion = st.selectbox("Seleccionar Cliente", clientes_df["nombre"])
        cliente_id = clientes_df[clientes_df["nombre"]==seleccion]["id"].values[0]
        if st.button("Generar Contrato"):
            cliente = clientes_df[clientes_df["id"]==cliente_id].iloc[0]
            contrato_texto = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS

Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en el Psje. Victoria N° 280 – Barrio San Martín, comprensión del distrito, provincia y región Cajamarca, a quien en adelante se denominará EL LOCADOR; y, de la otra parte, la empresa MANTENIMIENTO E INGENIERÍA INDUSTRIAL SRL, con RUC N° 20529648147, debidamente representada por su gerente administrativo JHONNY MANUEL PEREZ PAREDES identificado con DNI N° 46499746, según obra en la Partida Electrónica N° 11137191 del registro de Personas Jurídicas de Cajamarca, con domicilio en el Av. Intihuatana Nro. 617 Urb. Residencial Higuereta Lima - Lima - Santiago de Surco, a quien en adelante se denominará EL CLIENTE.

Cliente seleccionado: {cliente['nombre']} | DNI: {cliente['dni']}
Contrato generado el: {datetime.datetime.now().strftime('%d/%m/%Y')}

[Se incluyen todas las cláusulas tal como se definieron previamente en tu contrato]
"""
            st.text_area("Contrato",contrato_texto,height=500)

            # Guardar contrato
            if st.button("Guardar Contrato"):
                new_id = contratos_df["id"].max()+1 if not contratos_df.empty else 1
                contratos_df = pd.concat([contratos_df,pd.DataFrame([{
                    "id":new_id,
                    "cliente_id":cliente_id,
                    "texto":contrato_texto,
                    "fecha":datetime.datetime.now().strftime("%Y-%m-%d")
                }])],ignore_index=True)
                guardar_csv(contratos_df,CONTRATOS_FILE)
                registrar_historial(st.session_state.usuario,f"Generó contrato para cliente {cliente['nombre']}")
                st.success("Contrato guardado")
                st.experimental_rerun()

# ---------- USUARIOS Y ROLES ----------
if menu == "Usuarios":
    st.title("👤 Gestión de Usuarios y Roles")
    usuarios_df = cargar_csv(USUARIOS_FILE)

    with st.expander("➕ Nuevo Usuario"):
        nombre = st.text_input("Nombre completo")
        usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña",type="password")
        rol = st.selectbox("Rol",["Admin","Abogado","Asistente"])
        if st.button("Agregar Usuario"):
            new_id = usuarios_df["id"].max()+1 if not usuarios_df.empty else 1
            usuarios_df = pd.concat([usuarios_df,pd.DataFrame([{
                "id":new_id,"nombre":nombre,"usuario":usuario,"contrasena":contrasena,"rol":rol
            }])],ignore_index=True)
            guardar_csv(usuarios_df,USUARIOS_FILE)
            registrar_historial(st.session_state.usuario,f"Registró usuario {usuario}")
            st.success("Usuario agregado")
            st.experimental_rerun()

    if not usuarios_df.empty:
        st.subheader("Lista de Usuarios")
        st.dataframe(usuarios_df[["id","nombre","usuario","rol"]])

# ---------- HISTORIAL ----------
if menu == "Historial":
    st.title("📝 Historial de acciones")
    historial_df = cargar_csv(HISTORIAL_FILE)
    if not historial_df.empty:
        st.dataframe(historial_df[["fecha","usuario","accion"]])
    else:
        st.info("No hay registros de historial aún")
