import streamlit as st
import sqlite3
from datetime import date, datetime

st.set_page_config(page_title="Estudio Jurídico Roncal Liñán y Asociados ⚖️", layout="wide")

# ============================
# CONEXIÓN A BASE DE DATOS
# ============================
conn = sqlite3.connect("estudio_roncal.db", check_same_thread=False)
c = conn.cursor()

# Crear tablas si no existen
c.execute("""CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            rol TEXT,
            abogado_id INTEGER
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS abogados(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            dni TEXT,
            celular TEXT,
            correo TEXT,
            colegiatura TEXT,
            domicilio TEXT,
            casilla_electronica TEXT,
            casilla_judicial TEXT
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS clientes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            dni TEXT,
            celular TEXT,
            correo TEXT,
            direccion TEXT,
            observaciones TEXT
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS casos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente TEXT,
            año TEXT,
            cliente_id INTEGER,
            abogado_id INTEGER,
            materia TEXT,
            estado TEXT,
            pretension TEXT,
            monto_honorarios REAL,
            monto_base REAL,
            porcentaje_litis REAL,
            observaciones TEXT
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS pagos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caso_id INTEGER,
            fecha TEXT,
            monto REAL,
            observaciones TEXT
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS pagos_litis(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caso_id INTEGER,
            fecha TEXT,
            monto REAL,
            observaciones TEXT
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS cronograma(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caso_id INTEGER,
            fecha_pago TEXT,
            monto REAL,
            observaciones TEXT
            )""")
conn.commit()

# Crear admin por defecto si no existe
c.execute("SELECT * FROM usuarios WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO usuarios(username,password,rol) VALUES ('admin','admin123','admin')")
    conn.commit()

# ============================
# LOGIN
# ============================
if "login" not in st.session_state:
    st.session_state.login = False
if "rol" not in st.session_state:
    st.session_state.rol = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.login:
    st.title("Acceso al Sistema")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        c.execute("SELECT id,rol FROM usuarios WHERE username=? AND password=?", (username,password))
        result = c.fetchone()
        if result:
            st.session_state.login = True
            st.session_state.user_id = result[0]
            st.session_state.rol = result[1]
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ============================
# MENÚ PRINCIPAL
# ============================
menu_items = ["Dashboard","Clientes","Abogados","Casos","Pagos","Cuota Litis",
              "Pagos Cuota Litis","Cronograma","Pendientes de Cobro","Resumen Financiero","Usuarios"]
menu = st.sidebar.selectbox("Menú", menu_items)

# ============================
# FUNCIONES AUXILIARES
# ============================
def obtener_clientes():
    c.execute("SELECT * FROM clientes")
    return c.fetchall()

def obtener_abogados():
    c.execute("SELECT * FROM abogados")
    return c.fetchall()

def obtener_casos(usuario_id=None, rol=None):
    if rol=="abogado":
        c.execute("SELECT * FROM casos WHERE abogado_id=?", (usuario_id,))
    else:
        c.execute("SELECT * FROM casos")
    return c.fetchall()

def obtener_pagos():
    c.execute("SELECT * FROM pagos")
    return c.fetchall()

def obtener_pagos_litis():
    c.execute("SELECT * FROM pagos_litis")
    return c.fetchall()

def obtener_cronograma():
    c.execute("SELECT * FROM cronograma")
    return c.fetchall()

# ============================
# DASHBOARD
# ============================
if menu=="Dashboard":
    st.title("Estudio Jurídico Roncal Liñán y Asociados ⚖️")
    c.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM casos")
    total_casos = c.fetchone()[0]
    c.execute("SELECT SUM(monto_honorarios) FROM casos")
    total_honorarios = c.fetchone()[0] or 0
    c.execute("SELECT SUM(monto_base*(porcentaje_litis/100)) FROM casos")
    total_litis = c.fetchone()[0] or 0
    c.execute("SELECT SUM(monto) FROM pagos")
    pagado_honorarios = c.fetchone()[0] or 0
    c.execute("SELECT SUM(monto) FROM pagos_litis")
    pagado_litis = c.fetchone()[0] or 0
    total_pagado = pagado_honorarios + pagado_litis
    total_pendiente = (total_honorarios+total_litis)-total_pagado

    col1,col2,col3,col4,col5,col6 = st.columns(6)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Honorarios Pactados", f"S/ {total_honorarios:,.2f}")
    col4.metric("Cuota Litis Calculada", f"S/ {total_litis:,.2f}")
    col5.metric("Total Pagado", f"S/ {total_pagado:,.2f}")
    col6.metric("Total Pendiente", f"S/ {total_pendiente:,.2f}")

