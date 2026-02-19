import streamlit as st
import pandas as pd
import os
import hashlib
import shutil
from datetime import date, datetime

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================
APP_NAME = "Estudio Jurídico Roncal Liñan y Asociados"
st.set_page_config(page_title=f"⚖️ {APP_NAME}", layout="wide")

DATA_DIR = "."
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
GENERADOS_DIR = os.path.join(DATA_DIR, "generados")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERADOS_DIR, exist_ok=True)

# ==========================================================
# ARCHIVOS
# ==========================================================
FILES = {
    "usuarios": os.path.join(DATA_DIR, "usuarios.csv"),
    "clientes": os.path.join(DATA_DIR, "clientes.csv"),
    "abogados": os.path.join(DATA_DIR, "abogados.csv"),
    "casos": os.path.join(DATA_DIR, "casos.csv"),
    "honorarios": os.path.join(DATA_DIR, "honorarios.csv"),
    "pagos_honorarios": os.path.join(DATA_DIR, "pagos_honorarios.csv"),
    "cuota_litis": os.path.join(DATA_DIR, "cuota_litis.csv"),
    "pagos_litis": os.path.join(DATA_DIR, "pagos_litis.csv"),
    "cuotas": os.path.join(DATA_DIR, "cuotas.csv"),
    "actuaciones": os.path.join(DATA_DIR, "actuaciones.csv"),
    "documentos": os.path.join(DATA_DIR, "documentos.csv"),
    "plantillas": os.path.join(DATA_DIR, "plantillas_contratos.csv"),
}

# ==========================================================
# ESQUEMAS (COLUMNAS EXACTAS)
# ==========================================================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","Activo","Creado"],
    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones","EstadoCaso","FechaInicio"],

    # Configuración / acuerdos
    "honorarios": ["ID","Caso","Monto Pactado","Notas"],
    "cuota_litis": ["ID","Caso","Monto Base","Porcentaje","Notas"],

    # Pagos
    "pagos_honorarios": ["ID","Caso","FechaPago","Monto","Observacion"],
    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],

    # Cronograma
    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"],

    # Seguimiento
    "actuaciones": ["ID","Caso","Fecha","TipoActuacion","Resumen","ProximaAccion","FechaProximaAccion","Notas"],

    # Documentos
    "documentos": ["ID","Caso","Tipo","NombreArchivo","Ruta","Fecha","Notas"],

    # Plantillas
    "plantillas": ["ID","Nombre","Contenido","Notas","Creado"],
}

