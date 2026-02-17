# ===============================
# SISTEMA DE GESTIÓN DE ESTUDIO JURÍDICO - BLOQUE 1
# ===============================
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from docx import Document

# -------------------------------
# Archivos CSV
# -------------------------------
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
USUARIOS_CSV = "usuarios.csv"

# -------------------------------
# Funciones de inicialización
# -------------------------------
def inicializar_csv():
    if not os.path.exists(CLIENTES_CSV):
        pd.DataFrame(columns=["id","nombre","dni","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"]).to_csv(CLIENTES_CSV,index=False)
    if not os.path.exists(CASOS_CSV):
        pd.DataFrame(columns=["id","cliente_id","expediente","anio","materia","abogado","etapa_procesal","contraparte","monto_pactado","pretension","cuota_litis","porcentaje","base_cuota","observaciones"]).to_csv(CASOS_CSV,index=False)
    if not os.path.exists(PAGOS_CSV):
        pd.DataFrame(columns=["id","caso_id","fecha","tipo","monto","observaciones"]).to_csv(PAGOS_CSV,index=False)
    if not os.path.exists(USUARIOS_CSV):
        pd.DataFrame([{"usuario":"admin","contrasena":"admin","rol":"admin"}]).to_csv(USUARIOS_CSV,index=False)

# -------------------------------
# Función para cargar CSV
# -------------------------------
def cargar_csv(archivo):
    if os.path.exists(archivo):
        return pd.read_csv(archivo)
    else:
        return pd.DataFrame()

# -------------------------------
# Función para guardar CSV
# -------------------------------
def guardar_csv(df, archivo):
    df.to_csv(archivo,index=False)

# -------------------------------
# Función para generar ID único
# -------------------------------
def generar_id(df):
    return int(df["id"].max()+1) if not df.empty else 1

# -------------------------------
# Inicializar archivos
# -------------------------------
inicializar_csv()

# -------------------------------
# LOGIN
# -------------------------------
st.title("Sistema Estudio Jurídico")
st.subheader("Iniciar Sesión")

usuario_input = st.text_input("Usuario")
contrasena_input = st.text_input("Contraseña",type="password")

usuarios_df = cargar_csv(USUARIOS_CSV)

if st.button("Ingresar"):
    user = usuarios_df[(usuarios_df["usuario"]==usuario_input) & (usuarios_df["contrasena"]==contrasena_input)]
    if not user.empty:
        st.session_state["usuario"] = usuario_input
        st.session_state["rol"] = user.iloc[0]["rol"]
        st.success(f"Bienvenido {usuario_input}")
    else:
        st.error("Usuario o contraseña incorrectos")

