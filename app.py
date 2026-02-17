# ===============================
# SISTEMA DE GESTIÓN JURÍDICA - BLOQUE 1
# ===============================
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

# ===============================
# CONEXIÓN A SQLITE
# ===============================
conn = sqlite3.connect("estudio_juridico.db", check_same_thread=False)
cursor = conn.cursor()

# ===============================
# CREACIÓN DE TABLAS SI NO EXISTEN
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
CREATE TABLE IF NOT EXISTS historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    accion TEXT,
    fecha TEXT
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
if "edit_cliente" not in st.session_state:
    st.session_state.edit_cliente = None

# ===============================
# FUNCIONES
# ===============================
def registrar_historial(usuario, accion):
    cursor.execute("INSERT INTO historial (usuario, accion, fecha) VALUES (?,?,DATE('now'))",(usuario,accion))
    conn.commit()

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
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND contrasena=?", (usuario_input, contrasena_input))
        user = cursor.fetchone()
        if user:
            st.session_state.usuario = user[1]
            st.session_state.rol = user[3]
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
# MENÚ CLIENTES
# ===============================
if st.session_state.usuario:
    menu = st.sidebar.selectbox("Menú", ["Clientes"])
    if menu=="Clientes":
        st.title("👥 Gestión de Clientes")
        clientes_df = pd.read_sql_query("SELECT * FROM clientes", conn)
        with st.expander("➕ Nuevo Cliente"):
            if st.session_state.edit_cliente:
                cursor.execute("SELECT * FROM clientes WHERE id=?",(st.session_state.edit_cliente,))
                c = cursor.fetchone()
                nombre = st.text_input("Nombre", c[1])
                dni = st.text_input("DNI", c[2])
                tipo_persona = st.selectbox("Tipo de persona", ["Natural","Jurídica"], index=0 if c[3]=="Natural" else 1)
                celular = st.text_input("Celular", c[4])
                correo = st.text_input("Correo", c[5])
                direccion = st.text_input("Dirección", c[6])
                contacto_emergencia = st.text_input("Contacto emergencia", c[7])
                numero_contacto = st.text_input("Número del contacto", c[8])
                observaciones = st.text_area("Observaciones", c[9])
                if st.button("Guardar Cliente Editado"):
                    cursor.execute("""
                        UPDATE clientes SET nombre=?, dni=?, tipo_persona=?, celular=?, correo=?, direccion=?, contacto_emergencia=?, numero_contacto=?, observaciones=?
                        WHERE id=?
                    """,(nombre,dni,tipo_persona,celular,correo,direccion,contacto_emergencia,numero_contacto,observaciones,st.session_state.edit_cliente))
                    conn.commit()
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
                    col1,col2 = st.columns(2)
                    with col1:
                        if st.button(f"Editar Cliente {row['id']}"):
                            st.session_state.edit_cliente=row['id']
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Eliminar Cliente {row['id']}"):
                            cursor.execute("DELETE FROM clientes WHERE id=?",(row['id'],))
                            conn.commit()
                            registrar_historial(st.session_state.usuario,f"Eliminó cliente {row['nombre']}")
                            st.experimental_rerun()
# ===============================
# BLOQUE 2 – CASOS, PAGOS, CONTRATOS Y USUARIOS
# ===============================

# ===============================
# TABLAS ADICIONALES
# ===============================
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
# FUNCIONES
# ===============================
def generar_contrato(caso, cliente, numero):
    plantilla = f"""
CONTRATO DE LOCACIÓN DE SERVICIOS PROFESIONALES N° {numero} - {caso['anio']} - CLS

Abogado: {caso['abogado']}
Cliente: {cliente['nombre']}
Expediente: {caso['numero_expediente']}-{caso['anio']}
Pretensión: {caso['pretension']}
Contraparte: {caso['contraparte']}

Monto pactado: S/ {caso['monto_pactado']}
Cuota Litis: S/ {caso['cuota_litis']} ({caso['porcentaje']}% sobre base S/ {caso['base_cuota']})

Observaciones: {caso['observaciones']}
"""
    return plantilla