# ==========================================================
# UTILIDADES
# ==========================================================
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def brand_header():
    st.markdown(
        f"""
        <div style="padding:10px 0 0 0;">
            <h1 style="margin-bottom:0;">⚖️ {APP_NAME}</h1>
            <p style="margin-top:2px;color:#666;">Sistema de gestión de clientes, casos, pagos, cuotas, documentos y contratos</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def drop_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.str.contains(r"^Unnamed", case=False, na=False)]

def backup_file(path: str):
    if not os.path.exists(path):
        return
    base = os.path.basename(path)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"{base}.{stamp}.bak")
    try:
        shutil.copy2(path, dst)
    except Exception:
        pass

def normalize_key(x) -> str:
    # quita espacios invisibles que causan "deudas fantasma"
    if pd.isna(x):
        return ""
    return str(x).strip()

def safe_float_series(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def money(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def to_date_safe(x):
    if pd.isna(x) or str(x).strip() == "":
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def ensure_csv(key: str):
    path = FILES[key]
    cols = SCHEMAS[key]

    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    try:
        if os.path.getsize(path) == 0:
            pd.DataFrame(columns=cols).to_csv(path, index=False)
            return
    except OSError:
        pass

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    df = drop_unnamed(df)

    # agregar columnas faltantes
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df = df.reindex(columns=cols)
    df.to_csv(path, index=False)

def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    try:
        df = pd.read_csv(FILES[key])
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=SCHEMAS[key])
    df = drop_unnamed(df)
    df = df.reindex(columns=SCHEMAS[key])
    return df

def save_df(key: str, df: pd.DataFrame):
    path = FILES[key]
    backup_file(path)
    df = drop_unnamed(df)
    df = df.reindex(columns=SCHEMAS[key])
    df.to_csv(path, index=False)

def next_id(df: pd.DataFrame, col="ID") -> int:
    if df.empty:
        return 1
    try:
        m = pd.to_numeric(df[col], errors="coerce").max()
        return int(m) + 1 if pd.notna(m) else len(df) + 1
    except Exception:
        return len(df) + 1

def add_row(df: pd.DataFrame, row_dict: dict, schema_key: str) -> pd.DataFrame:
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df2 = df2.reindex(columns=SCHEMAS[schema_key])
    return df2

def require_admin():
    if st.session_state.rol != "admin":
        st.error("❌ Solo ADMIN puede acceder a esta opción.")
        st.stop()

# ==========================================================
# INICIALIZAR CSVs
# ==========================================================
for k in FILES:
    ensure_csv(k)

# ==========================================================
# USUARIOS: asegurar admin (sin pisar si ya existe)
# ==========================================================
usuarios_df = load_df("usuarios")
if usuarios_df[usuarios_df["Usuario"].astype(str) == "admin"].empty:
    usuarios_df = add_row(usuarios_df, {
        "Usuario": "admin",
        "PasswordHash": sha256("estudio123"),
        "Rol": "admin",
        "Activo": "1",
        "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, "usuarios")
    save_df("usuarios", usuarios_df)

# ==========================================================
# LOGIN
# ==========================================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None

def login_ui():
    brand_header()
    st.subheader("Ingreso al Sistema")

    u = st.text_input("Usuario", value="admin")
    p = st.text_input("Contraseña", type="password", value="estudio123")

    if st.button("Ingresar"):
        users = load_df("usuarios")
        users = users[users["Activo"].astype(str) == "1"].copy()
        row = users[users["Usuario"].astype(str) == str(u)].copy()
        if row.empty or row.iloc[0]["PasswordHash"] != sha256(p):
            st.error("Credenciales incorrectas")
            st.stop()
        st.session_state.usuario = u
        st.session_state.rol = row.iloc[0]["Rol"]
        st.rerun()

if st.session_state.usuario is None:
    login_ui()
    st.stop()

# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.write(f"👤 Usuario: {st.session_state.usuario} ({st.session_state.rol})")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.rerun()

if st.sidebar.button("🛠️ Reparar sistema (CSVs)"):
    for k in FILES:
        ensure_csv(k)
    st.success("✅ Sistema reparado")
    st.rerun()

# ==========================================================
# CARGAR DATA
# ==========================================================
clientes = load_df("clientes")
abogados = load_df("abogados")
casos = load_df("casos")
honorarios = load_df("honorarios")
pagos_honorarios = load_df("pagos_honorarios")
cuota_litis = load_df("cuota_litis")
pagos_litis = load_df("pagos_litis")
cuotas = load_df("cuotas")
actuaciones = load_df("actuaciones")
documentos = load_df("documentos")
plantillas = load_df("plantillas")

# Normalizar claves (evita deuda/pagos invisibles por espacios)
casos["Expediente"] = casos["Expediente"].apply(normalize_key)

for df in [honorarios, pagos_honorarios, cuota_litis, pagos_litis, cuotas, actuaciones, documentos]:
    if "Caso" in df.columns:
        df["Caso"] = df["Caso"].apply(normalize_key)

# ==========================================================
# FINANZAS
# ==========================================================
def resumen_financiero_df():
    if casos.empty:
        return pd.DataFrame(columns=[
            "Expediente","Cliente","Materia",
            "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
            "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
        ])

    resumen = []
    for _, c in casos.iterrows():
        exp = normalize_key(c["Expediente"])
        cliente = c["Cliente"]
        materia = c["Materia"]

        pactado = safe_float_series(honorarios[honorarios["Caso"] == exp]["Monto Pactado"]).sum()
        pagado_h = safe_float_series(pagos_honorarios[pagos_honorarios["Caso"] == exp]["Monto"]).sum()

        base = safe_float_series(cuota_litis[cuota_litis["Caso"] == exp]["Monto Base"]).sum()
        porc_series = safe_float_series(cuota_litis[cuota_litis["Caso"] == exp]["Porcentaje"])
        porcentaje = float(porc_series.iloc[-1]) if len(porc_series) else 0.0
        calculada = float(base) * float(porcentaje) / 100.0

        pagado_l = safe_float_series(pagos_litis[pagos_litis["Caso"] == exp]["Monto"]).sum()

        resumen.append([
            exp, cliente, materia,
            float(pactado), float(pagado_h), float(pactado - pagado_h),
            float(calculada), float(pagado_l), float(calculada - pagado_l)
        ])

    return pd.DataFrame(resumen, columns=[
        "Expediente","Cliente","Materia",
        "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
        "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
    ])

def allocate_payments_oldest_first(cuotas_tipo_df: pd.DataFrame, pagos_tipo_df: pd.DataFrame):
    today = date.today()
    if cuotas_tipo_df.empty:
        return cuotas_tipo_df

    df = cuotas_tipo_df.copy()
    df["Monto"] = safe_float_series(df["Monto"])
    df["FechaVenc_dt"] = df["FechaVenc"].apply(to_date_safe)
    df["_sort_date"] = df["FechaVenc_dt"].apply(lambda d: d if d is not None else date(2100,1,1))
    df.sort_values(["Caso","_sort_date","NroCuota"], inplace=True)

    pagos = pagos_tipo_df.copy()
    pagos["Monto"] = safe_float_series(pagos["Monto"])
    pagado_por_caso = pagos.groupby("Caso")["Monto"].sum().to_dict()
    remaining = {k: float(v) for k, v in pagado_por_caso.items()}

    pagado_asignado, saldo_cuota, estado, dias = [], [], [], []
    for _, r in df.iterrows():
        caso = r["Caso"]
        monto = float(r["Monto"])
        venc = r["FechaVenc_dt"]

        rem = remaining.get(caso, 0.0)
        asignado = min(rem, monto) if monto > 0 else 0.0
        remaining[caso] = rem - asignado
        saldo = monto - asignado

        if monto == 0:
            est = "Sin monto"
        elif saldo <= 0.00001:
            est = "Pagada"
        elif asignado > 0:
            est = "Parcial"
        else:
            est = "Pendiente"

        dv = None if venc is None else (venc - today).days

        pagado_asignado.append(asignado)
        saldo_cuota.append(saldo)
        estado.append(est)
        dias.append(dv)

    df["PagadoAsignado"] = pagado_asignado
    df["SaldoCuota"] = saldo_cuota
    df["Estado"] = estado
    df["DiasParaVencimiento"] = dias
    df.drop(columns=["_sort_date"], inplace=True, errors="ignore")
    return df

def cuotas_status_all():
    if cuotas.empty:
        return pd.DataFrame()
    q_h = cuotas[cuotas["Tipo"] == "Honorarios"].copy()
    q_l = cuotas[cuotas["Tipo"] == "CuotaLitis"].copy()
    st_h = allocate_payments_oldest_first(q_h, pagos_honorarios)
    st_l = allocate_payments_oldest_first(q_l, pagos_litis)
    if st_h.empty and st_l.empty:
        return pd.DataFrame()
    return pd.concat([st_h, st_l], ignore_index=True)

def cuotas_pendientes(df_status: pd.DataFrame):
    if df_status.empty:
        return df_status
    return df_status[safe_float_series(df_status["SaldoCuota"]) > 0].copy()

def saldo_por_cliente():
    df = resumen_financiero_df()
    if df.empty:
        return pd.DataFrame(columns=["Cliente","SaldoHonorarios","SaldoCuotaLitis","SaldoTotal"])
    g = df.groupby("Cliente").agg({
        "Honorario Pendiente":"sum",
        "Saldo Litis":"sum"
    }).reset_index()
    g.rename(columns={"Honorario Pendiente":"SaldoHonorarios","Saldo Litis":"SaldoCuotaLitis"}, inplace=True)
    g["SaldoTotal"] = g["SaldoHonorarios"] + g["SaldoCuotaLitis"]
    g.sort_values("SaldoTotal", ascending=False, inplace=True)
    return g

# ==========================================================
# MENÚ COMPLETO (sin recortes)
# ==========================================================
menu = st.sidebar.selectbox("📌 Menú", [
    "Dashboard",
    "Búsqueda",
    "Clientes",
    "Abogados",
    "Casos",
    "Honorarios",
    "Pagos Honorarios",
    "Cuota Litis",
    "Pagos Cuota Litis",
    "Cronograma de Cuotas",
    "Actuaciones",
    "Documentos",
    "Plantillas de Contrato",
    "Generar Contrato",
    "Reportes",
    "Usuarios",
    "Resumen Financiero",
    "Auditoría (deudas/pagos huérfanos)"
])

brand_header()

# ==========================================================
# DASHBOARD
# ==========================================================
if menu == "Dashboard":
    st.subheader("📊 Dashboard General")

    df_res = resumen_financiero_df()
    df_status = cuotas_status_all()
    df_pend = cuotas_pendientes(df_status)

    total_pactado = df_res["Honorario Pactado"].sum() if not df_res.empty else 0
    total_pagado_h = df_res["Honorario Pagado"].sum() if not df_res.empty else 0
    total_pend_h = df_res["Honorario Pendiente"].sum() if not df_res.empty else 0

    total_litis = df_res["Cuota Litis Calculada"].sum() if not df_res.empty else 0
    total_pagado_l = df_res["Pagado Litis"].sum() if not df_res.empty else 0
    total_pend_l = df_res["Saldo Litis"].sum() if not df_res.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Honorarios pactados (S/)", f"{total_pactado:,.2f}")
    c2.metric("Honorarios pagados (S/)", f"{total_pagado_h:,.2f}")
    c3.metric("Honorarios pendientes (S/)", f"{total_pend_h:,.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Cuota litis calculada (S/)", f"{total_litis:,.2f}")
    c5.metric("Cuota litis pagada (S/)", f"{total_pagado_l:,.2f}")
    c6.metric("Cuota litis pendiente (S/)", f"{total_pend_l:,.2f}")

    st.divider()
    st.markdown("### 👤 Saldos por Cliente (Top)")
    st.dataframe(saldo_por_cliente().head(20), use_container_width=True)

    st.divider()
    st.markdown("### 📅 Cuotas pendientes (Top)")
    if df_pend.empty:
        st.info("No hay cuotas pendientes registradas.")
    else:
        st.dataframe(df_pend.sort_values("SaldoCuota", ascending=False).head(30), use_container_width=True)

# ==========================================================
# BÚSQUEDA GLOBAL
# ==========================================================
if menu == "Búsqueda":
    st.subheader("🔎 Búsqueda (DNI / Cliente / Expediente)")
    q = st.text_input("Buscar").strip().lower()
    if q:
        st.markdown("#### Clientes")
        st.dataframe(
            clientes[
                clientes["DNI"].astype(str).str.lower().str.contains(q, na=False) |
                clientes["Nombre"].astype(str).str.lower().str.contains(q, na=False)
            ],
            use_container_width=True
        )
        st.markdown("#### Casos")
        st.dataframe(
            casos[
                casos["Expediente"].astype(str).str.lower().str.contains(q, na=False) |
                casos["Cliente"].astype(str).str.lower().str.contains(q, na=False) |
                casos["Materia"].astype(str).str.lower().str.contains(q, na=False)
            ],
            use_container_width=True
        )
    else:
        st.info("Escribe algo para buscar.")

# ==========================================================
# CLIENTES (CRUD)
# ==========================================================
if menu == "Clientes":
    st.subheader("👥 Clientes")
    accion = st.radio("Acción", ["Nuevo","Editar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        with st.form("nuevo_cliente"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI")
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            direccion = st.text_input("Dirección")
            obs = st.text_area("Observaciones")
            submit = st.form_submit_button("Guardar")
            if submit:
                new_id = next_id(clientes)
                clientes = add_row(clientes, {
                    "ID": new_id,"Nombre": nombre,"DNI": dni,"Celular": celular,
                    "Correo": correo,"Direccion": direccion,"Observaciones": obs
                }, "clientes")
                save_df("clientes", clientes)
                st.success("✅ Cliente registrado")
                st.rerun()

    if accion == "Editar" and not clientes.empty:
        sel = st.selectbox("Cliente ID", clientes["ID"].tolist())
        fila = clientes[clientes["ID"] == sel].iloc[0]
        with st.form("edit_cliente"):
            nombre = st.text_input("Nombre", value=str(fila["Nombre"]))
            dni = st.text_input("DNI", value=str(fila["DNI"]))
            celular = st.text_input("Celular", value=str(fila["Celular"]))
            correo = st.text_input("Correo", value=str(fila["Correo"]))
            direccion = st.text_input("Dirección", value=str(fila["Direccion"]))
            obs = st.text_area("Observaciones", value=str(fila["Observaciones"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = clientes.index[clientes["ID"] == sel][0]
                clientes.loc[idx, :] = [sel, nombre, dni, celular, correo, direccion, obs]
                save_df("clientes", clientes)
                st.success("✅ Actualizado")
                st.rerun()

    if accion == "Eliminar" and not clientes.empty:
        sel = st.selectbox("Cliente ID a eliminar", clientes["ID"].tolist())
        st.warning("⚠️ Eliminar cliente no elimina casos automáticamente.")
        if st.button("Eliminar cliente"):
            clientes = clientes[clientes["ID"] != sel].copy()
            save_df("clientes", clientes)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(clientes, use_container_width=True)

# ==========================================================
# ABOGADOS (CRUD)
# ==========================================================
if menu == "Abogados":
    st.subheader("👨‍⚖️ Abogados")
    accion = st.radio("Acción", ["Nuevo","Editar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        with st.form("nuevo_abogado"):
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI")
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            coleg = st.text_input("Colegiatura")
            dom = st.text_input("Domicilio Procesal")
            cas_e = st.text_input("Casilla Electrónica")
            cas_j = st.text_input("Casilla Judicial")
            submit = st.form_submit_button("Guardar")
            if submit:
                new_id = next_id(abogados)
                abogados = add_row(abogados, {
                    "ID": new_id,"Nombre": nombre,"DNI": dni,"Celular": celular,"Correo": correo,
                    "Colegiatura": coleg,"Domicilio Procesal": dom,"Casilla Electronica": cas_e,"Casilla Judicial": cas_j
                }, "abogados")
                save_df("abogados", abogados)
                st.success("✅ Abogado registrado")
                st.rerun()

    if accion == "Editar" and not abogados.empty:
        sel = st.selectbox("Abogado ID", abogados["ID"].tolist())
        fila = abogados[abogados["ID"] == sel].iloc[0]
        with st.form("edit_abogado"):
            nombre = st.text_input("Nombre", value=str(fila["Nombre"]))
            dni = st.text_input("DNI", value=str(fila["DNI"]))
            celular = st.text_input("Celular", value=str(fila["Celular"]))
            correo = st.text_input("Correo", value=str(fila["Correo"]))
            coleg = st.text_input("Colegiatura", value=str(fila["Colegiatura"]))
            dom = st.text_input("Domicilio Procesal", value=str(fila["Domicilio Procesal"]))
            cas_e = st.text_input("Casilla Electrónica", value=str(fila["Casilla Electronica"]))
            cas_j = st.text_input("Casilla Judicial", value=str(fila["Casilla Judicial"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = abogados.index[abogados["ID"] == sel][0]
                abogados.loc[idx, :] = [sel, nombre, dni, celular, correo, coleg, dom, cas_e, cas_j]
                save_df("abogados", abogados)
                st.success("✅ Actualizado")
                st.rerun()

    if accion == "Eliminar" and not abogados.empty:
        sel = st.selectbox("Abogado ID a eliminar", abogados["ID"].tolist())
        if st.button("Eliminar abogado"):
            abogados = abogados[abogados["ID"] != sel].copy()
            save_df("abogados", abogados)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(abogados, use_container_width=True)

# ==========================================================
# CASOS (CRUD)
# ==========================================================
if menu == "Casos":
    st.subheader("📁 Casos")
    accion = st.radio("Acción", ["Nuevo","Editar","Eliminar"], horizontal=True)

    clientes_list = clientes["Nombre"].tolist() if not clientes.empty else []
    abogados_list = abogados["Nombre"].tolist() if not abogados.empty else [""]

    if accion == "Nuevo":
        with st.form("nuevo_caso"):
            cliente = st.selectbox("Cliente", clientes_list)
            abogado = st.selectbox("Abogado", abogados_list)
            expediente = st.text_input("Expediente")
            anio = st.text_input("Año")
            materia = st.text_input("Materia")
            pret = st.text_input("Pretensión")
            obs = st.text_area("Observaciones")
            estado = st.selectbox("Estado", ["Activo","En pausa","Cerrado","Archivado"])
            fecha_inicio = st.date_input("Fecha inicio", value=date.today())
            submit = st.form_submit_button("Guardar")
            if submit:
                new_id = next_id(casos)
                casos = add_row(casos, {
                    "ID": new_id,"Cliente": cliente,"Abogado": abogado,"Expediente": normalize_key(expediente),
                    "Año": anio,"Materia": materia,"Pretension": pret,"Observaciones": obs,
                    "EstadoCaso": estado,"FechaInicio": str(fecha_inicio)
                }, "casos")
                save_df("casos", casos)
                st.success("✅ Caso registrado")
                st.rerun()

    if accion == "Editar" and not casos.empty:
        sel = st.selectbox("Caso ID", casos["ID"].tolist())
        fila = casos[casos["ID"] == sel].iloc[0]
        with st.form("edit_caso"):
            cliente = st.text_input("Cliente", value=str(fila["Cliente"]))
            abogado = st.text_input("Abogado", value=str(fila["Abogado"]))
            expediente = st.text_input("Expediente", value=str(fila["Expediente"]))
            anio = st.text_input("Año", value=str(fila["Año"]))
            materia = st.text_input("Materia", value=str(fila["Materia"]))
            pret = st.text_input("Pretensión", value=str(fila["Pretension"]))
            obs = st.text_area("Observaciones", value=str(fila["Observaciones"]))
            estado = st.text_input("EstadoCaso", value=str(fila["EstadoCaso"]))
            fi = to_date_safe(fila["FechaInicio"]) or date.today()
            fecha_inicio = st.date_input("Fecha inicio", value=fi)
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = casos.index[casos["ID"] == sel][0]
                casos.loc[idx, :] = [sel, cliente, abogado, normalize_key(expediente), anio, materia, pret, obs, estado, str(fecha_inicio)]
                save_df("casos", casos)
                st.success("✅ Actualizado")
                st.rerun()

    if accion == "Eliminar" and not casos.empty:
        sel = st.selectbox("Caso ID a eliminar", casos["ID"].tolist())
        if st.button("Eliminar caso"):
            casos = casos[casos["ID"] != sel].copy()
            save_df("casos", casos)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(casos, use_container_width=True)

# ==========================================================
# HONORARIOS (CRUD por expediente)
# ==========================================================
if menu == "Honorarios":
    st.subheader("🧾 Honorarios pactados")
    st.dataframe(honorarios, use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")
    monto = st.number_input("Monto pactado", min_value=0.0, step=50.0)
    notas = st.text_input("Notas", value="")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar / Reemplazar honorario"):
            honorarios2 = honorarios[honorarios["Caso"] != normalize_key(exp)].copy()
            new_id = next_id(honorarios2)
            honorarios2 = add_row(honorarios2, {
                "ID": new_id, "Caso": normalize_key(exp), "Monto Pactado": float(monto), "Notas": notas
            }, "honorarios")
            honorarios = honorarios2
            save_df("honorarios", honorarios)
            st.success("✅ Guardado")
            st.rerun()

    with col2:
        if not honorarios.empty:
            sel = st.selectbox("Eliminar honorario (ID)", honorarios["ID"].tolist())
            if st.button("🗑️ Eliminar honorario"):
                honorarios = honorarios[honorarios["ID"] != sel].copy()
                save_df("honorarios", honorarios)
                st.success("✅ Eliminado")
                st.rerun()

# ==========================================================
# PAGOS HONORARIOS (SIEMPRE VISIBLE + EDITAR/BORRAR)
# ==========================================================
if menu == "Pagos Honorarios":
    st.subheader("💳 Pagos de Honorarios")

    st.markdown("#### Tabla completa (para que no se 'pierdan' pagos)")
    st.dataframe(pagos_honorarios.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente del pago", exp_list) if exp_list else st.text_input("Expediente del pago")
    fecha = st.date_input("Fecha pago", value=date.today())
    monto = st.number_input("Monto", min_value=0.0, step=50.0)
    obs = st.text_input("Observación", value="")

    if st.button("Registrar pago honorarios"):
        new_id = next_id(pagos_honorarios)
        pagos_honorarios = add_row(pagos_honorarios, {
            "ID": new_id, "Caso": normalize_key(exp), "FechaPago": str(fecha), "Monto": float(monto), "Observacion": obs
        }, "pagos_honorarios")
        save_df("pagos_honorarios", pagos_honorarios)
        st.success("✅ Pago registrado")
        st.rerun()

    st.divider()
    st.markdown("#### Editar / Borrar (por ID)")
    if not pagos_honorarios.empty:
        sel = st.selectbox("Pago ID", pagos_honorarios["ID"].tolist())
        fila = pagos_honorarios[pagos_honorarios["ID"] == sel].iloc[0]

        with st.form("edit_ph"):
            exp_e = st.text_input("Expediente", value=str(fila["Caso"]))
            fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
            obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = pagos_honorarios.index[pagos_honorarios["ID"] == sel][0]
                pagos_honorarios.loc[idx, :] = [sel, normalize_key(exp_e), fecha_e, float(monto_e), obs_e]
                save_df("pagos_honorarios", pagos_honorarios)
                st.success("✅ Actualizado")
                st.rerun()

        if st.button("🗑️ Borrar pago honorarios"):
            pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# CUOTA LITIS (CRUD por expediente)
# ==========================================================
if menu == "Cuota Litis":
    st.subheader("⚖️ Configuración Cuota Litis")
    st.dataframe(cuota_litis, use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")
    base = st.number_input("Monto base", min_value=0.0, step=100.0)
    porc = st.number_input("Porcentaje (%)", min_value=0.0, step=1.0)
    notas = st.text_input("Notas", value="")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar / Reemplazar cuota litis"):
            cuota2 = cuota_litis[cuota_litis["Caso"] != normalize_key(exp)].copy()
            new_id = next_id(cuota2)
            cuota2 = add_row(cuota2, {
                "ID": new_id, "Caso": normalize_key(exp), "Monto Base": float(base),
                "Porcentaje": float(porc), "Notas": notas
            }, "cuota_litis")
            cuota_litis = cuota2
            save_df("cuota_litis", cuota_litis)
            st.success("✅ Guardado")
            st.rerun()

    with col2:
        if not cuota_litis.empty:
            sel = st.selectbox("Eliminar cuota litis (ID)", cuota_litis["ID"].tolist())
            if st.button("🗑️ Eliminar cuota litis"):
                cuota_litis = cuota_litis[cuota_litis["ID"] != sel].copy()
                save_df("cuota_litis", cuota_litis)
                st.success("✅ Eliminado")
                st.rerun()

# ==========================================================
# PAGOS CUOTA LITIS (SIEMPRE VISIBLE + EDITAR/BORRAR)
# ==========================================================
if menu == "Pagos Cuota Litis":
    st.subheader("💳 Pagos de Cuota Litis")

    st.markdown("#### Tabla completa (para que no se 'pierdan' pagos)")
    st.dataframe(pagos_litis.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente del pago", exp_list) if exp_list else st.text_input("Expediente del pago")
    fecha = st.date_input("Fecha pago", value=date.today())
    monto = st.number_input("Monto", min_value=0.0, step=50.0)
    obs = st.text_input("Observación", value="")

    if st.button("Registrar pago cuota litis"):
        new_id = next_id(pagos_litis)
        pagos_litis = add_row(pagos_litis, {
            "ID": new_id, "Caso": normalize_key(exp), "FechaPago": str(fecha), "Monto": float(monto), "Observacion": obs
        }, "pagos_litis")
        save_df("pagos_litis", pagos_litis)
        st.success("✅ Pago registrado")
        st.rerun()

    st.divider()
    st.markdown("#### Editar / Borrar (por ID)")
    if not pagos_litis.empty:
        sel = st.selectbox("Pago ID", pagos_litis["ID"].tolist())
        fila = pagos_litis[pagos_litis["ID"] == sel].iloc[0]

        with st.form("edit_pl"):
            exp_e = st.text_input("Expediente", value=str(fila["Caso"]))
            fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
            obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = pagos_litis.index[pagos_litis["ID"] == sel][0]
                pagos_litis.loc[idx, :] = [sel, normalize_key(exp_e), fecha_e, float(monto_e), obs_e]
                save_df("pagos_litis", pagos_litis)
                st.success("✅ Actualizado")
                st.rerun()

        if st.button("🗑️ Borrar pago cuota litis"):
            pagos_litis = pagos_litis[pagos_litis["ID"] != sel].copy()
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# CRONOGRAMA DE CUOTAS
# ==========================================================
if menu == "Cronograma de Cuotas":
    st.subheader("📅 Cronograma de cuotas")
    st.dataframe(cuotas, use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")
    tipo = st.selectbox("Tipo", ["Honorarios","CuotaLitis"])
    venc = st.date_input("Vencimiento", value=date.today())
    monto = st.number_input("Monto cuota", min_value=0.0, step=50.0)
    notas = st.text_input("Notas", value="")

    subset = cuotas[(cuotas["Caso"] == normalize_key(exp)) & (cuotas["Tipo"] == tipo)].copy()
    nro = int(pd.to_numeric(subset["NroCuota"], errors="coerce").max()) + 1 if not subset.empty else 1

    if st.button("Guardar cuota"):
        new_id = next_id(cuotas)
        cuotas = add_row(cuotas, {
            "ID": new_id, "Caso": normalize_key(exp), "Tipo": tipo, "NroCuota": nro,
            "FechaVenc": str(venc), "Monto": float(monto), "Notas": notas
        }, "cuotas")
        save_df("cuotas", cuotas)
        st.success("✅ Cuota agregada")
        st.rerun()

    st.divider()
    st.markdown("#### Estado (pagos asignados a la cuota más antigua)")
    df_status = cuotas_status_all()
    st.dataframe(df_status, use_container_width=True)

    st.divider()
    st.markdown("#### Eliminar cuota (por ID)")
    if not cuotas.empty:
        sel = st.selectbox("Cuota ID", cuotas["ID"].tolist())
        if st.button("🗑️ Eliminar cuota"):
            cuotas = cuotas[cuotas["ID"] != sel].copy()
            save_df("cuotas", cuotas)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# ACTUACIONES
# ==========================================================
if menu == "Actuaciones":
    st.subheader("🧾 Actuaciones (timeline)")

    st.dataframe(actuaciones.sort_values("Fecha", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")

    with st.form("new_act"):
        fecha = st.date_input("Fecha", value=date.today())
        tipo = st.text_input("Tipo actuación")
        resumen = st.text_area("Resumen")
        prox = st.text_input("Próxima acción (opcional)")
        prox_fecha = st.text_input("Fecha próxima acción (YYYY-MM-DD opcional)")
        notas = st.text_input("Notas (opcional)")
        submit = st.form_submit_button("Guardar actuación")
        if submit:
            new_id = next_id(actuaciones)
            actuaciones = add_row(actuaciones, {
                "ID": new_id, "Caso": normalize_key(exp), "Fecha": str(fecha),
                "TipoActuacion": tipo, "Resumen": resumen,
                "ProximaAccion": prox, "FechaProximaAccion": prox_fecha, "Notas": notas
            }, "actuaciones")
            save_df("actuaciones", actuaciones)
            st.success("✅ Actuación registrada")
            st.rerun()

    st.divider()
    st.markdown("#### Eliminar actuación (por ID)")
    if not actuaciones.empty:
        sel = st.selectbox("Actuación ID", actuaciones["ID"].tolist())
        if st.button("🗑️ Eliminar actuación"):
            actuaciones = actuaciones[actuaciones["ID"] != sel].copy()
            save_df("actuaciones", actuaciones)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# DOCUMENTOS (simple: registra archivos, y borra registro)
# ==========================================================
if menu == "Documentos":
    st.subheader("📎 Documentos")
    st.dataframe(documentos.sort_values("Fecha", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")
    tipo = st.selectbox("Tipo", ["Contrato","Escrito","Resolución","Anexo","Otro"])
    notas = st.text_input("Notas", value="")
    up = st.file_uploader("Subir archivo")

    if st.button("Guardar documento"):
        if up is None:
            st.error("Sube un archivo primero.")
        else:
            exp_dir = os.path.join(UPLOADS_DIR, normalize_key(exp).replace("/", "_"))
            os.makedirs(exp_dir, exist_ok=True)
            filename = up.name
            path = os.path.join(exp_dir, filename)
            with open(path, "wb") as f:
                f.write(up.getbuffer())

            new_id = next_id(documentos)
            documentos = add_row(documentos, {
                "ID": new_id, "Caso": normalize_key(exp), "Tipo": tipo,
                "NombreArchivo": filename, "Ruta": path,
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Notas": notas
            }, "documentos")
            save_df("documentos", documentos)
            st.success("✅ Documento guardado")
            st.rerun()

    st.divider()
    st.markdown("#### Borrar documento (registro)")
    if not documentos.empty:
        sel = st.selectbox("Documento ID", documentos["ID"].tolist())
        if st.button("🗑️ Eliminar registro documento"):
            documentos = documentos[documentos["ID"] != sel].copy()
            save_df("documentos", documentos)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# PLANTILLAS (CRUD)
# ==========================================================
if menu == "Plantillas de Contrato":
    st.subheader("📝 Plantillas de contrato (modelos)")
    accion = st.radio("Acción", ["Nueva","Editar","Eliminar"], horizontal=True)

    st.info("Placeholders sugeridos: {{CLIENTE_NOMBRE}}, {{CLIENTE_DNI}}, {{EXPEDIENTE}}, {{MATERIA}}, {{MONTO_PACTADO}}, {{PORCENTAJE_LITIS}}, {{FECHA_HOY}}")

    if accion == "Nueva":
        with st.form("new_tpl"):
            nombre = st.text_input("Nombre plantilla")
            contenido = st.text_area("Contenido", height=300)
            notas = st.text_input("Notas")
            submit = st.form_submit_button("Guardar plantilla")
            if submit:
                new_id = next_id(plantillas)
                plantillas = add_row(plantillas, {
                    "ID": new_id, "Nombre": nombre, "Contenido": contenido,
                    "Notas": notas, "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, "plantillas")
                save_df("plantillas", plantillas)
                st.success("✅ Guardada")
                st.rerun()

    if accion == "Editar" and not plantillas.empty:
        sel = st.selectbox("Plantilla ID", plantillas["ID"].tolist())
        fila = plantillas[plantillas["ID"] == sel].iloc[0]
        with st.form("edit_tpl"):
            nombre = st.text_input("Nombre", value=str(fila["Nombre"]))
            contenido = st.text_area("Contenido", value=str(fila["Contenido"]), height=300)
            notas = st.text_input("Notas", value=str(fila["Notas"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = plantillas.index[plantillas["ID"] == sel][0]
                plantillas.loc[idx, :] = [sel, nombre, contenido, notas, fila["Creado"]]
                save_df("plantillas", plantillas)
                st.success("✅ Actualizada")
                st.rerun()

    if accion == "Eliminar" and not plantillas.empty:
        sel = st.selectbox("Plantilla ID a eliminar", plantillas["ID"].tolist())
        if st.button("🗑️ Eliminar plantilla"):
            plantillas = plantillas[plantillas["ID"] != sel].copy()
            save_df("plantillas", plantillas)
            st.success("✅ Eliminada")
            st.rerun()

    st.dataframe(plantillas[["ID","Nombre","Notas","Creado"]], use_container_width=True)

# ==========================================================
# GENERAR CONTRATO
# ==========================================================
def build_context(expediente: str):
    expediente = normalize_key(expediente)
    c = casos[casos["Expediente"] == expediente]
    if c.empty:
        return {}
    c = c.iloc[0]

    cli = clientes[clientes["Nombre"] == c["Cliente"]]
    cli = cli.iloc[0] if not cli.empty else None

    hon = safe_float_series(honorarios[honorarios["Caso"] == expediente]["Monto Pactado"]).sum()
    base = safe_float_series(cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"]).sum()
    porc_series = safe_float_series(cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"])
    porc = float(porc_series.iloc[-1]) if len(porc_series) else 0.0

    ctx = {
        "{{EXPEDIENTE}}": expediente,
        "{{MATERIA}}": str(c["Materia"]),
        "{{PRETENSION}}": str(c["Pretension"]),
        "{{CLIENTE_NOMBRE}}": str(c["Cliente"]),
        "{{ABOGADO_NOMBRE}}": str(c["Abogado"]),
        "{{MONTO_PACTADO}}": f"{hon:.2f}",
        "{{MONTO_BASE}}": f"{base:.2f}",
        "{{PORCENTAJE_LITIS}}": f"{porc:.2f}",
        "{{FECHA_HOY}}": date.today().strftime("%Y-%m-%d"),
    }
    if cli is not None:
        ctx.update({
            "{{CLIENTE_DNI}}": str(cli["DNI"]),
            "{{CLIENTE_CELULAR}}": str(cli["Celular"]),
            "{{CLIENTE_CORREO}}": str(cli["Correo"]),
            "{{CLIENTE_DIRECCION}}": str(cli["Direccion"]),
        })
    return ctx

def render_template(text: str, ctx: dict) -> str:
    out = text
    for k, v in ctx.items():
        out = out.replace(k, v)
    return out

if menu == "Generar Contrato":
    st.subheader("📄 Generar contrato automático")

    if plantillas.empty:
        st.info("Primero crea una plantilla.")
    elif casos.empty:
        st.info("Primero registra casos.")
    else:
        exp = st.selectbox("Expediente", casos["Expediente"].tolist())
        tpl_id = st.selectbox("Plantilla", plantillas["ID"].tolist())
        tpl = plantillas[plantillas["ID"] == tpl_id].iloc[0]
        ctx = build_context(exp)
        generado = render_template(str(tpl["Contenido"]), ctx)

        st.text_area("Contrato generado", value=generado, height=320)

        nombre_archivo = f"Contrato_{normalize_key(exp).replace('/','_')}_{str(tpl['Nombre']).replace(' ','_')}.txt"
        st.download_button("⬇️ Descargar (TXT)", data=generado.encode("utf-8"), file_name=nombre_archivo)

# ==========================================================
# REPORTES
# ==========================================================
if menu == "Reportes":
    st.subheader("📈 Reportes")
    df_res = resumen_financiero_df()
    st.markdown("### Saldos por cliente")
    st.dataframe(saldo_por_cliente(), use_container_width=True)
    st.markdown("### Saldos por caso")
    st.dataframe(df_res, use_container_width=True)
    st.download_button("Descargar reporte clientes (CSV)", saldo_por_cliente().to_csv(index=False).encode("utf-8"), "reporte_clientes.csv")
    st.download_button("Descargar reporte casos (CSV)", df_res.to_csv(index=False).encode("utf-8"), "reporte_casos.csv")

# ==========================================================
# USUARIOS (ADMIN)
# ==========================================================
if menu == "Usuarios":
    require_admin()
    st.subheader("👥 Usuarios")

    users = load_df("usuarios")
    st.dataframe(users[["Usuario","Rol","Activo","Creado"]], use_container_width=True)

    accion = st.radio("Acción", ["Nuevo","Cambiar contraseña","Activar/Desactivar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        with st.form("new_user"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            rol = st.selectbox("Rol", ["admin","usuario"])
            submit = st.form_submit_button("Crear")
            if submit:
                if (users["Usuario"].astype(str) == str(u)).any():
                    st.error("Ese usuario ya existe.")
                else:
                    users = add_row(users, {
                        "Usuario": u,
                        "PasswordHash": sha256(p),
                        "Rol": rol,
                        "Activo": "1",
                        "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }, "usuarios")
                    save_df("usuarios", users)
                    st.success("✅ Usuario creado")
                    st.rerun()

    if accion == "Cambiar contraseña":
        sel = st.selectbox("Usuario", users["Usuario"].tolist())
        newp = st.text_input("Nueva contraseña", type="password")
        if st.button("Guardar contraseña"):
            idx = users.index[users["Usuario"] == sel][0]
            users.loc[idx, "PasswordHash"] = sha256(newp)
            save_df("usuarios", users)
            st.success("✅ Contraseña cambiada")
            st.rerun()

    if accion == "Activar/Desactivar":
        sel = st.selectbox("Usuario", users["Usuario"].tolist())
        row = users[users["Usuario"] == sel].iloc[0]
        estado = str(row["Activo"])
        st.write("Estado actual:", "Activo" if estado == "1" else "Inactivo")
        if st.button("Alternar estado"):
            idx = users.index[users["Usuario"] == sel][0]
            users.loc[idx, "Activo"] = "0" if estado == "1" else "1"
            save_df("usuarios", users)
            st.success("✅ Estado actualizado")
            st.rerun()

    if accion == "Eliminar":
        sel = st.selectbox("Usuario a eliminar", users["Usuario"].tolist())
        if sel == "admin":
            st.error("No puedes eliminar admin.")
        else:
            if st.button("Eliminar usuario"):
                users = users[users["Usuario"] != sel].copy()
                save_df("usuarios", users)
                st.success("✅ Usuario eliminado")
                st.rerun()

# ==========================================================
# RESUMEN FINANCIERO
# ==========================================================
if menu == "Resumen Financiero":
    st.subheader("📌 Resumen Financiero")
    st.dataframe(resumen_financiero_df(), use_container_width=True)

    st.markdown("### Cuotas pendientes")
    df_status = cuotas_status_all()
    df_pend = cuotas_pendientes(df_status)
    st.dataframe(df_pend, use_container_width=True)

# ==========================================================
# AUDITORÍA: HUÉRFANOS (corrige deuda/pagos fantasmas)
# ==========================================================
if menu == "Auditoría (deudas/pagos huérfanos)":
    st.subheader("🧹 Auditoría de registros HUÉRFANOS")
    st.info("Aquí aparecen pagos/deudas que NO coinciden con un expediente vigente. Estos son los que causan deuda en dashboard pero no se ven donde esperas.")

    casos_set = set(casos["Expediente"].apply(normalize_key).tolist())

    def orphan(df):
        if df.empty:
            return df
        tmp = df.copy()
        tmp["Caso"] = tmp["Caso"].apply(normalize_key)
        return tmp[~tmp["Caso"].isin(casos_set)].copy()

    oh = orphan(honorarios)
    oph = orphan(pagos_honorarios)
    ol = orphan(cuota_litis)
    opl = orphan(pagos_litis)
    oc = orphan(cuotas)

    st.markdown("### Honorarios huérfanos")
    st.dataframe(oh, use_container_width=True)
    if not oh.empty:
        sel = st.selectbox("Eliminar honorario huérfano (ID)", oh["ID"].tolist(), key="del_oh")
        if st.button("🗑️ Eliminar honorario huérfano"):
            honorarios = honorarios[honorarios["ID"] != sel].copy()
            save_df("honorarios", honorarios)
            st.success("✅ Eliminado")
            st.rerun()

    st.markdown("### Pagos honorarios huérfanos")
    st.dataframe(oph, use_container_width=True)
    if not oph.empty:
        sel = st.selectbox("Eliminar pago honorarios huérfano (ID)", oph["ID"].tolist(), key="del_oph")
        if st.button("🗑️ Eliminar pago honorarios huérfano"):
            pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Eliminado")
            st.rerun()

    st.markdown("### Cuota litis huérfana")
    st.dataframe(ol, use_container_width=True)
    if not ol.empty:
        sel = st.selectbox("Eliminar cuota litis huérfana (ID)", ol["ID"].tolist(), key="del_ol")
        if st.button("🗑️ Eliminar cuota litis huérfana"):
            cuota_litis = cuota_litis[cuota_litis["ID"] != sel].copy()
            save_df("cuota_litis", cuota_litis)
            st.success("✅ Eliminado")
            st.rerun()

    st.markdown("### Pagos cuota litis huérfanos")
    st.dataframe(opl, use_container_width=True)
    if not opl.empty:
        sel = st.selectbox("Eliminar pago cuota litis huérfano (ID)", opl["ID"].tolist(), key="del_opl")
        if st.button("🗑️ Eliminar pago cuota litis huérfano"):
            pagos_litis = pagos_litis[pagos_litis["ID"] != sel].copy()
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Eliminado")
            st.rerun()

    st.markdown("### Cuotas (cronograma) huérfanas")
    st.dataframe(oc, use_container_width=True)
    if not oc.empty:
        sel = st.selectbox("Eliminar cuota huérfana (ID)", oc["ID"].tolist(), key="del_oc")
        if st.button("🗑️ Eliminar cuota huérfana"):
            cuotas = cuotas[cuotas["ID"] != sel].copy()
            save_df("cuotas", cuotas)
            st.success("✅ Eliminado")
            st.rerun()