if "usuario" in st.session_state:

    # -------------------------------
    # MENÚ PRINCIPAL
    # -------------------------------
    menu = st.sidebar.selectbox("Menú", ["Clientes","Casos","Pagos","Generar Contrato","Cerrar Sesión"])
    
    if menu=="Cerrar Sesión":
        st.session_state.clear()
        st.experimental_rerun()
    
    # ===============================
    # CLIENTES
    # ===============================
    if menu=="Clientes":
        st.title("Gestión de Clientes")
        clientes_df = cargar_csv(CLIENTES_CSV)

        with st.expander("➕ Nuevo Cliente"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI")
            celular = st.text_input("Celular")
            correo = st.text_input("Correo Electrónico")
            direccion = st.text_input("Dirección")
            contacto_emergencia = st.text_input("Contacto de Emergencia")
            numero_contacto = st.text_input("Número de Contacto")
            obs = st.text_area("Observaciones")
            
            if st.button("Guardar Cliente"):
                nuevo = {
                    "id": generar_id(clientes_df),
                    "nombre": nombre,
                    "dni": dni,
                    "celular": celular,
                    "correo": correo,
                    "direccion": direccion,
                    "contacto_emergencia": contacto_emergencia,
                    "numero_contacto": numero_contacto,
                    "observaciones": obs
                }
                clientes_df = pd.concat([clientes_df,pd.DataFrame([nuevo])],ignore_index=True)
                guardar_csv(clientes_df,CLIENTES_CSV)
                st.success("Cliente registrado correctamente")
                st.experimental_rerun()

        st.subheader("Lista de Clientes")
        st.dataframe(clientes_df)

        # Editar/Eliminar
        with st.expander("✏️ Editar/Eliminar Cliente"):
            if not clientes_df.empty:
                seleccion = st.selectbox("Seleccionar Cliente", clientes_df["nombre"])
                cliente = clientes_df[clientes_df["nombre"]==seleccion].iloc[0]
                nombre_edit = st.text_input("Nombre",cliente["nombre"])
                dni_edit = st.text_input("DNI",cliente["dni"])
                celular_edit = st.text_input("Celular",cliente["celular"])
                correo_edit = st.text_input("Correo",cliente["correo"])
                direccion_edit = st.text_input("Dirección",cliente["direccion"])
                contacto_edit = st.text_input("Contacto Emergencia",cliente["contacto_emergencia"])
                numero_contacto_edit = st.text_input("Número Contacto",cliente["numero_contacto"])
                obs_edit = st.text_area("Observaciones",cliente["observaciones"])
                
                if st.button("Actualizar Cliente"):
                    idx = cliente.name
                    clientes_df.loc[idx,"nombre"] = nombre_edit
                    clientes_df.loc[idx,"dni"] = dni_edit
                    clientes_df.loc[idx,"celular"] = celular_edit
                    clientes_df.loc[idx,"correo"] = correo_edit
                    clientes_df.loc[idx,"direccion"] = direccion_edit
                    clientes_df.loc[idx,"contacto_emergencia"] = contacto_edit
                    clientes_df.loc[idx,"numero_contacto"] = numero_contacto_edit
                    clientes_df.loc[idx,"observaciones"] = obs_edit
                    guardar_csv(clientes_df,CLIENTES_CSV)
                    st.success("Cliente actualizado")
                    st.experimental_rerun()
                
                if st.button("Eliminar Cliente"):
                    clientes_df = clientes_df[clientes_df["id"]!=cliente["id"]]
                    guardar_csv(clientes_df,CLIENTES_CSV)
                    st.success("Cliente eliminado")
                    st.experimental_rerun()

    # ===============================
    # CASOS
    # ===============================
    if menu=="Casos":
        st.title("Gestión de Casos")
        casos_df = cargar_csv(CASOS_CSV)
        clientes_df = cargar_csv(CLIENTES_CSV)
        
        with st.expander("➕ Nuevo Caso"):
            if clientes_df.empty:
                st.warning("No hay clientes registrados")
            else:
                clientes_df["desc"] = clientes_df["nombre"] + " | DNI: " + clientes_df["dni"]
                seleccion_cliente = st.selectbox("Seleccionar Cliente", clientes_df["desc"])
                cliente_id = clientes_df[clientes_df["desc"]==seleccion_cliente]["id"].values[0]
                
                expediente = st.text_input("Número de Expediente")
                anio = st.number_input("Año",min_value=2000,max_value=2100,value=datetime.now().year)
                materia = st.text_input("Materia")
                abogado = st.text_input("Abogado a cargo")
                etapa_procesal = st.text_input("Etapa Procesal")
                contraparte = st.text_input("Contraparte")
                monto_pactado = st.number_input("Monto Pactado",0.0)
                pretension = st.text_input("Pretensión")
                cuota_litis = st.number_input("Cuota Litis",0.0)
                porcentaje = st.number_input("Porcentaje (%)",0.0)
                base_cuota = st.number_input("Base para Cálculo Cuota Litis",0.0)
                obs = st.text_area("Observaciones")
                
                if st.button("Guardar Caso"):
                    nuevo = {
                        "id": generar_id(casos_df),
                        "cliente_id": cliente_id,
                        "expediente": expediente,
                        "anio": anio,
                        "materia": materia,
                        "abogado": abogado,
                        "etapa_procesal": etapa_procesal,
                        "contraparte": contraparte,
                        "monto_pactado": monto_pactado,
                        "pretension": pretension,
                        "cuota_litis": cuota_litis,
                        "porcentaje": porcentaje,
                        "base_cuota": base_cuota,
                        "observaciones": obs
                    }
                    casos_df = pd.concat([casos_df,pd.DataFrame([nuevo])],ignore_index=True)
                    guardar_csv(casos_df,CASOS_CSV)
                    st.success("Caso registrado correctamente")
                    st.experimental_rerun()

        st.subheader("Lista de Casos")
        st.dataframe(casos_df)
# ===============================
# BLOQUE 2 - Pagos y Contrato
# ===============================

    # ===============================
    # PAGOS
    # ===============================
    if menu=="Pagos":
        st.title("💰 Gestión de Pagos")
        pagos_df = cargar_csv(PAGOS_CSV)
        casos_df = cargar_csv(CASOS_CSV)
        clientes_df = cargar_csv(CLIENTES_CSV)

        if casos_df.empty:
            st.warning("No hay casos registrados")
        else:
            with st.expander("➕ Nuevo Pago"):
                casos_df["desc"] = (
                    clientes_df.set_index("id").loc[casos_df["cliente_id"],"nombre"].values
                    + " | Exp: " + casos_df["expediente"].astype(str)
                    + "-" + casos_df["anio"].astype(str)
                )
                seleccion = st.selectbox("Seleccionar Caso", casos_df["desc"])
                caso_id = casos_df[casos_df["desc"]==seleccion]["id"].values[0]

                fecha = st.date_input("Fecha")
                tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
                monto = st.number_input("Monto",0.0)
                obs = st.text_area("Observaciones")

                if st.button("Guardar Pago"):
                    nuevo = {
                        "id": generar_id(pagos_df),
                        "caso_id": caso_id,
                        "fecha": str(fecha),
                        "tipo": tipo,
                        "monto": monto,
                        "observaciones": obs
                    }
                    pagos_df = pd.concat([pagos_df,pd.DataFrame([nuevo])],ignore_index=True)
                    guardar_csv(pagos_df,PAGOS_CSV)
                    st.success("Pago registrado correctamente")
                    st.experimental_rerun()

        # Mostrar pagos por expediente y año
        st.subheader("Pagos Registrados")
        if not pagos_df.empty:
            pagos_display = pagos_df.copy()
            pagos_display["Cliente"] = pagos_display["caso_id"].apply(lambda x: clientes_df.set_index("id").loc[casos_df.set_index("id").loc[x,"cliente_id"],"nombre"])
            pagos_display["Expediente"] = pagos_display["caso_id"].apply(lambda x: casos_df.set_index("id").loc[x,"expediente"])
            pagos_display["Año"] = pagos_display["caso_id"].apply(lambda x: casos_df.set_index("id").loc[x,"anio"])
            pagos_display = pagos_display[["id","Cliente","Expediente","Año","fecha","tipo","monto","observaciones"]]
            st.dataframe(pagos_display)

            # Editar / Eliminar pagos
            with st.expander("✏️ Editar/Eliminar Pago"):
                seleccion_pago = st.selectbox("Seleccionar ID de Pago", pagos_display["id"])
                pago = pagos_df[pagos_df["id"]==seleccion_pago].iloc[0]
                fecha_edit = st.date_input("Fecha",pd.to_datetime(pago["fecha"]))
                tipo_edit = st.selectbox("Tipo",["Honorarios","Cuota Litis"],index=0 if pago["tipo"]=="Honorarios" else 1)
                monto_edit = st.number_input("Monto",pago["monto"])
                obs_edit = st.text_area("Observaciones",pago["observaciones"])

                if st.button("Actualizar Pago"):
                    idx = pago.name
                    pagos_df.loc[idx,"fecha"] = str(fecha_edit)
                    pagos_df.loc[idx,"tipo"] = tipo_edit
                    pagos_df.loc[idx,"monto"] = monto_edit
                    pagos_df.loc[idx,"observaciones"] = obs_edit
                    guardar_csv(pagos_df,PAGOS_CSV)
                    st.success("Pago actualizado")
                    st.experimental_rerun()

                if st.button("Eliminar Pago"):
                    pagos_df = pagos_df[pagos_df["id"]!=pago["id"]]
                    guardar_csv(pagos_df,PAGOS_CSV)
                    st.success("Pago eliminado")
                    st.experimental_rerun()

    # ===============================
    # GENERAR CONTRATO
    # ===============================
    if menu=="Generar Contrato":
        st.title("📄 Generar Contrato de Prestación de Servicios")
        clientes_df = cargar_csv(CLIENTES_CSV)
        casos_df = cargar_csv(CASOS_CSV)

        if clientes_df.empty or casos_df.empty:
            st.warning("Necesitas clientes y casos registrados para generar un contrato")
        else:
            clientes_df["desc"] = clientes_df["nombre"] + " | DNI: " + clientes_df["dni"]
            seleccion_cliente = st.selectbox("Seleccionar Cliente", clientes_df["desc"])
            cliente_id = clientes_df[clientes_df["desc"]==seleccion_cliente]["id"].values[0]
            
            casos_cliente = casos_df[casos_df["cliente_id"]==cliente_id]
            if casos_cliente.empty:
                st.warning("El cliente no tiene casos registrados")
            else:
                seleccion_casos = st.multiselect("Seleccionar Casos para el Contrato", casos_cliente["expediente"] + "-" + casos_cliente["anio"].astype(str))
                
                if st.button("Generar Contrato"):
                    doc = Document()
                    doc.add_heading('CONTRATO DE PRESTACIÓN DE SERVICIOS',0)
                    doc.add_paragraph(
                        f"Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en el Psje. Victoria N° 280 – Barrio San Martín, comprensión del distrito, provincia y región Cajamarca, a quien en adelante se denominará EL LOCADOR; y, de la otra parte, el cliente {seleccion_cliente}, a quien en adelante se denominará EL CLIENTE. Para todos sus efectos, el contrato se celebra bajo los siguientes términos y condiciones:"
                    )
                    doc.add_heading("PRIMERO: ANTECEDENTES",level=1)
                    doc.add_paragraph(
                        "1.1. EL LOCADOR es una persona natural que ejerce la profesión de abogado, registrado con colegiatura número 2710.\n"
                        "1.2. EL CLIENTE requiere contratar los servicios de EL LOCADOR conforme al objeto del presente contrato."
                    )
                    doc.add_heading("SEGUNDO: OBJETO DEL CONTRATO",level=1)
                    for c in seleccion_casos:
                        expediente, anio = c.split("-")
                        caso = casos_cliente[(casos_cliente["expediente"]==expediente)&(casos_cliente["anio"].astype(str)==anio)].iloc[0]
                        doc.add_paragraph(f"{c}: {caso['pretension']} (Monto pactado: S/ {caso['monto_pactado']})")
                    doc.add_heading("TERCERO: CONTRAPRESTACIÓN PACTADA POR EL SERVICIO",level=1)
                    for c in seleccion_casos:
                        expediente, anio = c.split("-")
                        caso = casos_cliente[(casos_cliente["expediente"]==expediente)&(casos_cliente["anio"].astype(str)==anio)].iloc[0]
                        doc.add_paragraph(f"{c}: Monto S/ {caso['monto_pactado']} (Cuota Litis: {caso['cuota_litis']} / {caso['porcentaje']}%)")
                    doc.add_heading("CUARTO: VIGENCIA DEL CONTRATO",level=1)
                    doc.add_paragraph("Duración: indefinida hasta rescisión escrita por ambas partes.")
                    doc.add_heading("OCTAVO: CLÁUSULA DE CONFORMIDAD",level=1)
                    doc.add_paragraph("Firmado de común acuerdo por ambas partes.")
                    
                    file_name = f"Contrato_{cliente_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
                    doc.save(file_name)
                    st.success(f"Contrato generado: {file_name}")
                    with open(file_name,"rb") as f:
                        st.download_button("Descargar Contrato",f.data,file_name=file_name)
