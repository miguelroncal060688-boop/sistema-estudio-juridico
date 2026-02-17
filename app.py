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
    contraseña TEXT,
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
# LOGIN SIMPLE
# ===============================
if st.session_state.usuario is None:
    st.sidebar.title("Login")
    usuario_input = st.sidebar.text_input("Usuario")
    contraseña_input = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Ingresar"):
        user = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND contraseña=?", conn, params=(usuario_input, contraseña_input))
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
        clientes_df = pd.read_sql("SELECT * FROM clientes", conn)
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
        clientes_df = pd.read_sql("SELECT id,nombre FROM clientes",conn)
        casos_df = pd.read_sql("SELECT * FROM casos",conn)
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
        if not casos_df.empty:
            st.subheader("Lista de Casos")
            export_df_to_excel(casos_df,"casos.xlsx")
            for i,row in casos_df.iterrows():
                cliente_nombre = pd.read_sql(f"SELECT nombre FROM clientes WHERE id={row['cliente_id']}",conn).iloc[0,0]
                with st.expander(f"{cliente_nombre} - {row['numero_expediente']}-{row['anio']}"):
                    st.write(f"Materia: {row['materia']} / Abogado: {row['abogado']} / Etapa: {row['etapa_procesal']}")
                    st.write(f"Contraparte: {row['contraparte']}")
                    st.write(f"Monto pactado: {row['monto_pactado']} / Cuota Litis: {row['cuota_litis']} ({row['porcentaje']}%) / Base: {row['base_cuota']}")
                    st.write(f"Observaciones: {row['observaciones']}")
                    if st.button(f"Editar Caso {row['id']}"):
                        st.session_state.edit_caso=row['id']
                        st.experimental_rerun()
                    if st.button(f"Eliminar Caso {row['id']}"):
                        cursor.execute("DELETE FROM casos WHERE id=?",(row['id'],))
                        conn.commit()
                        st.experimental_rerun()

    # ===============================
    # PAGOS
    # ===============================
    elif menu=="Pagos":
        st.title("💰 Gestión de Pagos")
        casos_df = pd.read_sql("SELECT * FROM casos",conn)
        pagos_df = pd.read_sql("SELECT * FROM pagos",conn)
        if casos_df.empty:
            st.warning("No hay casos registrados")
        else:
            with st.expander("➕ Nuevo Pago"):
                casos_df["descripcion"] = casos_df["numero_expediente"].astype(str)+"-"+casos_df["anio"].astype(str)
                seleccion = st.selectbox("Seleccionar Caso",casos_df["descripcion"])
                caso_sel = casos_df[casos_df["descripcion"]==seleccion]
                if not caso_sel.empty:
                    caso_id = int(caso_sel["id"].values[0])
                else:
                    st.error("No se pudo identificar el caso")
                    caso_id=None
                fecha = st.date_input("Fecha",value=date.today())
                tipo = st.selectbox("Tipo",["Honorarios","Cuota Litis"])
                monto = st.number_input("Monto",min_value=0.0,format="%.2f")
                observaciones = st.text_area("Observaciones")
                if st.button("Guardar Pago") and caso_id is not None:
                    cursor.execute("INSERT INTO pagos (caso_id,fecha,tipo,monto,observaciones) VALUES (?,?,?,?,?)",(caso_id,str(fecha),tipo,monto,observaciones))
                    conn.commit()
                    st.success("Pago registrado")
                    st.experimental_rerun()
        if not pagos_df.empty:
            st.subheader("Pagos realizados")
            pagos_display = pagos_df.copy()
            pagos_display["caso"] = pagos_display["caso_id"].apply(lambda x: pd.read_sql(f"SELECT numero_expediente,anio FROM casos WHERE id={x}",conn).iloc[0,0]+"-"+str(pd.read_sql(f"SELECT numero_expediente,anio FROM casos WHERE id={x}",conn).iloc[0,1]))
            pagos_display["cliente"] = pagos_display["caso_id"].apply(lambda x: pd.read_sql(f"SELECT cliente_id FROM casos WHERE id={x}",conn).iloc[0,0])
            pagos_display["cliente"] = pagos_display["cliente"].apply(lambda x: pd.read_sql(f"SELECT nombre FROM clientes WHERE id={x}",conn).iloc[0,0])
            export_df_to_excel(pagos_display[["id","cliente","caso","fecha","tipo","monto","observaciones"]],"pagos.xlsx")
            st.dataframe(pagos_display[["id","cliente","caso","fecha","tipo","monto","observaciones"]])
            id_elim = st.number_input("ID Pago a eliminar",min_value=1,step=1)
            if st.button("Eliminar Pago"):
                cursor.execute("DELETE FROM pagos WHERE id=?",(id_elim,))
                conn.commit()
                st.experimental_rerun()

    # ===============================
    # CONTRATOS
    # ===============================
    elif menu=="Contratos":
        st.title("📝 Generación de Contratos")
        casos_df = pd.read_sql("SELECT * FROM casos",conn)
        clientes_df = pd.read_sql("SELECT * FROM clientes",conn)
        if casos_df.empty:
            st.warning("No hay casos para generar contrato")
        else:
            seleccion = st.selectbox("Seleccionar Caso",casos_df["numero_expediente"].astype(str)+"-"+casos_df["anio"].astype(str))
            caso = casos_df[casos_df["numero_expediente"].astype(str)+"-"+casos_df["anio"].astype(str)==seleccion]
            if not caso.empty:
                caso = caso.iloc[0]
                cliente = clientes_df[clientes_df["id"]==caso["cliente_id"]].iloc[0]
                numero_contrato = f"{caso['id']:04d}"
                contrato_txt = generar_contrato(caso,cliente,numero_contrato)
                st.text_area("Contrato generado",value=contrato_txt,height=400)
                if st.button("Guardar Contrato"):
                    cursor.execute("INSERT INTO contratos (caso_id,numero,fecha,contenido) VALUES (?,?,DATE('now'),?)",(caso["id"],numero_contrato,contrato_txt))
                    conn.commit()
                    st.success("Contrato guardado")

    # ===============================
    # HISTORIAL
    # ===============================
    elif menu=="Historial":
        st.title("📜 Historial de acciones")
        hist_df = pd.read_sql("SELECT * FROM historial ORDER BY fecha DESC",conn)
        if not hist_df.empty:
            st.dataframe(hist_df)
            export_df_to_excel(hist_df,"historial.xlsx")
