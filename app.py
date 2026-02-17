import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

# ---------- CSV Paths ----------
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
USUARIOS_CSV = "usuarios.csv"
HISTORIAL_CSV = "historial.csv"

# ---------- Columnas requeridas ----------
CLIENTES_COLUMNS = ["id","nombre","dni","celular","correo","direccion","contacto_emergencia","telefono_emergencia","observaciones"]
CASOS_COLUMNS = ["id","cliente_id","expediente","anio","materia","pretension","monto_pactado","cuota_litis","porcentaje","abogado","etapa_procesal","contraparte","observaciones"]
PAGOS_COLUMNS = ["id","caso_id","fecha","tipo","monto","observaciones"]
USUARIOS_COLUMNS = ["usuario","contrasena","rol"]
HISTORIAL_COLUMNS = ["fecha","usuario","accion"]

# ---------- Funciones para CSV ----------
def cargar_csv(path,columnas):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=columnas)
        df.to_csv(path,index=False)
    return df

def guardar_csv(df,path):
    df.to_csv(path,index=False)

def generar_id(df):
    if df.empty:
        return "1"
    else:
        return str(int(df["id"].max())+1)

# ---------- Cargar CSVs ----------
clientes_df = cargar_csv(CLIENTES_CSV,CLIENTES_COLUMNS)
casos_df = cargar_csv(CASOS_CSV,CASOS_COLUMNS)
pagos_df = cargar_csv(PAGOS_CSV,PAGOS_COLUMNS)
usuarios_df = cargar_csv(USUARIOS_CSV,USUARIOS_COLUMNS)
historial_df = cargar_csv(HISTORIAL_CSV,HISTORIAL_COLUMNS)

# ---------- Sesión ----------
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "rol" not in st.session_state:
    st.session_state["rol"] = ""

# ---------- Función historial ----------
def registrar_historial(usuario,accion):
    global historial_df
    historial_df = historial_df.append({"fecha":datetime.now(),"usuario":usuario,"accion":accion},ignore_index=True)
    guardar_csv(historial_df,HISTORIAL_CSV)

# ---------- Login ----------
st.title("🔒 Sistema de Gestión Jurídica")
if st.session_state.usuario == "":
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña",type="password")
    if st.button("Ingresar"):
        user = usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)]
        if not user.empty:
            st.session_state.usuario = usuario_input
            st.session_state.rol = user.iloc[0]["rol"]
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
else:
    st.success(f"Bienvenido {st.session_state.usuario} ({st.session_state.rol})")
    menu = st.selectbox("Menú", ["Clientes","Casos","Pagos","Contratos","Usuarios","Historial","Cerrar Sesión"])
    
    if menu == "Cerrar Sesión":
        st.session_state.usuario = ""
        st.session_state.rol = ""
        st.experimental_rerun()

