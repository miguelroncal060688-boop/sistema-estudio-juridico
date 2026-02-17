import streamlit as st
import pandas as pd
import os
from datetime import date
import io
from docx import Document

st.set_page_config(page_title="Estudio Jurídico", layout="wide")

# ===============================
# ARCHIVOS CSV
# ===============================
CLIENTES_CSV = "clientes.csv"
CASOS_CSV = "casos.csv"
PAGOS_CSV = "pagos.csv"
HISTORIAL_CSV = "historial.csv"
USUARIOS_CSV = "usuarios.csv"

# ===============================
# FUNCIONES GENERALES
# ===============================
def cargar_csv(file, columnas):
    if os.path.exists(file):
        df = pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=columnas)
        df.to_csv(file,index=False)
    return df

def guardar_csv(df,file):
    df.to_csv(file,index=False)

def registrar_historial(usuario,accion):
    historial = cargar_csv(HISTORIAL_CSV,["usuario","accion","fecha"])
    historial = pd.concat([historial,pd.DataFrame([[usuario,accion,str(date.today())]],columns=historial.columns)],ignore_index=True)
    guardar_csv(historial,HISTORIAL_CSV)

# ===============================
# LOGIN SIMPLE
# ===============================
usuarios_df = cargar_csv(USUARIOS_CSV,["usuario","contrasena","rol"])
if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:
    st.title("🔒 Login")
    usuario_input = st.text_input("Usuario")
    contrasena_input = st.text_input("Contraseña",type="password")
    if st.button("Ingresar"):
        user = usuarios_df[(usuarios_df["usuario"]==usuario_input)&(usuarios_df["contrasena"]==contrasena_input)]
        if not user.empty:
            st.session_state.login=True
            st.session_state.usuario=usuario_input
            st.session_state.rol=user.iloc[0]["rol"]
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
else:
    st.sidebar.write(f"Bienvenido, {st.session_state.usuario} ({st.session_state.rol})")
    menu = st.sidebar.selectbox("Menú",["Clientes","Casos","Pagos","Historial","Cerrar Sesión"])
    
    if menu=="Cerrar Sesión":
        st.session_state.login=False
        st.experimental_rerun()

