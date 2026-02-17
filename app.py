import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os
import io

st.set_page_config(page_title="Sistema Estudio Jurídico", layout="wide")

# ===============================
# BASE DE DATOS SQLITE
# ===============================

def get_connection():
    return sqlite3.connect("estudio.db", check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

# ===============================
# CREAR TABLAS
# ===============================

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    password TEXT,
    rol TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    nombre TEXT,
    documento TEXT,
    representante TEXT,
    dni_representante TEXT,
    direccion TEXT,
    celular TEXT,
    correo TEXT,
    contacto_emergencia TEXT,
    telefono_emergencia TEXT,
    observaciones TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS casos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    expediente TEXT,
    anio TEXT,
    materia TEXT,
    pretension TEXT,
    abogado TEXT,
    etapa TEXT,
    contraparte TEXT,
    monto REAL,
    cuota_porcentaje REAL,
    base_calculo REAL,
    cuota_calculada REAL,
    observaciones TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER,
    fecha TEXT,
    tipo TEXT,
    monto REAL,
    observaciones TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT,
    anio TEXT,
    caso_id INTEGER,
    fecha TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    accion TEXT,
    fecha TEXT
)
""")

conn.commit()

# ===============================
# CREAR ADMIN POR DEFECTO
# ===============================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO usuarios (usuario,password,rol) VALUES (?,?,?)",
        ("admin", hash_password("admin123"), "Administrador")
    )
    conn.commit()

# ===============================
# FUNCIONES UTILITARIAS
# ===============================

def registrar_historial(usuario, accion):
    cursor.execute(
        "INSERT INTO historial (usuario,accion,fecha) VALUES (?,?,?)",
        (usuario, accion, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

def numero_contrato():
    anio_actual = datetime.now().year
    cursor.execute("SELECT COUNT(*) FROM contratos WHERE anio=?", (anio_actual,))
    total = cursor.fetchone()[0] + 1
    return f"{str(total).zfill(4)}-{anio_actual}-CLS"

def numero_a_letras(numero):
    unidades = ["","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve"]
    especiales = ["diez","once","doce","trece","catorce","quince"]
    decenas = ["","diez","veinte","treinta"]

    if numero < 10:
        return unidades[numero]
    if numero < 16:
        return especiales[numero-10]
    if numero < 20:
        return "dieci" + unidades[numero-10]
    if numero < 30:
        return "veinti" + unidades[numero-20]
    if numero < 40:
        return "treinta y " + unidades[numero-30]
    return str(numero)

def fecha_formal():
    hoy = datetime.now()
    dia = numero_a_letras(hoy.day)
    mes = hoy.strftime("%B")
    anio = hoy.year
    return f"a los {dia} días del mes de {mes} del año {anio}"

# ===============================
# LOGIN
# ===============================

if "login" not in st.session_state:
    st.session_state.login = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

if not st.session_state.login:
    st.title("🔐 Sistema Estudio Jurídico")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (user,))
        data = cursor.fetchone()
        if data and data[2] == hash_password(password):
            st.session_state.login = True
            st.session_state.usuario = user
            st.session_state.rol = data[3]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

# ===============================
# MENÚ
# ===============================

st.sidebar.title(f"👤 {st.session_state.usuario}")
menu = st.sidebar.selectbox("Menú",
    ["Dashboard","Clientes","Casos","Pagos","Contratos","Usuarios","Historial","Exportar"]
)
# ===============================
# DASHBOARD
# ===============================

if menu == "Dashboard":
    st.title("📊 Dashboard Financiero")

    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_casos = cursor.execute("SELECT COUNT(*) FROM casos").fetchone()[0]
    total_pagos = cursor.execute("SELECT SUM(monto) FROM pagos").fetchone()[0] or 0

    total_honorarios = cursor.execute("SELECT SUM(monto) FROM casos").fetchone()[0] or 0
    total_cuota = cursor.execute("SELECT SUM(cuota_calculada) FROM casos").fetchone()[0] or 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Total Pagado", f"S/ {round(total_pagos,2)}")

    st.markdown("### 💰 Proyección")
    st.write(f"Honorarios pactados: S/ {round(total_honorarios,2)}")
    st.write(f"Cuota litis proyectada: S/ {round(total_cuota,2)}")
    st.write(f"Total proyectado: S/ {round(total_honorarios + total_cuota,2)}")


# ===============================
# CLIENTES
# ===============================

if menu == "Clientes":
    st.title("👤 Gestión de Clientes")

    with st.expander("➕ Nuevo Cliente"):
        tipo = st.selectbox("Tipo", ["Persona Natural","Persona Jurídica"])
        nombre = st.text_input("Nombre / Razón Social")
        documento = st.text_input("DNI o RUC")
        representante = ""
        dni_rep = ""

        if tipo == "Persona Jurídica":
            representante = st.text_input("Representante Legal")
            dni_rep = st.text_input("DNI Representante")

        direccion = st.text_input("Dirección")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        contacto = st.text_input("Contacto Emergencia")
        tel_contacto = st.text_input("Teléfono Emergencia")
        obs = st.text_area("Observaciones")

        if st.button("Guardar Cliente"):
            cursor.execute("""
            INSERT INTO clientes 
            (tipo,nombre,documento,representante,dni_representante,direccion,celular,correo,contacto_emergencia,telefono_emergencia,observaciones)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,(tipo,nombre,documento,representante,dni_rep,direccion,celular,correo,contacto,tel_contacto,obs))
            conn.commit()
            registrar_historial(st.session_state.usuario,"Creó cliente")
            st.success("Cliente registrado")
            st.rerun()

    df = pd.read_sql("SELECT * FROM clientes", conn)
    st.dataframe(df)

    if not df.empty:
        id_eliminar = st.number_input("ID Cliente a eliminar", step=1)
        if st.button("Eliminar Cliente"):
            cursor.execute("DELETE FROM clientes WHERE id=?", (id_eliminar,))
            conn.commit()
            registrar_historial(st.session_state.usuario,"Eliminó cliente")
            st.success("Cliente eliminado")
            st.rerun()