# ---------- Gestión de Clientes ----------
    if menu == "Clientes":
        st.header("📋 Gestión de Clientes")
        with st.expander("➕ Nuevo Cliente"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI")
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            direccion = st.text_input("Dirección")
            contacto = st.text_input("Contacto de Emergencia")
            telefono_contacto = st.text_input("Teléfono de Contacto")
            obs = st.text_area("Observaciones")
            if st.button("Guardar Cliente"):
                nuevo_id = generar_id(clientes_df)
                clientes_df = clientes_df.append({
                    "id":nuevo_id,"nombre":nombre,"dni":dni,"celular":celular,"correo":correo,
                    "direccion":direccion,"contacto_emergencia":contacto,"telefono_emergencia":telefono_contacto,
                    "observaciones":obs
                },ignore_index=True)
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
                st.success("Cliente registrado")
                st.experimental_rerun()

        if not clientes_df.empty:
            st.subheader("Lista de Clientes")
            seleccion = st.selectbox("Seleccionar Cliente", clientes_df["nombre"])
            cliente = clientes_df[clientes_df["nombre"]==seleccion].iloc[0]

            st.write(cliente.to_dict())
            
            # Editar Cliente
            st.subheader("✏️ Editar Cliente")
            nombre_edit = st.text_input("Nombre",cliente["nombre"])
            dni_edit = st.text_input("DNI",cliente["dni"])
            celular_edit = st.text_input("Celular",cliente["celular"])
            correo_edit = st.text_input("Correo",cliente["correo"])
            direccion_edit = st.text_input("Dirección",cliente["direccion"])
            contacto_edit = st.text_input("Contacto Emergencia",cliente["contacto_emergencia"])
            telefono_edit = st.text_input("Teléfono Contacto",cliente["telefono_emergencia"])
            obs_edit = st.text_area("Observaciones",cliente["observaciones"])

            if st.button("Guardar Cambios Cliente"):
                clientes_df.loc[clientes_df["id"]==cliente["id"],["nombre","dni","celular","correo","direccion","contacto_emergencia","telefono_emergencia","observaciones"]] = \
                    [nombre_edit,dni_edit,celular_edit,correo_edit,direccion_edit,contacto_edit,telefono_edit,obs_edit]
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Editó cliente {nombre_edit}")
                st.success("Cliente actualizado")
                st.experimental_rerun()
            
            # Eliminar Cliente
            if st.button("Eliminar Cliente"):
                clientes_df = clientes_df[clientes_df["id"]!=cliente["id"]]
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Eliminó cliente {cliente['nombre']}")
                st.success("Cliente eliminado")
                st.experimental_rerun()
# ---------- Gestión de Casos ----------
    if menu == "Casos":
        st.header("⚖️ Gestión de Casos")
        with st.expander("➕ Nuevo Caso"):
            cliente_sel = st.selectbox("Cliente", clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==cliente_sel]["id"].values[0]
            expediente = st.text_input("Número de Expediente")
            anio = st.number_input("Año", value=datetime.now().year, step=1)
            materia = st.text_input("Materia")
            pretension = st.text_input("Pretensión")
            monto_pactado = st.number_input("Monto Pactado",0.0)
            cuota_litis = st.number_input("Cuota Litis",0.0)
            porcentaje = st.number_input("Porcentaje Cuota Litis",0.0)
            abogado = st.text_input("Abogado a cargo",st.session_state.usuario)
            etapa = st.text_input("Etapa Procesal")
            contraparte = st.text_input("Contraparte")
            obs = st.text_area("Observaciones")
            
            if st.button("Guardar Caso"):
                nuevo_id = generar_id(casos_df)
                casos_df = casos_df.append({
                    "id":nuevo_id,"cliente_id":cliente_id,"expediente":expediente,"anio":anio,"materia":materia,
                    "pretension":pretension,"monto_pactado":monto_pactado,"cuota_litis":cuota_litis,
                    "porcentaje":porcentaje,"abogado":abogado,"etapa_procesal":etapa,
                    "contraparte":contraparte,"observaciones":obs
                },ignore_index=True)
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró caso {expediente}-{anio}")
                st.success("Caso registrado")
                st.experimental_rerun()

        if not casos_df.empty:
            st.subheader("Lista de Casos")
            if st.session_state.rol == "abogado":
                df_casos = casos_df[casos_df["abogado"]==st.session_state.usuario]
            else:
                df_casos = casos_df.copy()
            df_casos["desc"] = df_casos.apply(lambda x: f"{clientes_df[clientes_df['id']==x['cliente_id']]['nombre'].values[0]} | Exp: {x['expediente']}-{x['anio']}",axis=1)
            seleccion = st.selectbox("Seleccionar Caso", df_casos["desc"])
            partes = seleccion.split("Exp: ")[1].split("-")
            caso = df_casos[(df_casos["expediente"]==partes[0]) & (df_casos["anio"]==int(partes[1]))].iloc[0]
            st.write(caso.to_dict())

            # Editar Caso
            expediente_edit = st.text_input("Número de Expediente",caso["expediente"])
            anio_edit = st.number_input("Año",caso["anio"], step=1)
            materia_edit = st.text_input("Materia",caso["materia"])
            pretension_edit = st.text_input("Pretensión",caso["pretension"])
            monto_pactado_edit = st.number_input("Monto Pactado",caso["monto_pactado"])
            cuota_litis_edit = st.number_input("Cuota Litis",caso["cuota_litis"])
            porcentaje_edit = st.number_input("Porcentaje Cuota Litis",caso["porcentaje"])
            abogado_edit = st.text_input("Abogado a cargo",caso["abogado"])
            etapa_edit = st.text_input("Etapa Procesal",caso["etapa_procesal"])
            contraparte_edit = st.text_input("Contraparte",caso["contraparte"])
            obs_edit = st.text_area("Observaciones",caso["observaciones"])

            if st.button("Guardar Cambios Caso"):
                idx = casos_df[casos_df["id"]==caso["id"]].index[0]
                casos_df.loc[idx,["expediente","anio","materia","pretension","monto_pactado","cuota_litis","porcentaje",
                                  "abogado","etapa_procesal","contraparte","observaciones"]] = \
                                  [expediente_edit,anio_edit,materia_edit,pretension_edit,monto_pactado_edit,
                                   cuota_litis_edit,porcentaje_edit,abogado_edit,etapa_edit,contraparte_edit,obs_edit]
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Editó caso {expediente_edit}-{anio_edit}")
                st.success("Caso actualizado")
                st.experimental_rerun()

            if st.button("Eliminar Caso"):
                casos_df = casos_df[casos_df["id"]!=caso["id"]]
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Eliminó caso {caso['expediente']}-{caso['anio']}")
                st.success("Caso eliminado")
                st.experimental_rerun()

# ---------- Gestión de Pagos ----------
    if menu == "Pagos":
        st.header("💰 Gestión de Pagos")
        if casos_df.empty:
            st.warning("No hay casos registrados")
        else:
            with st.expander("➕ Nuevo Pago"):
                df = casos_df.copy()
                df["desc"] = df.apply(lambda x: f"{clientes_df[clientes_df['id']==x['cliente_id']]['nombre'].values[0]} | Exp: {x['expediente']}-{x['anio']}",axis=1)
                seleccion = st.selectbox("Seleccionar Caso",df["desc"])
                partes = seleccion.split("Exp: ")[1].split("-")
                caso = df[(df["expediente"]==partes[0]) & (df["anio"]==int(partes[1]))].iloc[0]
                fecha = st.date_input("Fecha")
                tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
                monto = st.number_input("Monto",0.0)
                obs = st.text_area("Observaciones")
                if st.button("Guardar Pago"):
                    nuevo_id = generar_id(pagos_df)
                    pagos_df = pagos_df.append({
                        "id":nuevo_id,"caso_id":caso["id"],"fecha":fecha,"tipo":tipo,"monto":monto,"observaciones":obs
                    },ignore_index=True)
                    guardar_csv(pagos_df,PAGOS_CSV)
                    registrar_historial(st.session_state.usuario,f"Registró pago {monto} a caso {caso['expediente']}-{caso['anio']}")
                    st.success("Pago registrado")
                    st.experimental_rerun()
            
            if not pagos_df.empty:
                st.subheader("Lista de Pagos")
                pagos_display = pagos_df.copy()
                pagos_display["Cliente"] = pagos_display["caso_id"].apply(lambda x: clientes_df[clientes_df["id"]==casos_df[casos_df["id"]==x]["cliente_id"].values[0]]["nombre"].values[0])
                pagos_display["Expediente"] = pagos_display["caso_id"].apply(lambda x: casos_df[casos_df["id"]==x]["expediente"].values[0])
                pagos_display["Año"] = pagos_display["caso_id"].apply(lambda x: casos_df[casos_df["id"]==x]["anio"].values[0])
                st.dataframe(pagos_display[["Cliente","Expediente","Año","fecha","tipo","monto","observaciones"]])
# ---------- Gestión de Contratos ----------
if menu == "Contratos":
    st.header("📄 Contratos de Prestación de Servicios")
    if casos_df.empty:
        st.warning("No hay casos para generar contrato")
    else:
        df = casos_df.copy()
        df["desc"] = df.apply(lambda x: f"{clientes_df[clientes_df['id']==x['cliente_id']]['nombre'].values[0]} | Exp: {x['expediente']}-{x['anio']}",axis=1)
        seleccion = st.selectbox("Seleccionar Caso para Contrato", df["desc"])
        partes = seleccion.split("Exp: ")[1].split("-")
        caso = df[(df["expediente"]==partes[0]) & (df["anio"]==int(partes[1]))].iloc[0]
        cliente = clientes_df[clientes_df["id"]==caso["cliente_id"]].iloc[0]

        st.subheader("Contrato generado:")
        contrato_texto = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS

Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en el Psje. Victoria N° 280 – Barrio San Martín, comprensión del distrito, provincia y región Cajamarca, a quien en adelante se denominará EL LOCADOR; y, de la otra parte, {cliente['nombre']}, identificado con DNI/RUC {cliente['dni']}, a quien en adelante se denominará EL CLIENTE. Para todos sus efectos, el contrato se celebra bajo los siguientes términos y condiciones:

PRIMERO: ANTECEDENTES
1.1. EL LOCADOR es abogado colegiado N° 2710 del Ilustre Colegio de Abogados de Cajamarca.
1.2. EL CLIENTE requiere los servicios de EL LOCADOR conforme al objeto del presente contrato.

SEGUNDO: OBJETO DEL CONTRATO
2.1. EL LOCADOR se obliga a patrocinar al CLIENTE en el expediente judicial N° {caso['expediente']}-{caso['anio']}, con pretensión: {caso['pretension']}, etapa procesal: {caso['etapa_procesal']}, contraparte: {caso['contraparte']}.

TERCERO: CONTRAPRESTACIÓN
3.1. Monto pactado: S/ {caso['monto_pactado']:.2f}
3.2. Cuota Litis: S/ {caso['cuota_litis']:.2f} ({caso['porcentaje']:.2f}%)
3.3. Todos los pagos serán coordinados de común acuerdo y no generarán intereses.

CUARTO: VIGENCIA
El contrato tendrá duración indefinida mientras se mantengan vigentes las prestaciones o hasta rescisión mutua.

QUINTO: PROPIEDAD INTELECTUAL
Toda documentación producida por EL LOCADOR pertenece al CLIENTE, excepto honorarios y regalías.

SEXTO: CLÁUSULA RESOLUTORIA
Podrá resolverse por mutuo acuerdo o incumplimiento de obligaciones.

SÉPTIMO: CLÁUSULA COMPETENCIAL
Renuncia de competencia domiciliaria a favor de la Corte Superior de Justicia de Cajamarca.

OCTAVO: CONFORMIDAD
Las partes firman por duplicado, a la fecha de generación del contrato.

Observaciones: {caso['observaciones']}
"""
        st.text_area("Contrato",contrato_texto,height=400)
        if st.button("Registrar Contrato"):
            contrato_id = generar_id(contratos_df)
            contratos_df = contratos_df.append({
                "id":contrato_id,"caso_id":caso["id"],"texto":contrato_texto,"fecha":str(datetime.now().date())
            },ignore_index=True)
            guardar_csv(contratos_df,CONTRATOS_CSV)
            registrar_historial(st.session_state.usuario,f"Generó contrato para caso {caso['expediente']}-{caso['anio']}")
            st.success("Contrato registrado")

# ---------- Gestión de Usuarios ----------
if menu == "Usuarios" and st.session_state.rol=="admin":
    st.header("👤 Gestión de Usuarios")
    with st.expander("➕ Nuevo Usuario"):
        nuevo_usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña",type="password")
        rol = st.selectbox("Rol",["admin","abogado"])
        if st.button("Guardar Usuario"):
            nuevo_id = generar_id(usuarios_df)
            usuarios_df = usuarios_df.append({
                "id":nuevo_id,"usuario":nuevo_usuario,"contrasena":contrasena,"rol":rol
            },ignore_index=True)
            guardar_csv(usuarios_df,USUARIOS_CSV)
            st.success("Usuario creado")
            registrar_historial(st.session_state.usuario,f"Creó usuario {nuevo_usuario}")
            st.experimental_rerun()
    
    if not usuarios_df.empty:
        st.subheader("Lista de Usuarios")
        st.dataframe(usuarios_df)
        # Editar y eliminar
        sel_usuario = st.selectbox("Seleccionar Usuario",usuarios_df["usuario"])
        usuario = usuarios_df[usuarios_df["usuario"]==sel_usuario].iloc[0]
        nuevo_rol = st.selectbox("Editar Rol",["admin","abogado"],index=0)
        if st.button("Guardar Cambios Usuario"):
            idx = usuarios_df[usuarios_df["id"]==usuario["id"]].index[0]
            usuarios_df.loc[idx,"rol"]=nuevo_rol
            guardar_csv(usuarios_df,USUARIOS_CSV)
            registrar_historial(st.session_state.usuario,f"Cambió rol de {sel_usuario} a {nuevo_rol}")
            st.success("Usuario actualizado")
            st.experimental_rerun()
        if st.button("Eliminar Usuario"):
            usuarios_df = usuarios_df[usuarios_df["id"]!=usuario["id"]]
            guardar_csv(usuarios_df,USUARIOS_CSV)
            registrar_historial(st.session_state.usuario,f"Eliminó usuario {sel_usuario}")
            st.success("Usuario eliminado")
            st.experimental_rerun()

# ---------- Historial ----------
if menu == "Historial":
    st.header("📝 Historial de Actividades")
    if historial_df.empty:
        st.info("No hay actividades registradas")
    else:
        st.dataframe(historial_df.sort_values(by="fecha",ascending=False))