# ===============================
# CLIENTES
# ===============================
if st.session_state.login and menu=="Clientes":
    st.title("👤 Gestión de Clientes")
    clientes_df = cargar_csv(CLIENTES_CSV,["id","nombre","dni","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    
    with st.expander("➕ Nuevo Cliente"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI/RUC")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo electrónico")
        direccion = st.text_input("Dirección")
        contacto = st.text_input("Contacto de emergencia")
        numero_contacto = st.text_input("Número de contacto")
        obs = st.text_area("Observaciones")
        
        if st.button("Guardar Cliente"):
            nuevo_id = str(int(clientes_df["id"].max())+1 if not clientes_df.empty else 1)
            clientes_df = pd.concat([clientes_df,pd.DataFrame([[nuevo_id,nombre,dni,celular,correo,direccion,contacto,numero_contacto,obs]],columns=clientes_df.columns)],ignore_index=True)
            guardar_csv(clientes_df,CLIENTES_CSV)
            registrar_historial(st.session_state.usuario,f"Registró cliente {nombre}")
            st.success("Cliente registrado correctamente")
            st.experimental_rerun()
    
    st.subheader("Lista de Clientes")
    st.dataframe(clientes_df)
    
    # Editar / Eliminar
    if not clientes_df.empty:
        editar_id = st.number_input("ID Cliente a Editar", step=1)
        if st.button("Editar Cliente"):
            if int(editar_id) in clientes_df["id"].values:
                idx = clientes_df[clientes_df["id"]==int(editar_id)].index[0]
                clientes_df.at[idx,"nombre"]=st.text_input("Nombre",clientes_df.at[idx,"nombre"])
                clientes_df.at[idx,"dni"]=st.text_input("DNI/RUC",clientes_df.at[idx,"dni"])
                clientes_df.at[idx,"celular"]=st.text_input("Celular",clientes_df.at[idx,"celular"])
                clientes_df.at[idx,"correo"]=st.text_input("Correo",clientes_df.at[idx,"correo"])
                clientes_df.at[idx,"direccion"]=st.text_input("Dirección",clientes_df.at[idx,"direccion"])
                clientes_df.at[idx,"contacto_emergencia"]=st.text_input("Contacto de Emergencia",clientes_df.at[idx,"contacto_emergencia"])
                clientes_df.at[idx,"numero_contacto"]=st.text_input("Número de Contacto",clientes_df.at[idx,"numero_contacto"])
                clientes_df.at[idx,"observaciones"]=st.text_area("Observaciones",clientes_df.at[idx,"observaciones"])
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Editó cliente {clientes_df.at[idx,'nombre']}")
                st.success("Cliente editado correctamente")
                st.experimental_rerun()
        
        eliminar_id = st.number_input("ID Cliente a Eliminar", step=1,key="elim_cli")
        if st.button("Eliminar Cliente"):
            if int(eliminar_id) in clientes_df["id"].values:
                nombre_elim = clientes_df.loc[clientes_df["id"]==int(eliminar_id),"nombre"].values[0]
                clientes_df = clientes_df[clientes_df["id"]!=int(eliminar_id)]
                guardar_csv(clientes_df,CLIENTES_CSV)
                registrar_historial(st.session_state.usuario,f"Eliminó cliente {nombre_elim}")
                st.success("Cliente eliminado")
                st.experimental_rerun()
# ===============================
# CASOS
# ===============================
if st.session_state.login and menu=="Casos":
    st.title("📁 Gestión de Casos")
    
    clientes_df = cargar_csv(CLIENTES_CSV,["id","nombre","dni","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    casos_df = cargar_csv(CASOS_CSV,["id","cliente_id","contraparte","materia","expediente","anio","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","observaciones"])
    
    with st.expander("➕ Nuevo Caso"):
        if clientes_df.empty:
            st.warning("Debe registrar clientes antes de crear un caso")
        else:
            clientes_df["descripcion"] = clientes_df["nombre"] + " | DNI: " + clientes_df["dni"]
            seleccion = st.selectbox("Seleccionar Cliente",clientes_df["descripcion"])
            cliente_id = clientes_df[clientes_df["descripcion"]==seleccion]["id"].values[0]
            
            contraparte = st.text_input("Contraparte")
            materia = st.text_input("Materia")
            expediente = st.text_input("Número de expediente")
            anio = st.number_input("Año", min_value=2000, max_value=2100, value=date.today().year)
            abogado = st.text_input("Abogado a cargo")
            etapa = st.text_input("Etapa procesal")
            monto_pactado = st.number_input("Monto pactado",0.0)
            pretension = st.text_input("Pretensión")
            cuota_litis = st.number_input("Cuota Litis",0.0)
            porcentaje = st.number_input("Porcentaje (%)",0.0)
            obs = st.text_area("Observaciones")
            
            if st.button("Guardar Caso"):
                nuevo_id = str(int(casos_df["id"].max())+1 if not casos_df.empty else 1)
                casos_df = pd.concat([casos_df,pd.DataFrame([[nuevo_id,cliente_id,contraparte,materia,expediente,anio,abogado,etapa,monto_pactado,pretension,cuota_litis,porcentaje,obs]],columns=casos_df.columns)],ignore_index=True)
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró caso {expediente}-{anio}")
                st.success("Caso registrado correctamente")
                st.experimental_rerun()
    
    st.subheader("Lista de Casos")
    if not casos_df.empty:
        casos_mostrar = casos_df.merge(clientes_df,left_on="cliente_id",right_on="id",suffixes=("_caso","_cliente"))
        casos_mostrar = casos_mostrar[["id_caso","nombre","contraparte","materia","expediente","anio","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","observaciones"]] if "id_caso" in casos_mostrar.columns else casos_mostrar
        st.dataframe(casos_mostrar)

        # Editar / Eliminar
        editar_id = st.number_input("ID Caso a Editar", step=1,key="editar_caso")
        if st.button("Editar Caso"):
            if int(editar_id) in casos_df["id"].values:
                idx = casos_df[casos_df["id"]==int(editar_id)].index[0]
                casos_df.at[idx,"contraparte"]=st.text_input("Contraparte",casos_df.at[idx,"contraparte"])
                casos_df.at[idx,"materia"]=st.text_input("Materia",casos_df.at[idx,"materia"])
                casos_df.at[idx,"expediente"]=st.text_input("Número de expediente",casos_df.at[idx,"expediente"])
                casos_df.at[idx,"anio"]=st.number_input("Año",min_value=2000,max_value=2100,value=int(casos_df.at[idx,"anio"]))
                casos_df.at[idx,"abogado"]=st.text_input("Abogado a cargo",casos_df.at[idx,"abogado"])
                casos_df.at[idx,"etapa_procesal"]=st.text_input("Etapa procesal",casos_df.at[idx,"etapa_procesal"])
                casos_df.at[idx,"monto_pactado"]=st.number_input("Monto pactado",float(casos_df.at[idx,"monto_pactado"]))
                casos_df.at[idx,"pretension"]=st.text_input("Pretensión",casos_df.at[idx,"pretension"])
                casos_df.at[idx,"cuota_litis"]=st.number_input("Cuota Litis",float(casos_df.at[idx,"cuota_litis"]))
                casos_df.at[idx,"porcentaje"]=st.number_input("Porcentaje (%)",float(casos_df.at[idx,"porcentaje"]))
                casos_df.at[idx,"observaciones"]=st.text_area("Observaciones",casos_df.at[idx,"observaciones"])
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Editó caso {casos_df.at[idx,'expediente']}-{casos_df.at[idx,'anio']}")
                st.success("Caso editado correctamente")
                st.experimental_rerun()

        eliminar_id = st.number_input("ID Caso a Eliminar", step=1,key="elim_caso")
        if st.button("Eliminar Caso"):
            if int(eliminar_id) in casos_df["id"].values:
                exp_elim = casos_df.loc[casos_df["id"]==int(eliminar_id),"expediente"].values[0]
                casos_df = casos_df[casos_df["id"]!=int(eliminar_id)]
                guardar_csv(casos_df,CASOS_CSV)
                registrar_historial(st.session_state.usuario,f"Eliminó caso {exp_elim}")
                st.success("Caso eliminado")
                st.experimental_rerun()

# ===============================
# PAGOS
# ===============================
if st.session_state.login and menu=="Pagos":
    st.title("💰 Gestión de Pagos")
    
    clientes_df = cargar_csv(CLIENTES_CSV,["id","nombre","dni","celular","correo","direccion","contacto_emergencia","numero_contacto","observaciones"])
    casos_df = cargar_csv(CASOS_CSV,["id","cliente_id","contraparte","materia","expediente","anio","abogado","etapa_procesal","monto_pactado","pretension","cuota_litis","porcentaje","observaciones"])
    pagos_df = cargar_csv(PAGOS_CSV,["id","caso_id","fecha","tipo","monto","observaciones"])
    
    if casos_df.empty:
        st.warning("No hay casos registrados")
    else:
        with st.expander("➕ Nuevo Pago"):
            casos_df["descripcion"] = casos_df["expediente"].astype(str) + "-" + casos_df["anio"].astype(str) + " | " + casos_df["abogado"]
            seleccion = st.selectbox("Seleccionar Caso",casos_df["descripcion"])
            caso_id = casos_df[casos_df["descripcion"]==seleccion]["id"].values[0]
            
            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
            monto = st.number_input("Monto",0.0)
            obs = st.text_area("Observaciones")
            
            if st.button("Guardar Pago"):
                nuevo_id = str(int(pagos_df["id"].max())+1 if not pagos_df.empty else 1)
                pagos_df = pd.concat([pagos_df,pd.DataFrame([[nuevo_id,caso_id,str(fecha),tipo,monto,obs]],columns=pagos_df.columns)],ignore_index=True)
                guardar_csv(pagos_df,PAGOS_CSV)
                registrar_historial(st.session_state.usuario,f"Registró pago {casos_df.loc[casos_df['id']==caso_id,'expediente'].values[0]}-{casos_df.loc[casos_df['id']==caso_id,'anio'].values[0]}")
                st.success("Pago registrado correctamente")
                st.experimental_rerun()
    
    st.subheader("Pagos realizados")
    if not pagos_df.empty:
        pagos_mostrar = pagos_df.merge(casos_df,left_on="caso_id",right_on="id",suffixes=("_pago","_caso"))
        pagos_mostrar = pagos_mostrar[["id_pago","expediente","anio","tipo","monto","fecha","observaciones"]]
        st.dataframe(pagos_mostrar)
        
        # Editar / Eliminar
        editar_id = st.number_input("ID Pago a Editar", step=1,key="editar_pago")
        if st.button("Editar Pago"):
            if int(editar_id) in pagos_df["id"].values:
                idx = pagos_df[pagos_df["id"]==int(editar_id)].index[0]
                pagos_df.at[idx,"fecha"]=st.date_input("Fecha",pd.to_datetime(pagos_df.at[idx,"fecha"]))
                pagos_df.at[idx,"tipo"]=st.selectbox("Tipo",["Honorarios","Cuota Litis"],index=0)
                pagos_df.at[idx,"monto"]=st.number_input("Monto",float(pagos_df.at[idx,"monto"]))
                pagos_df.at[idx,"observaciones"]=st.text_area("Observaciones",pagos_df.at[idx,"observaciones"])
                guardar_csv(pagos_df,PAGOS_CSV)
                registrar_historial(st.session_state.usuario,f"Editó pago ID {editar_id}")
                st.success("Pago editado correctamente")
                st.experimental_rerun()
        
        eliminar_id = st.number_input("ID Pago a Eliminar", step=1,key="elim_pago")
        if st.button("Eliminar Pago"):
            if int(eliminar_id) in pagos_df["id"].values:
                pagos_df = pagos_df[pagos_df["id"]!=int(eliminar_id)]
                guardar_csv(pagos_df,PAGOS_CSV)
                registrar_historial(st.session_state.usuario,f"Eliminó pago ID {eliminar_id}")
                st.success("Pago eliminado")
                st.experimental_rerun()

# ===============================
# CONTRATO (GENERACIÓN DOCX)
# ===============================
if st.session_state.login and menu=="Casos" and not casos_df.empty:
    st.subheader("📄 Generar Contrato")
    
    caso_seleccion = st.selectbox("Seleccionar Caso para Contrato",casos_df["expediente"].astype(str) + "-" + casos_df["anio"].astype(str))
    
    if st.button("Generar Contrato"):
        partes = caso_seleccion.split("-")
        expediente = partes[0]
        anio = partes[1]
        caso = casos_df[(casos_df["expediente"]==expediente)&(casos_df["anio"]==int(anio))].iloc[0]
        cliente = clientes_df[clientes_df["id"]==caso["cliente_id"]].iloc[0]
        
        # Crear documento
        doc = Document()
        doc.add_heading("CONTRATO DE PRESTACIÓN DE SERVICIOS",0)
        doc.add_paragraph(f"Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en Cajamarca, a quien en adelante se denominará EL LOCADOR; y de la otra parte, {cliente['nombre']}, con DNI/RUC N° {cliente['dni']}, a quien en adelante se denominará EL CLIENTE. Para todos sus efectos, el contrato se celebra bajo los siguientes términos y condiciones:")
        doc.add_heading("PRIMERO: ANTECEDENTES",level=1)
        doc.add_paragraph("1.1. EL LOCADOR es una persona natural que ejerce la profesión de abogado, debidamente registrado con la colegiatura número 2710 en el Ilustre Colegio de Abogados de Cajamarca.")
        doc.add_paragraph(f"1.2. EL CLIENTE requiere contratar los servicios del LOCADOR para el caso de expediente {caso['expediente']}-{caso['anio']} con pretensión: {caso['pretension']}.")
        doc.add_heading("SEGUNDO: OBJETO DEL CONTRATO",level=1)
        doc.add_paragraph(f"Por el presente contrato EL LOCADOR se obliga a patrocinar a EL CLIENTE en el proceso judicial o administrativo con expediente {caso['expediente']}-{caso['anio']}.")
        doc.add_heading("TERCERO: CONTRAPRESTACIÓN PACTADA",level=1)
        doc.add_paragraph(f"El monto pactado es de S/ {caso['monto_pactado']} y la cuota litis es de S/ {caso['cuota_litis']} ({caso['porcentaje']}%).")
        doc.add_heading("CUARTO: VIGENCIA",level=1)
        doc.add_paragraph("La duración del contrato es por tiempo indefinido, mientras se mantengan vigentes las prestaciones contenidas en su objeto.")
        doc.add_heading("OCTAVO: CLÁUSULA DE CONFORMIDAD",level=1)
        doc.add_paragraph("De común acuerdo entre las partes y en señal de conformidad con todos sus términos y condiciones, se suscribe el presente contrato por duplicado.")
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button("📄 Descargar Contrato",buffer,file_name=f"Contrato_{caso['expediente']}_{caso['anio']}.docx")
