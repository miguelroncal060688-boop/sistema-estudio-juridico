# ===============================
# SISTEMA JURÍDICO COMPLETO - VERSIÓN FINAL
# ===============================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from io import BytesIO

# ===============================
# CONEXIÓN A SQLITE
# ===============================
conn = sqlite3.connect("estudio_juridico.db", check_same_thread=False)
cursor = conn.cursor()

# ===============================
# TABLAS
# ===============================
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE,
    contrasena TEXT,
    rol TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    dni TEXT,
    tipo_persona TEXT,
    celular TEXT,
    correo TEXT,
    direccion TEXT,
    contacto_emergencia TEXT,
    numero_contacto TEXT,
    observaciones TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS casos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    numero_expediente TEXT,
    anio INTEGER,
    materia TEXT,
    pretension TEXT,
    abogado TEXT,
    etapa_procesal TEXT,
    contraparte TEXT,
    monto_pactado REAL,
    cuota_litis REAL,
    porcentaje REAL,
    base_cuota REAL,
    observaciones TEXT,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER,
    fecha TEXT,
    tipo TEXT,
    monto REAL,
    observaciones TEXT,
    FOREIGN KEY(caso_id) REFERENCES casos(id)
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
cursor.execute("""
CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER,
    numero TEXT,
    fecha TEXT,
    contenido TEXT,
    FOREIGN KEY(caso_id) REFERENCES casos(id)
)
""")
conn.commit()

# ===============================
# SESIÓN
# ===============================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None

# ===============================
# FUNCIONES
# ===============================
def registrar_historial(usuario, accion):
    cursor.execute("INSERT INTO historial (usuario, accion, fecha) VALUES (?,?,DATE('now'))",(usuario,accion))
    conn.commit()

def generar_contrato(caso, cliente, numero):
    plantilla = f"""
CONTRATO DE LOCACIÓN DE SERVICIOS PROFESIONALES N° {numero} - {caso['anio']} - CLS

Conste por el presente documento que el abogado {caso['abogado']} se compromete con {cliente['nombre']} a prestar servicios legales conforme al expediente {caso['numero_expediente']}-{caso['anio']}, con pretensión: {caso['pretension']} y contraparte: {caso['contraparte']}.

Monto pactado: S/ {caso['monto_pactado']}
Cuota Litis: S/ {caso['cuota_litis']} ({caso['porcentaje']}% sobre base S/ {caso['base_cuota']})

Observaciones: {caso['observaciones']}
"""
    return plantilla

def export_df_to_excel(df, filename="export.xlsx"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        writer.save()
    st.download_button(label="Descargar Excel", data=output.getvalue(), file_name=filename)

# ===============================
# LOGIN
# ===============================
if st.session_state.usuario is None:
    st.sidebar.title("Login")
    usuario_input = st.sidebar.text_input("Usuario")
    contrasena_input = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Ingresar"):
        query = "SELECT * FROM usuarios WHERE usuario=? AND contrasena=?"
        user = pd.read_sql_query(query, conn, params=(usuario_input, contrasena_input))
        if not user.empty:
            st.session_state.usuario = usuario_input
            st.session_state.rol = user.iloc[0]["rol"]
            st.experimental_rerun()
        else:
            st.sidebar.error("Usuario o contraseña incorrecto")
else:
    st.sidebar.write(f"Usuario: {st.session_state.usuario} ({st.session_state.rol})")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.experimental_rerun()

# ===============================
# MENÚ PRINCIPAL
# ===============================
if st.session_state.usuario:
    menu = st.sidebar.selectbox("Menú", ["Clientes","Casos","Pagos","Contratos","Historial"])

    # ===============================
    # CLIENTES
    # ===============================
    if menu=="Clientes":
        st.title("👥 Gestión de Clientes")
        clientes_df = pd.read_sql_query("SELECT * FROM clientes", conn)
        with st.expander("➕ Nuevo Cliente"):
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
                cursor.execute("""
                    INSERT INTO clientes (nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """,(nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones))
                conn.commit()
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
                    if st.button(f"Editar Cliente {row['id']}"):
                        st.session_state.edit_cliente=row['id']
                        st.experimental_rerun()
                    if st.button(f"Eliminar Cliente {row['id']}"):
                        cursor.execute("DELETE FROM clientes WHERE id=?",(row['id'],))
                        conn.commit()
                        st.experimental_rerun()

    # ===============================
    # CASOS
    # ===============================
    elif menu=="Casos":
        st.title("📂 Gestión de Casos")
        clientes_df = pd.read_sql_query("SELECT id,nombre FROM clientes",conn)
        casos_df = pd.read_sql_query("SELECT * FROM casos",conn)
        with st.expander("➕ Nuevo Caso"):
            if clientes_df.empty:
                st.warning("Debe registrar al menos un cliente")
            else:
                cliente_sel = st.selectbox("Cliente",clientes_df["nombre"])
                cliente_id = int(clientes_df[clientes_df["nombre"]==cliente_sel]["id"].values[0])
                numero_expediente = st.text_input("Número de expediente")
                anio = st.number_input("Año",min_value=2000,max_value=2100,value=date.today().year)
                materia = st.text_input("Materia")
                pretension = st.text_input("Pretensión")
                abogado = st.text_input("Abogado a cargo")
                etapa = st.text_input("Etapa procesal")
                contraparte = st.text_input("Contraparte")
                monto_pactado = st.number_input("Monto pactado",min_value=0.0)
                cuota_litis = st.number_input("Cuota Litis",min_value=0.0)
                porcentaje = st.number_input("Porcentaje (%)",min_value=0.0,max_value=100.0)
                base_cuota = st.number_input("Base para cálculo",min_value=0.0)
                observaciones = st.text_area("Observaciones")
                if st.button("Guardar Caso"):
                    cursor.execute("""
                        INSERT INTO casos (cliente_id,numero_expediente,anio,materia,pretension,abogado,etapa_procesal,contraparte,monto_pactado,cuota_litis,porcentaje,base_cuota,observaciones)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,(cliente_id,numero_expediente,anio,materia,pretension,abogado,etapa,contraparte,monto_pactado,cuota_litis,porcentaje,base_cuota,observaciones))
                    conn.commit()
                    registrar_historial(st.session_state.usuario,f"Registró caso {numero_expediente}-{anio}")
                    st.experimental_rerun()
