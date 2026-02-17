# =====================================================
# SISTEMA JURÍDICO ULTRA PRO - 100% GRATIS
# Multiusuario + Roles + Historial + Alertas + Backup
# Base de datos SQLite profesional
# =====================================================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

st.set_page_config(page_title="Sistema Jurídico ULTRA PRO", layout="wide")

# =====================================================
# CONEXIÓN BASE DE DATOS
# =====================================================

conn = sqlite3.connect("estudio_juridico.db", check_same_thread=False)
cursor = conn.cursor()

# ================= TABLAS =================

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    rol TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    dni TEXT,
    celular TEXT,
    correo TEXT,
    direccion TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS casos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    materia TEXT,
    expediente TEXT,
    anio TEXT,
    distrito TEXT,
    juzgado TEXT,
    tipo_proceso TEXT,
    estado TEXT,
    monto REAL,
    fecha_inicio TEXT,
    fecha_vencimiento TEXT,
    observaciones TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER,
    fecha TEXT,
    monto REAL,
    metodo TEXT,
    observacion TEXT
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

# =====================================================
# FUNCIONES
# =====================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_historial(usuario, accion):
    cursor.execute(
        "INSERT INTO historial (usuario,accion,fecha) VALUES (?,?,?)",
        (usuario, accion, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()

def obtener_df(query):
    return pd.read_sql_query(query, conn)

# =====================================================
# CREAR ADMIN POR DEFECTO
# =====================================================

cursor.execute("SELECT * FROM usuarios WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO usuarios (username,password,rol) VALUES (?,?,?)",
        ("admin", hash_password("admin123"), "Administrador")
    )
    conn.commit()

# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("Sistema Jurídico ULTRA PRO")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        cursor.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?",
            (username, hash_password(password))
        )
        user = cursor.fetchone()

        if user:
            st.session_state.login = True
            st.session_state.usuario = username
            st.session_state.rol = user[3]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

# =====================================================
# MENÚ SEGÚN ROL
# =====================================================

st.sidebar.write(f"Usuario: {st.session_state.usuario}")
st.sidebar.write(f"Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

menu = st.sidebar.selectbox("Menú", [
    "Dashboard",
    "Clientes",
    "Casos",
    "Pagos",
    "Usuarios",
    "Historial",
    "Backup",
    "Contrato PDF"
])

# =====================================================
# DASHBOARD
# =====================================================

if menu == "Dashboard":

    clientes = obtener_df("SELECT * FROM clientes")
    casos = obtener_df("SELECT * FROM casos")
    pagos = obtener_df("SELECT * FROM pagos")

    total_clientes = len(clientes)
    total_casos = len(casos)
    total_ingresos = pagos["monto"].sum() if not pagos.empty else 0

    pendiente = 0
    for _, caso in casos.iterrows():
        pagado = pagos[pagos["caso_id"] == caso["id"]]["monto"].sum()
        pendiente += caso["monto"] - pagado

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_ingresos}")
    col4.metric("Pendiente", f"S/ {pendiente}")

    st.subheader("Alertas")

    hoy = date.today()

    for _, caso in casos.iterrows():
        if caso["fecha_vencimiento"]:
            venc = datetime.strptime(caso["fecha_vencimiento"], "%Y-%m-%d").date()
            if venc < hoy:
                st.error(f"⚠ Caso vencido: {caso['expediente']}-{caso['anio']}")
            elif venc <= hoy + timedelta(days=7):
                st.warning(f"⏳ Caso por vencer: {caso['expediente']}-{caso['anio']}")

# =====================================================
# CLIENTES
# =====================================================

if menu == "Clientes":

    if st.session_state.rol != "Solo Lectura":

        with st.expander("Nuevo Cliente"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI")
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            direccion = st.text_input("Dirección")

            if st.button("Guardar Cliente"):
                cursor.execute(
                    "INSERT INTO clientes (nombre,dni,celular,correo,direccion) VALUES (?,?,?,?,?)",
                    (nombre,dni,celular,correo,direccion)
                )
                conn.commit()
                registrar_historial(st.session_state.usuario, f"Creó cliente {nombre}")
                st.success("Cliente guardado")
                st.rerun()

    st.dataframe(obtener_df("SELECT * FROM clientes"))

# =====================================================
# CASOS
# =====================================================

if menu == "Casos":

    clientes = obtener_df("SELECT * FROM clientes")
    cliente_dict = dict(zip(clientes["nombre"], clientes["id"]))

    if st.session_state.rol != "Solo Lectura":

        with st.expander("Nuevo Caso"):

            cliente_nombre = st.selectbox("Cliente", list(cliente_dict.keys()))
            materia = st.text_input("Materia")
            expediente = st.text_input("Expediente")
            anio = st.text_input("Año")
            distrito = st.text_input("Distrito Judicial")
            juzgado = st.text_input("Juzgado")
            tipo_proceso = st.text_input("Tipo de Proceso")
            estado = st.selectbox("Estado", ["Activo","En trámite","Archivado","Finalizado"])
            monto = st.number_input("Monto", 0.0)
            fecha_inicio = st.date_input("Fecha inicio")
            fecha_vencimiento = st.date_input("Fecha vencimiento")
            observaciones = st.text_area("Observaciones")

            if st.button("Guardar Caso"):
                cursor.execute("""
                    INSERT INTO casos
                    (cliente_id,materia,expediente,anio,distrito,juzgado,
                    tipo_proceso,estado,monto,fecha_inicio,fecha_vencimiento,observaciones)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,(cliente_dict[cliente_nombre],materia,expediente,anio,
                    distrito,juzgado,tipo_proceso,estado,monto,
                    fecha_inicio,fecha_vencimiento,observaciones))
                conn.commit()
                registrar_historial(st.session_state.usuario,
                                    f"Creó caso {expediente}-{anio}")
                st.success("Caso guardado")
                st.rerun()

    st.dataframe(obtener_df("SELECT * FROM casos"))

# =====================================================
# PAGOS
# =====================================================

if menu == "Pagos":

    casos = obtener_df("SELECT * FROM casos")
    caso_dict = {
        f"{row['expediente']}-{row['anio']}": row["id"]
        for _, row in casos.iterrows()
    }

    if st.session_state.rol != "Solo Lectura":

        caso_sel = st.selectbox("Caso", list(caso_dict.keys()))
        fecha = st.date_input("Fecha")
        monto = st.number_input("Monto",0.0)
        metodo = st.selectbox("Método",["Efectivo","Transferencia","Yape","Plin"])
        observacion = st.text_input("Observación")

        if st.button("Registrar Pago"):
            cursor.execute("""
                INSERT INTO pagos (caso_id,fecha,monto,metodo,observacion)
                VALUES (?,?,?,?,?)
            """,(caso_dict[caso_sel],fecha,monto,metodo,observacion))
            conn.commit()
            registrar_historial(st.session_state.usuario,
                                f"Registró pago en {caso_sel}")
            st.success("Pago registrado")
            st.rerun()

    st.dataframe(obtener_df("SELECT * FROM pagos"))

# =====================================================
# USUARIOS (Solo Admin)
# =====================================================

if menu == "Usuarios" and st.session_state.rol == "Administrador":

    with st.expander("Nuevo Usuario"):
        user = st.text_input("Usuario nuevo")
        pwd = st.text_input("Contraseña", type="password")
        rol = st.selectbox("Rol",["Administrador","Asistente","Solo Lectura"])

        if st.button("Crear Usuario"):
            cursor.execute(
                "INSERT INTO usuarios (username,password,rol) VALUES (?,?,?)",
                (user, hash_password(pwd), rol)
            )
            conn.commit()
            st.success("Usuario creado")
            st.rerun()

    st.dataframe(obtener_df("SELECT id,username,rol FROM usuarios"))

# =====================================================
# HISTORIAL
# =====================================================

if menu == "Historial" and st.session_state.rol == "Administrador":
    st.dataframe(obtener_df("SELECT * FROM historial ORDER BY id DESC"))

# =====================================================
# BACKUP
# =====================================================

if menu == "Backup" and st.session_state.rol == "Administrador":

    if st.button("Descargar Backup Completo"):
        with open("estudio_juridico.db","rb") as f:
            st.download_button("Descargar Base de Datos", f, "backup_estudio.db")

# =====================================================
# CONTRATO PDF
# =====================================================

if menu == "Contrato PDF":

    casos = obtener_df("SELECT * FROM casos")
    caso_dict = {
        f"{row['expediente']}-{row['anio']}": row["id"]
        for _, row in casos.iterrows()
    }

    caso_sel = st.selectbox("Caso", list(caso_dict.keys()))

    if st.button("Generar PDF"):
        archivo = f"Contrato_{caso_sel}.pdf"
        doc = SimpleDocTemplate(archivo,pagesize=A4)
        elementos = []
        estilos = getSampleStyleSheet()
        estilo = estilos["Normal"]

        texto = f"""
        CONTRATO DE PRESTACIÓN DE SERVICIOS LEGALES

        Caso: {caso_sel}
        Fecha: {datetime.today().strftime("%d/%m/%Y")}
        """

        elementos.append(Paragraph(texto, estilo))
        elementos.append(Spacer(1,0.5*inch))
        doc.build(elementos)

        with open(archivo,"rb") as f:
            st.download_button("Descargar PDF",f,archivo)