# ============================
# CLIENTES
# ============================
if menu=="Clientes":
    st.title("Gestión de Clientes")
    with st.form("form_cliente"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        observaciones = st.text_area("Observaciones")
        if st.form_submit_button("Guardar Cliente"):
            c.execute("INSERT INTO clientes(nombre,dni,celular,correo,direccion,observaciones) VALUES (?,?,?,?,?,?)",
                      (nombre,dni,celular,correo,direccion,observaciones))
            conn.commit()
            st.success("Cliente guardado")
            st.experimental_rerun()
    st.subheader("Clientes registrados")
    clientes_data = obtener_clientes()
    for cli in clientes_data:
        st.write(f"**{cli[1]}** - DNI: {cli[2]} - Celular: {cli[3]} - Correo: {cli[4]}")
        col1,col2 = st.columns(2)
        if col1.button("Editar", key=f"edit_cli_{cli[0]}"):
            with st.form(f"edit_cliente_form_{cli[0]}"):
                nombre_e = st.text_input("Nombre", cli[1])
                dni_e = st.text_input("DNI", cli[2])
                celular_e = st.text_input("Celular", cli[3])
                correo_e = st.text_input("Correo", cli[4])
                direccion_e = st.text_input("Dirección", cli[5])
                observaciones_e = st.text_area("Observaciones", cli[6])
                if st.form_submit_button("Guardar cambios"):
                    c.execute("""UPDATE clientes SET nombre=?,dni=?,celular=?,correo=?,direccion=?,observaciones=?
                                 WHERE id=?""",
                              (nombre_e,dni_e,celular_e,correo_e,direccion_e,observaciones_e,cli[0]))
                    conn.commit()
                    st.success("Cliente actualizado")
                    st.experimental_rerun()
        if col2.button("Eliminar", key=f"del_cli_{cli[0]}"):
            c.execute("DELETE FROM clientes WHERE id=?",(cli[0],))
            conn.commit()
            st.success("Cliente eliminado")
            st.experimental_rerun()

# ============================
# ABGADOS
# ============================
if menu=="Abogados":
    st.title("Gestión de Abogados")
    with st.form("form_abogado"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        colegiatura = st.text_input("Colegiatura")
        domicilio = st.text_input("Domicilio procesal")
        casilla_e = st.text_input("Casilla electrónica")
        casilla_j = st.text_input("Casilla judicial")
        if st.form_submit_button("Guardar Abogado"):
            c.execute("""INSERT INTO abogados(nombre,dni,celular,correo,colegiatura,domicilio,casilla_electronica,casilla_judicial)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (nombre,dni,celular,correo,colegiatura,domicilio,casilla_e,casilla_j))
            conn.commit()
            st.success("Abogado guardado")
            st.experimental_rerun()
    st.subheader("Abogados registrados")
    abogados_data = obtener_abogados()
    for ab in abogados_data:
        st.write(f"**{ab[1]}** - DNI: {ab[2]} - Celular: {ab[3]} - Correo: {ab[4]}")
        col1,col2 = st.columns(2)
        if col1.button("Editar", key=f"edit_ab_{ab[0]}"):
            with st.form(f"edit_abogado_form_{ab[0]}"):
                nombre_e = st.text_input("Nombre", ab[1])
                dni_e = st.text_input("DNI", ab[2])
                celular_e = st.text_input("Celular", ab[3])
                correo_e = st.text_input("Correo", ab[4])
                colegiatura_e = st.text_input("Colegiatura", ab[5])
                domicilio_e = st.text_input("Domicilio", ab[6])
                casilla_e_e = st.text_input("Casilla electrónica", ab[7])
                casilla_j_e = st.text_input("Casilla judicial", ab[8])
                if st.form_submit_button("Guardar cambios"):
                    c.execute("""UPDATE abogados SET nombre=?,dni=?,celular=?,correo=?,colegiatura=?,domicilio=?,casilla_electronica=?,casilla_judicial=?
                                 WHERE id=?""",
                              (nombre_e,dni_e,celular_e,correo_e,colegiatura_e,domicilio_e,casilla_e_e,casilla_j_e,ab[0]))
                    conn.commit()
                    st.success("Abogado actualizado")
                    st.experimental_rerun()
        if col2.button("Eliminar", key=f"del_ab_{ab[0]}"):
            c.execute("DELETE FROM abogados WHERE id=?",(ab[0],))
            conn.commit()
            st.success("Abogado eliminado")
            st.experimental_rerun()
# ============================
# CASOS
# ============================
if menu=="Casos":
    st.title("Gestión de Casos")
    clientes_data = obtener_clientes()
    abogados_data = obtener_abogados()
    if not clientes_data or not abogados_data:
        st.warning("Debe haber al menos un cliente y un abogado registrados.")
    else:
        with st.form("form_caso"):
            expediente = st.text_input("Número de expediente")
            año = st.text_input("Año")
            cliente_sel = st.selectbox("Cliente", [(c[0],c[1]) for c in clientes_data], format_func=lambda x: x[1])
            abogado_sel = st.selectbox("Abogado", [(a[0],a[1]) for a in abogados_data], format_func=lambda x: x[1])
            materia = st.text_input("Materia")
            estado = st.text_input("Estado")
            pretension = st.text_input("Pretensión")
            monto_honorarios = st.number_input("Monto de Honorarios",0.0)
            monto_base = st.number_input("Monto Base (para Cuota Litis)",0.0)
            porcentaje_litis = st.number_input("Porcentaje Cuota Litis (%)",0.0)
            observaciones = st.text_area("Observaciones")
            if st.form_submit_button("Guardar Caso"):
                c.execute("""INSERT INTO casos(expediente,año,cliente_id,abogado_id,materia,estado,pretension,
                             monto_honorarios,monto_base,porcentaje_litis,observaciones)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                          (expediente,año,cliente_sel[0],abogado_sel[0],materia,estado,pretension,
                           monto_honorarios,monto_base,porcentaje_litis,observaciones))
                conn.commit()
                st.success("Caso registrado")
                st.experimental_rerun()

    st.subheader("Casos Registrados")
    casos_data = obtener_casos()
    for caso in casos_data:
        c.execute("SELECT nombre FROM clientes WHERE id=?",(caso[3],))
        cliente_nombre = c.fetchone()[0]
        c.execute("SELECT nombre FROM abogados WHERE id=?",(caso[4],))
        abogado_nombre = c.fetchone()[0]
        st.write(f"**Expediente:** {caso[1]} | Año: {caso[2]} | Cliente: {cliente_nombre} | Abogado: {abogado_nombre}")
        st.write(f"Monto Honorarios: S/ {caso[8]:,.2f} | Cuota Litis: {caso[10]}% | Pretensión: {caso[7]}")
        col1,col2 = st.columns(2)
        if col1.button("Editar", key=f"edit_caso_{caso[0]}"):
            with st.form(f"edit_caso_form_{caso[0]}"):
                expediente_e = st.text_input("Expediente", caso[1])
                año_e = st.text_input("Año", caso[2])
                cliente_e = st.selectbox("Cliente", [(c[0],c[1]) for c in clientes_data], index=[i for i,v in enumerate(clientes_data) if v[0]==caso[3]][0], format_func=lambda x: x[1])
                abogado_e = st.selectbox("Abogado", [(a[0],a[1]) for a in abogados_data], index=[i for i,v in enumerate(abogados_data) if v[0]==caso[4]][0], format_func=lambda x: x[1])
                materia_e = st.text_input("Materia", caso[5])
                estado_e = st.text_input("Estado", caso[6])
                pretension_e = st.text_input("Pretensión", caso[7])
                monto_honorarios_e = st.number_input("Monto de Honorarios", caso[8])
                monto_base_e = st.number_input("Monto Base", caso[9])
                porcentaje_litis_e = st.number_input("Porcentaje Cuota Litis", caso[10])
                observaciones_e = st.text_area("Observaciones", caso[11])
                if st.form_submit_button("Guardar Cambios"):
                    c.execute("""UPDATE casos SET expediente=?,año=?,cliente_id=?,abogado_id=?,materia=?,estado=?,pretension=?,
                                 monto_honorarios=?,monto_base=?,porcentaje_litis=?,observaciones=? WHERE id=?""",
                              (expediente_e,año_e,cliente_e[0],abogado_e[0],materia_e,estado_e,pretension_e,
                               monto_honorarios_e,monto_base_e,porcentaje_litis_e,observaciones_e,caso[0]))
                    conn.commit()
                    st.success("Caso actualizado")
                    st.experimental_rerun()
        if col2.button("Eliminar", key=f"del_caso_{caso[0]}"):
            c.execute("DELETE FROM casos WHERE id=?",(caso[0],))
            conn.commit()
            st.success("Caso eliminado")
            st.experimental_rerun()

# ============================
# PAGOS
# ============================
if menu=="Pagos":
    st.title("Pagos de Honorarios")
    casos_data = obtener_casos()
    if casos_data:
        with st.form("form_pago"):
            caso_sel = st.selectbox("Caso", [(c[0],c[1]) for c in casos_data], format_func=lambda x: x[1])
            fecha = st.date_input("Fecha de Pago", date.today())
            monto = st.number_input("Monto Pagado",0.0)
            observaciones = st.text_area("Observaciones")
            if st.form_submit_button("Registrar Pago"):
                c.execute("INSERT INTO pagos(caso_id,fecha,monto,observaciones) VALUES (?,?,?,?)",
                          (caso_sel[0],fecha.isoformat(),monto,observaciones))
                conn.commit()
                st.success("Pago registrado")
                st.experimental_rerun()
        st.subheader("Pagos Registrados")
        pagos_data = obtener_pagos()
        for pago in pagos_data:
            c.execute("SELECT expediente FROM casos WHERE id=?",(pago[1],))
            expediente = c.fetchone()[0]
            st.write(f"Caso: {expediente} | Fecha: {pago[2]} | Monto: S/ {pago[3]:,.2f} | Observaciones: {pago[4]}")
            if st.button("Eliminar", key=f"del_pago_{pago[0]}"):
                c.execute("DELETE FROM pagos WHERE id=?",(pago[0],))
                conn.commit()
                st.success("Pago eliminado")
                st.experimental_rerun()

# ============================
# CUOTA LITIS
# ============================
if menu=="Cuota Litis":
    st.title("Cuota Litis por Caso")
    casos_data = obtener_casos()
    if casos_data:
        for caso in casos_data:
            cuota = caso[9]*(caso[10]/100)
            c.execute("SELECT nombre FROM clientes WHERE id=?",(caso[3],))
            cliente_nombre = c.fetchone()[0]
            st.write(f"Expediente: {caso[1]} | Cliente: {cliente_nombre} | Monto Base: S/ {caso[9]:,.2f} | Cuota Litis: S/ {cuota:,.2f}")
# ============================
# PAGOS CUOTA LITIS
# ============================
if menu=="Pagos Cuota Litis":
    st.title("Pagos de Cuota Litis")
    casos_data = obtener_casos()
    if casos_data:
        with st.form("form_pago_litis"):
            caso_sel = st.selectbox("Caso", [(c[0],c[1]) for c in casos_data], format_func=lambda x: x[1])
            fecha = st.date_input("Fecha de Pago", date.today())
            monto = st.number_input("Monto Pagado",0.0)
            observaciones = st.text_area("Observaciones")
            if st.form_submit_button("Registrar Pago Cuota Litis"):
                c.execute("INSERT INTO pagos_litis(caso_id,fecha,monto,observaciones) VALUES (?,?,?,?)",
                          (caso_sel[0],fecha.isoformat(),monto,observaciones))
                conn.commit()
                st.success("Pago de Cuota Litis registrado")
                st.experimental_rerun()
        st.subheader("Pagos Cuota Litis Registrados")
        pagos_litis_data = obtener_pagos_litis()
        for pago in pagos_litis_data:
            c.execute("SELECT expediente FROM casos WHERE id=?",(pago[1],))
            expediente = c.fetchone()[0]
            st.write(f"Caso: {expediente} | Fecha: {pago[2]} | Monto: S/ {pago[3]:,.2f} | Observaciones: {pago[4]}")
            if st.button("Eliminar", key=f"del_pago_litis_{pago[0]}"):
                c.execute("DELETE FROM pagos_litis WHERE id=?",(pago[0],))
                conn.commit()
                st.success("Pago eliminado")
                st.experimental_rerun()

# ============================
# CRONOGRAMA DE PAGOS
# ============================
if menu=="Cronograma":
    st.title("Cronograma de Pagos por Caso")
    casos_data = obtener_casos()
    if casos_data:
        with st.form("form_cronograma"):
            caso_sel = st.selectbox("Caso", [(c[0],c[1]) for c in casos_data], format_func=lambda x: x[1])
            fecha_prog = st.date_input("Fecha programada")
            monto_prog = st.number_input("Monto programado",0.0)
            observaciones = st.text_area("Observaciones")
            if st.form_submit_button("Registrar Cronograma"):
                c.execute("INSERT INTO cronograma(caso_id,fecha_prog,monto,observaciones) VALUES (?,?,?,?)",
                          (caso_sel[0],fecha_prog.isoformat(),monto_prog,observaciones))
                conn.commit()
                st.success("Pago programado registrado")
                st.experimental_rerun()
        st.subheader("Cronograma Registrado")
        c.execute("SELECT cronograma.id,casos.expediente,clientes.nombre,fecha_prog,monto,cronograma.observaciones FROM cronograma JOIN casos ON cronograma.caso_id=casos.id JOIN clientes ON casos.cliente_id=clientes.id")
        rows = c.fetchall()
        for r in rows:
            st.write(f"Caso: {r[1]} | Cliente: {r[2]} | Fecha: {r[3]} | Monto: S/ {r[4]:,.2f} | Observaciones: {r[5]}")
            if st.button("Eliminar", key=f"del_cronograma_{r[0]}"):
                c.execute("DELETE FROM cronograma WHERE id=?",(r[0],))
                conn.commit()
                st.success("Registro eliminado")
                st.experimental_rerun()

# ============================
# PENDIENTES DE COBRO
# ============================
if menu=="Pendientes":
    st.title("Pendientes de Cobro")
    casos_data = obtener_casos()
    for caso in casos_data:
        c.execute("SELECT nombre FROM clientes WHERE id=?",(caso[3],))
        cliente_nombre = c.fetchone()[0]
        # Pagos honorarios
        c.execute("SELECT SUM(monto) FROM pagos WHERE caso_id=?",(caso[0],))
        pagado = c.fetchone()[0] or 0
        saldo_honorarios = caso[8] - pagado
        # Pagos cuota litis
        cuota = caso[9]*(caso[10]/100)
        c.execute("SELECT SUM(monto) FROM pagos_litis WHERE caso_id=?",(caso[0],))
        pagado_litis = c.fetchone()[0] or 0
        saldo_litis = cuota - pagado_litis
        if saldo_honorarios>0 or saldo_litis>0:
            st.write(f"Expediente: {caso[1]} | Cliente: {cliente_nombre}")
            st.write(f"Saldo Honorarios: S/ {saldo_honorarios:,.2f} | Saldo Cuota Litis: S/ {saldo_litis:,.2f}")

# ============================
# RESUMEN FINANCIERO
# ============================
if menu=="Resumen Financiero":
    st.title("Resumen Financiero - Estudio Jurídico Roncal Liñán y Asociados")
    casos_data = obtener_casos()
    tabla_honorarios = []
    tabla_litis = []
    for caso in casos_data:
        c.execute("SELECT nombre FROM clientes WHERE id=?",(caso[3],))
        cliente_nombre = c.fetchone()[0]
        # Honorarios
        c.execute("SELECT SUM(monto) FROM pagos WHERE caso_id=?",(caso[0],))
        pagado = c.fetchone()[0] or 0
        saldo_honorarios = caso[8] - pagado
        tabla_honorarios.append([caso[1],cliente_nombre,caso[2],caso[8],pagado,saldo_honorarios])
        # Cuota Litis
        cuota = caso[9]*(caso[10]/100)
        c.execute("SELECT SUM(monto) FROM pagos_litis WHERE caso_id=?",(caso[0],))
        pagado_litis = c.fetchone()[0] or 0
        saldo_litis = cuota - pagado_litis
        tabla_litis.append([caso[1],cliente_nombre,caso[9],caso[10],cuota,pagado_litis,saldo_litis])
    st.subheader("Honorarios")
    st.dataframe(pd.DataFrame(tabla_honorarios,columns=["Expediente","Cliente","Año","Monto Pactado","Pagado","Saldo"]))
    st.subheader("Cuota Litis")
    st.dataframe(pd.DataFrame(tabla_litis,columns=["Expediente","Cliente","Monto Base","Porcentaje","Cuota Calculada","Pagado","Saldo"]))

# ============================
# USUARIOS / ABOGADOS
# ============================
if menu=="Usuarios":
    st.title("Gestión de Abogados / Usuarios")
    with st.form("form_abogado"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        correo = st.text_input("Correo")
        celular = st.text_input("Celular")
        colegiatura = st.text_input("N° Colegiatura")
        direccion_proc = st.text_input("Domicilio Procesal")
        casilla_e = st.text_input("Casilla Electrónica")
        casilla_j = st.text_input("Casilla Judicial")
        if st.form_submit_button("Registrar Abogado"):
            c.execute("""INSERT INTO abogados(nombre,dni,correo,celular,colegiatura,direccion_proc,casilla_e,casilla_j)
                         VALUES (?,?,?,?,?,?,?,?)""",(nombre,dni,correo,celular,colegiatura,direccion_proc,casilla_e,casilla_j))
            conn.commit()
            st.success("Abogado registrado")
            st.experimental_rerun()
    st.subheader("Abogados Registrados")
    abogados_data = obtener_abogados()
    for ab in abogados_data:
        st.write(f"{ab[1]} | DNI: {ab[2]} | Correo: {ab[3]} | Celular: {ab[4]}")
        col1,col2 = st.columns(2)
        if col1.button("Editar", key=f"edit_ab_{ab[0]}"):
            with st.form(f"edit_ab_form_{ab[0]}"):
                nombre_e = st.text_input("Nombre", ab[1])
                dni_e = st.text_input("DNI", ab[2])
                correo_e = st.text_input("Correo", ab[3])
                celular_e = st.text_input("Celular", ab[4])
                colegiatura_e = st.text_input("N° Colegiatura", ab[5])
                direccion_proc_e = st.text_input("Domicilio Procesal", ab[6])
                casilla_e_e = st.text_input("Casilla Electrónica", ab[7])
                casilla_j_e = st.text_input("Casilla Judicial", ab[8])
                if st.form_submit_button("Guardar Cambios"):
                    c.execute("""UPDATE abogados SET nombre=?,dni=?,correo=?,celular=?,colegiatura=?,direccion_proc=?,casilla_e=?,casilla_j=? WHERE id=?""",
                              (nombre_e,dni_e,correo_e,celular_e,colegiatura_e,direccion_proc_e,casilla_e_e,casilla_j_e,ab[0]))
                    conn.commit()
                    st.success("Abogado actualizado")
                    st.experimental_rerun()
        if col2.button("Eliminar", key=f"del_ab_{ab[0]}"):
            c.execute("DELETE FROM abogados WHERE id=?",(ab[0],))
            conn.commit()
            st.success("Abogado eliminado")
            st.experimental_rerun()