# ===============================
# CASOS
# ===============================

if menu == "Casos":
    st.title("⚖ Gestión de Casos")

    clientes_df = pd.read_sql("SELECT id,nombre FROM clientes", conn)

    if clientes_df.empty:
        st.warning("Primero debes registrar un cliente")
    else:
        with st.expander("➕ Nuevo Caso"):
            cliente_sel = st.selectbox("Cliente", clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==cliente_sel]["id"].values[0]

            expediente = st.text_input("Número de Expediente")
            anio = st.text_input("Año")
            materia = st.text_input("Materia")
            pretension = st.text_area("Pretensión (Objeto del contrato)")
            abogado = st.text_input("Abogado a cargo")
            etapa = st.text_input("Etapa procesal")
            contraparte = st.text_input("Contraparte")
            monto = st.number_input("Monto pactado",0.0)
            porcentaje = st.number_input("Cuota litis %",0.0)
            base = st.number_input("Base cálculo cuota litis",0.0)
            cuota_calc = base*(porcentaje/100)
            obs = st.text_area("Observaciones")

            st.write(f"Cuota litis calculada: S/ {round(cuota_calc,2)}")

            if st.button("Guardar Caso"):
                cursor.execute("""
                INSERT INTO casos
                (cliente_id,expediente,anio,materia,pretension,abogado,etapa,contraparte,monto,cuota_porcentaje,base_calculo,cuota_calculada,observaciones)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,(cliente_id,expediente,anio,materia,pretension,abogado,etapa,contraparte,monto,porcentaje,base,cuota_calc,obs))
                conn.commit()
                registrar_historial(st.session_state.usuario,"Creó caso")
                st.success("Caso registrado")
                st.rerun()

    casos_df = pd.read_sql("""
    SELECT casos.id,clientes.nombre,expediente,anio,materia,abogado,monto,cuota_calculada 
    FROM casos
    JOIN clientes ON clientes.id = casos.cliente_id
    """, conn)

    if st.session_state.rol == "Abogado":
        casos_df = casos_df[casos_df["abogado"] == st.session_state.usuario]

    st.dataframe(casos_df)

    if not casos_df.empty:
        id_eliminar = st.number_input("ID Caso a eliminar", step=1)
        if st.button("Eliminar Caso"):
            cursor.execute("DELETE FROM casos WHERE id=?", (id_eliminar,))
            conn.commit()
            registrar_historial(st.session_state.usuario,"Eliminó caso")
            st.success("Caso eliminado")
            st.rerun()


# ===============================
# PAGOS
# ===============================

if menu == "Pagos":
    st.title("💰 Gestión de Pagos")

    casos_df = pd.read_sql("SELECT id,expediente,anio FROM casos", conn)

    if not casos_df.empty:
        with st.expander("➕ Nuevo Pago"):
            seleccion = st.selectbox(
                "Expediente",
                casos_df["expediente"] + "-" + casos_df["anio"]
            )
            partes = seleccion.split("-")
            caso = casos_df[
                (casos_df["expediente"]==partes[0]) &
                (casos_df["anio"]==partes[1])
            ].iloc[0]

            fecha = st.date_input("Fecha")
            tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
            monto = st.number_input("Monto",0.0)
            obs = st.text_area("Observaciones")

            if st.button("Guardar Pago"):
                cursor.execute("""
                INSERT INTO pagos (caso_id,fecha,tipo,monto,observaciones)
                VALUES (?,?,?,?,?)
                """,(caso["id"],str(fecha),tipo,monto,obs))
                conn.commit()
                registrar_historial(st.session_state.usuario,"Registró pago")
                st.success("Pago registrado")
                st.rerun()

    pagos_df = pd.read_sql("""
    SELECT pagos.id,expediente,anio,fecha,tipo,monto
    FROM pagos
    JOIN casos ON casos.id = pagos.caso_id
    """, conn)

    st.dataframe(pagos_df)


# ===============================
# CONTRATOS PDF
# ===============================

if menu == "Contratos":
    st.title("📄 Generar Contrato")

    casos_df = pd.read_sql("""
    SELECT casos.id,clientes.tipo,clientes.nombre,clientes.documento,
           clientes.representante,clientes.dni_representante,
           expediente,anio,pretension,monto,cuota_porcentaje,base_calculo,cuota_calculada
    FROM casos
    JOIN clientes ON clientes.id = casos.cliente_id
    """, conn)

    if not casos_df.empty:
        seleccion = st.selectbox(
            "Seleccionar Caso",
            casos_df["expediente"] + "-" + casos_df["anio"]
        )

        partes = seleccion.split("-")
        caso = casos_df[
            (casos_df["expediente"]==partes[0]) &
            (casos_df["anio"]==partes[1])
        ].iloc[0]

        if st.button("Generar Contrato PDF"):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            styles = getSampleStyleSheet()
            estilo_titulo = ParagraphStyle(
                'Titulo',
                parent=styles['Heading1'],
                alignment=TA_CENTER,
                fontSize=14,
                spaceAfter=20
            )

            numero = numero_contrato()

            titulo = f"""
            CONTRATO DE LOCACIÓN DE SERVICIOS PROFESIONALES<br/>
            N° {numero}
            """

            elements.append(Paragraph(titulo, estilo_titulo))
            elements.append(Spacer(1, 12))

            texto = f"""
            Conste por el presente documento el contrato que celebran de una parte 
            MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926,
            a quien en adelante se denominará EL LOCADOR; y de la otra parte 
            {caso['nombre']} identificado con documento N° {caso['documento']}.
            """

            elements.append(Paragraph(texto, styles["Normal"]))
            elements.append(Spacer(1, 12))

            objeto = f"""
            OBJETO: Patrocinio del expediente N° {caso['expediente']}-{caso['anio']}.
            Pretensión: {caso['pretension']}.
            """

            elements.append(Paragraph(objeto, styles["Normal"]))
            elements.append(Spacer(1, 12))

            honorarios = f"""
            HONORARIOS: S/ {caso['monto']}.
            Cuota Litis: {caso['cuota_porcentaje']}% sobre base S/ {caso['base_calculo']}
            equivalente a S/ {caso['cuota_calculada']}.
            """

            elements.append(Paragraph(honorarios, styles["Normal"]))
            elements.append(Spacer(1, 12))

            cesion = """
            CLÁUSULA DE CESIÓN: El cliente cede los derechos de cobro
            correspondientes a la cuota litis pactada.
            """

            elements.append(Paragraph(cesion, styles["Normal"]))
            elements.append(Spacer(1, 12))

            fecha_txt = fecha_formal()
            elements.append(Paragraph(fecha_txt, styles["Normal"]))

            doc.build(elements)

            buffer.seek(0)

            cursor.execute(
                "INSERT INTO contratos (numero,anio,caso_id,fecha) VALUES (?,?,?,?)",
                (numero,datetime.now().year,caso["id"],datetime.now().strftime("%Y-%m-%d"))
            )
            conn.commit()

            st.download_button(
                label="Descargar Contrato",
                data=buffer,
                file_name=f"Contrato_{numero}.pdf",
                mime="application/pdf"
            )


# ===============================
# USUARIOS
# ===============================

if menu == "Usuarios" and st.session_state.rol == "Administrador":
    st.title("👥 Gestión de Usuarios")

    nuevo_user = st.text_input("Usuario")
    nueva_pass = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol",["Administrador","Asistente","Abogado","Solo lectura"])

    if st.button("Crear Usuario"):
        cursor.execute(
            "INSERT INTO usuarios (usuario,password,rol) VALUES (?,?,?)",
            (nuevo_user,hash_password(nueva_pass),rol)
        )
        conn.commit()
        st.success("Usuario creado")
        st.rerun()

    df = pd.read_sql("SELECT id,usuario,rol FROM usuarios", conn)
    st.dataframe(df)


# ===============================
# HISTORIAL
# ===============================

if menu == "Historial" and st.session_state.rol == "Administrador":
    df = pd.read_sql("SELECT * FROM historial", conn)
    st.dataframe(df)


# ===============================
# EXPORTAR
# ===============================

if menu == "Exportar":
    st.title("📤 Exportar Información")

    tablas = ["clientes","casos","pagos"]
    seleccion = st.selectbox("Seleccionar tabla", tablas)

    df = pd.read_sql(f"SELECT * FROM {seleccion}", conn)

    st.download_button(
        label="Descargar Excel",
        data=df.to_csv(index=False),
        file_name=f"{seleccion}.csv",
        mime="text/csv"
    )