# ===============================
# MENÚ PRINCIPAL EXTENDIDO
# ===============================
if st.session_state.usuario:
    menu = st.sidebar.selectbox("Menú", ["Clientes","Casos","Pagos","Contratos","Historial","Usuarios"])

    # ===============================
    # CASOS
    # ===============================
    if menu=="Casos":
        st.title("📁 Gestión de Casos")
        clientes_df = pd.read_sql_query("SELECT * FROM clientes", conn)
        casos_df = pd.read_sql_query("SELECT casos.*, clientes.nombre as cliente_nombre FROM casos JOIN clientes ON clientes.id=casos.cliente_id", conn)

        with st.expander("➕ Nuevo Caso"):
            cliente_selec = st.selectbox("Cliente", clientes_df["nombre"])
            cliente_id = clientes_df[clientes_df["nombre"]==cliente_selec]["id"].values[0]
            numero_expediente = st.text_input("Número de expediente")
            anio = st.number_input("Año", min_value=2000, max_value=2100, value=date.today().year)
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
                cursor.execute("""
                    INSERT INTO casos (cliente_id,numero_expediente,anio,materia,pretension,abogado,etapa_procesal,contraparte,monto_pactado,cuota_litis,porcentaje,base_cuota,observaciones)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,(cliente_id,numero_expediente,anio,materia,pretension,abogado,etapa_procesal,contraparte,monto_pactado,cuota_litis,porcentaje,base_cuota,observaciones))
                conn.commit()
                registrar_historial(st.session_state.usuario,f"Registró caso {numero_expediente}-{anio}")
                st.experimental_rerun()

        if not casos_df.empty:
            st.subheader("Lista de Casos")
            export_df_to_excel(casos_df,"casos.xlsx")
            for i,row in casos_df.iterrows():
                with st.expander(f"{row['cliente_nombre']} - {row['numero_expediente']}-{row['anio']}"):
                    st.write(f"Materia: {row['materia']}, Pretensión: {row['pretension']}")
                    st.write(f"Abogado: {row['abogado']}, Etapa: {row['etapa_procesal']}")
                    st.write(f"Contraparte: {row['contraparte']}")
                    st.write(f"Monto pactado: S/ {row['monto_pactado']}, Cuota Litis: S/ {row['cuota_litis']} ({row['porcentaje']}%)")
                    st.write(f"Base cuota: S/ {row['base_cuota']}")
                    st.write(f"Observaciones: {row['observaciones']}")
                    col1,col2,col3 = st.columns(3)
                    with col1:
                        if st.button(f"Editar Caso {row['id']}"):
                            st.session_state.edit_caso=row['id']
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"Eliminar Caso {row['id']}"):
                            cursor.execute("DELETE FROM casos WHERE id=?",(row['id'],))
                            cursor.execute("DELETE FROM pagos WHERE caso_id=?",(row['id'],))
                            cursor.execute("DELETE FROM contratos WHERE caso_id=?",(row['id'],))
                            conn.commit()
                            registrar_historial(st.session_state.usuario,f"Eliminó caso {row['numero_expediente']}-{row['anio']}")
                            st.experimental_rerun()
                    with col3:
                        if st.button(f"Generar Contrato {row['id']}"):
                            cliente = clientes_df[clientes_df["id"]==row['cliente_id']].iloc[0]
                            numero_contrato = f"{row['id']}-{row['anio']}"
                            contenido = generar_contrato(row, cliente, numero_contrato)
                            cursor.execute("INSERT INTO contratos (caso_id,numero,fecha,contenido) VALUES (?,?,DATE('now'),?)",
                                           (row['id'],numero_contrato,contenido))
                            conn.commit()
                            registrar_historial(st.session_state.usuario,f"Generó contrato {numero_contrato}")
                            st.success(f"Contrato generado: N° {numero_contrato}")

# ===============================
# PAGOS
# ===============================
    if menu=="Pagos":
        st.title("💰 Gestión de Pagos")
        pagos_df = pd.read_sql_query("""
            SELECT pagos.id, clientes.nombre as cliente, casos.numero_expediente, casos.anio, pagos.fecha, pagos.tipo, pagos.monto
            FROM pagos
            JOIN casos ON casos.id=pagos.caso_id
            JOIN clientes ON clientes.id=casos.cliente_id
        """, conn)
        casos_df = pd.read_sql_query("SELECT casos.*, clientes.nombre as cliente_nombre FROM casos JOIN clientes ON clientes.id=casos.cliente_id", conn)

        with st.expander("➕ Nuevo Pago"):
            if not casos_df.empty:
                casos_df["descripcion"] = casos_df["cliente_nombre"]+" | Exp: "+casos_df["numero_expediente"]+"-"+casos_df["anio"].astype(str)
                seleccion = st.selectbox("Seleccionar Caso", casos_df["descripcion"])
                caso_id = casos_df[casos_df["descripcion"]==seleccion]["id"].values[0]
                fecha = st.date_input("Fecha")
                tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
                monto = st.number_input("Monto",0.0)
                observaciones = st.text_area("Observaciones")
                if st.button("Guardar Pago"):
                    cursor.execute("INSERT INTO pagos (caso_id,fecha,tipo,monto,observaciones) VALUES (?,?,?,?,?)",
                                   (caso_id,str(fecha),tipo,monto,observaciones))
                    conn.commit()
                    registrar_historial(st.session_state.usuario,f"Registró pago en caso {seleccion}")
                    st.experimental_rerun()

        if not pagos_df.empty:
            st.subheader("Lista de Pagos")
            export_df_to_excel(pagos_df,"pagos.xlsx")
            for i,row in pagos_df.iterrows():
                with st.expander(f"{row['cliente']} - {row['numero_expediente']}-{row['anio']} / {row['tipo']}"):
                    st.write(f"Fecha: {row['fecha']}, Monto: S/ {row['monto']}")
                    st.write(f"Observaciones: {row['observaciones']}")
                    if st.button(f"Eliminar Pago {row['id']}"):
                        cursor.execute("DELETE FROM pagos WHERE id=?",(row['id'],))
                        conn.commit()
                        registrar_historial(st.session_state.usuario,f"Eliminó pago {row['id']}")
                        st.experimental_rerun()

# ===============================
# CONTRATOS
# ===============================
    if menu=="Contratos":
        st.title("📄 Contratos")
        contratos_df = pd.read_sql_query("""
            SELECT contratos.id, contratos.numero, contratos.fecha, casos.numero_expediente, casos.anio, clientes.nombre as cliente
            FROM contratos
            JOIN casos ON casos.id=contratos.caso_id
            JOIN clientes ON clientes.id=casos.cliente_id
        """, conn)
        if not contratos_df.empty:
            export_df_to_excel(contratos_df,"contratos.xlsx")
            for i,row in contratos_df.iterrows():
                with st.expander(f"{row['cliente']} - {row['numero_expediente']}-{row['anio']}"):
                    st.write(f"Número de Contrato: {row['numero']}, Fecha: {row['fecha']}")
                    contenido = pd.read_sql_query(f"SELECT contenido FROM contratos WHERE id={row['id']}", conn).iloc[0,0]
                    st.text_area("Contenido",contenido,height=300)

# ===============================
# HISTORIAL
# ===============================
    if menu=="Historial":
        st.title("📝 Historial de Acciones")
        historial_df = pd.read_sql_query("SELECT * FROM historial ORDER BY fecha DESC", conn)
        if not historial_df.empty:
            export_df_to_excel(historial_df,"historial.xlsx")
            st.dataframe(historial_df)

# ===============================
# USUARIOS
# ===============================
    if menu=="Usuarios" and st.session_state.rol=="admin":
        st.title("👤 Gestión de Usuarios")
        usuarios_df = pd.read_sql_query("SELECT * FROM usuarios", conn)
        with st.expander("➕ Nuevo Usuario"):
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña",type="password")
            rol = st.selectbox("Rol", ["admin","abogado"])
            if st.button("Guardar Usuario"):
                cursor.execute("INSERT INTO usuarios (usuario,contrasena,rol) VALUES (?,?,?)",(usuario,contrasena,rol))
                conn.commit()
                registrar_historial(st.session_state.usuario,f"Registró usuario {usuario}")
                st.experimental_rerun()
        if not usuarios_df.empty:
            export_df_to_excel(usuarios_df,"usuarios.xlsx")
            st.dataframe(usuarios_df)
