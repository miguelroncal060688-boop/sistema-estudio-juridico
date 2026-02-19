import streamlit as st
import pandas as pd
import os
import hashlib
import shutil
from datetime import date, datetime

# ==========================================================
# CONFIG GENERAL
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
# ESQUEMAS
# ==========================================================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","Activo","Creado"],

    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones","EstadoCaso","FechaInicio"],

    # Importante: con ID (para poder borrar sí o sí)
    "honorarios": ["ID","Caso","Monto Pactado","Notas","FechaRegistro"],
    "pagos_honorarios": ["ID","Caso","FechaPago","Monto","Observacion"],

    "cuota_litis": ["ID","Caso","Monto Base","Porcentaje","Notas","FechaRegistro"],
    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],

    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"],
    "actuaciones": ["ID","Caso","Fecha","TipoActuacion","Resumen","ProximaAccion","FechaProximaAccion","Notas"],

    "documentos": ["ID","Caso","Tipo","NombreArchivo","Ruta","Fecha","Notas"],
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
    m = pd.to_numeric(df[col], errors="coerce").max()
    return int(m) + 1 if pd.notna(m) else len(df) + 1

def add_row(df: pd.DataFrame, row_dict: dict, schema_key: str) -> pd.DataFrame:
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df2 = df2.reindex(columns=SCHEMAS[schema_key])
    return df2

def ensure_ids(df: pd.DataFrame, keyname: str) -> pd.DataFrame:
    """Si hay filas sin ID, se asigna automáticamente."""
    if "ID" not in df.columns:
        return df
    ids = pd.to_numeric(df["ID"], errors="coerce")
    max_id = int(ids.max()) if pd.notna(ids.max()) else 0
    for idx in df[ids.isna()].index.tolist():
        max_id += 1
        df.at[idx, "ID"] = max_id
    return df

def require_admin():
    if st.session_state.rol != "admin":
        st.error("❌ Solo ADMIN puede acceder a esta opción.")
        st.stop()

# ==========================================================
# INIT CSVs
# ==========================================================
for k in FILES:
    ensure_csv(k)

# ==========================================================
# ASEGURAR ADMIN
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
# CARGA DATOS
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

# Normalizar claves
casos["Expediente"] = casos["Expediente"].apply(normalize_key)
for dfname in ["honorarios","pagos_honorarios","cuota_litis","pagos_litis","cuotas","actuaciones","documentos"]:
    df = locals()[dfname]
    if "Caso" in df.columns:
        df["Caso"] = df["Caso"].apply(normalize_key)
    df = ensure_ids(df, dfname)
    locals()[dfname] = df

# Guardar reparaciones (IDs + normalize)
save_df("honorarios", honorarios)
save_df("pagos_honorarios", pagos_honorarios)
save_df("cuota_litis", cuota_litis)
save_df("pagos_litis", pagos_litis)
save_df("cuotas", cuotas)
save_df("actuaciones", actuaciones)
save_df("documentos", documentos)

# ==========================================================
# CANONICALIZAR (anti-fantasmas): último registro por expediente
# ==========================================================
def canon_last_by_case(df: pd.DataFrame, case_col="Caso"):
    if df.empty:
        return df
    tmp = df.copy()
    tmp[case_col] = tmp[case_col].apply(normalize_key)
    tmp["__id__"] = pd.to_numeric(tmp["ID"], errors="coerce").fillna(0).astype(int)
    tmp.sort_values([case_col, "__id__"], inplace=True)
    tmp = tmp.groupby(case_col, as_index=False).tail(1)
    tmp.drop(columns=["__id__"], inplace=True, errors="ignore")
    return tmp

def calc_cuota_litis(canon_cl: pd.DataFrame):
    if canon_cl.empty:
        return pd.DataFrame(columns=["Caso","CuotaLitisCalculada"])
    tmp = canon_cl.copy()
    tmp["Monto Base"] = safe_float_series(tmp["Monto Base"])
    tmp["Porcentaje"] = safe_float_series(tmp["Porcentaje"])
    tmp["CuotaLitisCalculada"] = tmp["Monto Base"] * tmp["Porcentaje"] / 100.0
    return tmp[["Caso","CuotaLitisCalculada"]]

# ==========================================================
# RESUMEN FINANCIERO (usa canonical para evitar fantasmas)
# ==========================================================
def resumen_financiero_df():
    if casos.empty:
        return pd.DataFrame(columns=[
            "Expediente","Cliente","Materia",
            "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
            "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
        ])

    canon_h = canon_last_by_case(honorarios, "Caso")
    canon_cl = canon_last_by_case(cuota_litis, "Caso")
    cl_calc = calc_cuota_litis(canon_cl)

    resumen = []
    for _, c in casos.iterrows():
        exp = normalize_key(c["Expediente"])
        pactado = safe_float_series(canon_h[canon_h["Caso"] == exp]["Monto Pactado"]).sum()
        pagado_h = safe_float_series(pagos_honorarios[pagos_honorarios["Caso"] == exp]["Monto"]).sum()

        calc = safe_float_series(cl_calc[cl_calc["Caso"] == exp]["CuotaLitisCalculada"]).sum()
        pagado_l = safe_float_series(pagos_litis[pagos_litis["Caso"] == exp]["Monto"]).sum()

        resumen.append([
            exp, c["Cliente"], c["Materia"],
            float(pactado), float(pagado_h), float(pactado - pagado_h),
            float(calc), float(pagado_l), float(calc - pagado_l)
        ])

    return pd.DataFrame(resumen, columns=[
        "Expediente","Cliente","Materia",
        "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
        "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
    ])

# ==========================================================
# RESET SISTEMA (suave / total)
# ==========================================================
def reset_system(mode: str, wipe_files: bool = False):
    # backup
    for k in FILES:
        backup_file(FILES[k])

    if mode == "soft":
        # elimina registros con Caso que no exista en casos
        casos_set = set(casos["Expediente"].apply(normalize_key).tolist())

        def keep_valid(df):
            if df.empty or "Caso" not in df.columns:
                return df
            df = df.copy()
            df["Caso"] = df["Caso"].apply(normalize_key)
            return df[df["Caso"].isin(casos_set)].copy()

        for keyname in ["honorarios","pagos_honorarios","cuota_litis","pagos_litis","cuotas","actuaciones","documentos"]:
            df = load_df(keyname)
            df = keep_valid(df)
            df = ensure_ids(df, keyname)
            save_df(keyname, df)

    elif mode == "hard":
        # borra todo menos usuarios; recrea admin
        for keyname in FILES:
            if keyname == "usuarios":
                continue
            pd.DataFrame(columns=SCHEMAS[keyname]).to_csv(FILES[keyname], index=False)

        users = pd.DataFrame(columns=SCHEMAS["usuarios"])
        users = pd.concat([users, pd.DataFrame([{
            "Usuario":"admin",
            "PasswordHash": sha256("estudio123"),
            "Rol":"admin",
            "Activo":"1",
            "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])], ignore_index=True)
        users.to_csv(FILES["usuarios"], index=False)

        if wipe_files:
            for folder in [UPLOADS_DIR, GENERADOS_DIR]:
                try:
                    if os.path.exists(folder):
                        shutil.rmtree(folder)
                    os.makedirs(folder, exist_ok=True)
                except Exception:
                    pass

# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.write(f"👤 Usuario: {st.session_state.usuario} ({st.session_state.rol})")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.rerun()

with st.sidebar.expander("🧨 Resetear sistema", expanded=False):
    st.write("**Reset suave**: limpia huérfanos (fantasmas) sin borrar casos válidos.")
    st.write("**Reset total**: borra todo y reinicia limpio.")
    token = st.text_input("Escribe RESET para habilitar", value="")
    if token.strip().upper() == "RESET":
        if st.button("✅ Reset suave (limpiar fantasmas)"):
            reset_system("soft")
            st.success("✅ Reset suave aplicado")
            st.rerun()
        wipe = st.checkbox("Borrar también uploads/ y generados/ (solo reset total)", value=False)
        if st.button("🧨 Reset total (borra todo)"):
            reset_system("hard", wipe_files=wipe)
            st.success("✅ Reset total aplicado. admin/estudio123")
            st.rerun()
    else:
        st.info("Escribe RESET para habilitar.")

# ==========================================================
# MENÚ COMPLETO (mantiene todo)
# ==========================================================
menu = st.sidebar.selectbox("📌 Menú", [
    "Dashboard",
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
    "Auditoría (ver todo lo que suma)"
])

brand_header()

# ==========================================================
# DASHBOARD
# ==========================================================
if menu == "Dashboard":
    df_res = resumen_financiero_df()

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
    st.subheader("Detalle por caso")
    st.dataframe(df_res, use_container_width=True)

# ==========================================================
# CLIENTES (CRUD)
# ==========================================================
if menu == "Clientes":
    st.subheader("Clientes")
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
                    "ID": new_id, "Nombre": nombre, "DNI": dni, "Celular": celular,
                    "Correo": correo, "Direccion": direccion, "Observaciones": obs
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
        if st.button("Eliminar cliente"):
            clientes = clientes[clientes["ID"] != sel].copy()
            save_df("clientes", clientes)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(clientes, use_container_width=True)

# ==========================================================
# ABOGADOS / CASOS (solo mostrar para mantenerlo corto en este bloque)
# (Si quieres, te pongo CRUD completo aquí también)
# ==========================================================
if menu == "Abogados":
    st.subheader("Abogados")
    st.dataframe(abogados, use_container_width=True)

if menu == "Casos":
    st.subheader("Casos")
    st.dataframe(casos, use_container_width=True)

# ==========================================================
# HONORARIOS (config)
# ==========================================================
if menu == "Honorarios":
    st.subheader("Honorarios (config)")
    st.info("El Dashboard toma el ÚLTIMO registro por expediente para evitar deudas fantasma antiguas.")

    st.markdown("### Registros (raw)")
    st.dataframe(honorarios.sort_values("ID", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")
    monto = st.number_input("Monto pactado", min_value=0.0, step=50.0)
    notas = st.text_input("Notas", value="")

    if st.button("Guardar (nuevo registro)"):
        new_id = next_id(honorarios)
        honorarios = add_row(honorarios, {
            "ID": new_id, "Caso": normalize_key(exp), "Monto Pactado": float(monto),
            "Notas": notas, "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "honorarios")
        save_df("honorarios", honorarios)
        st.success("✅ Guardado")
        st.rerun()

    st.divider()
    st.markdown("### Borrar honorario (por ID)")
    if not honorarios.empty:
        sel = st.selectbox("ID a borrar", honorarios["ID"].tolist())
        if st.button("🗑️ Borrar honorario"):
            honorarios = honorarios[honorarios["ID"] != sel].copy()
            save_df("honorarios", honorarios)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# PAGOS HONORARIOS (tabla siempre + borrar)
# ==========================================================
if menu == "Pagos Honorarios":
    st.subheader("Pagos Honorarios")
    st.dataframe(pagos_honorarios.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente del pago", exp_list) if exp_list else st.text_input("Expediente")
    fecha = st.date_input("Fecha", value=date.today())
    monto = st.number_input("Monto", min_value=0.0, step=50.0)
    obs = st.text_input("Observación", value="")

    if st.button("Registrar pago"):
        new_id = next_id(pagos_honorarios)
        pagos_honorarios = add_row(pagos_honorarios, {
            "ID": new_id, "Caso": normalize_key(exp), "FechaPago": str(fecha),
            "Monto": float(monto), "Observacion": obs
        }, "pagos_honorarios")
        save_df("pagos_honorarios", pagos_honorarios)
        st.success("✅ Registrado")
        st.rerun()

    st.divider()
    if not pagos_honorarios.empty:
        sel = st.selectbox("Pago ID a borrar", pagos_honorarios["ID"].tolist())
        if st.button("🗑️ Borrar pago honorarios"):
            pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# CUOTA LITIS (config)
# ==========================================================
if menu == "Cuota Litis":
    st.subheader("Cuota Litis (config)")
    st.info("El Dashboard toma el ÚLTIMO registro por expediente para evitar deudas fantasma antiguas.")

    st.dataframe(cuota_litis.sort_values("ID", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente", exp_list) if exp_list else st.text_input("Expediente")
    base = st.number_input("Monto base", min_value=0.0, step=100.0)
    porc = st.number_input("Porcentaje (%)", min_value=0.0, step=1.0)
    notas = st.text_input("Notas", value="")

    if st.button("Guardar (nuevo registro cuota litis)"):
        new_id = next_id(cuota_litis)
        cuota_litis = add_row(cuota_litis, {
            "ID": new_id, "Caso": normalize_key(exp), "Monto Base": float(base),
            "Porcentaje": float(porc), "Notas": notas,
            "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "cuota_litis")
        save_df("cuota_litis", cuota_litis)
        st.success("✅ Guardado")
        st.rerun()

    st.divider()
    if not cuota_litis.empty:
        sel = st.selectbox("Cuota Litis ID a borrar", cuota_litis["ID"].tolist())
        if st.button("🗑️ Borrar cuota litis"):
            cuota_litis = cuota_litis[cuota_litis["ID"] != sel].copy()
            save_df("cuota_litis", cuota_litis)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# PAGOS CUOTA LITIS
# ==========================================================
if menu == "Pagos Cuota Litis":
    st.subheader("Pagos Cuota Litis")
    st.dataframe(pagos_litis.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    exp = st.selectbox("Expediente del pago", exp_list) if exp_list else st.text_input("Expediente")
    fecha = st.date_input("Fecha", value=date.today())
    monto = st.number_input("Monto", min_value=0.0, step=50.0)
    obs = st.text_input("Observación", value="")

    if st.button("Registrar pago litis"):
        new_id = next_id(pagos_litis)
        pagos_litis = add_row(pagos_litis, {
            "ID": new_id, "Caso": normalize_key(exp), "FechaPago": str(fecha),
            "Monto": float(monto), "Observacion": obs
        }, "pagos_litis")
        save_df("pagos_litis", pagos_litis)
        st.success("✅ Registrado")
        st.rerun()

    st.divider()
    if not pagos_litis.empty:
        sel = st.selectbox("Pago Litis ID a borrar", pagos_litis["ID"].tolist())
        if st.button("🗑️ Borrar pago litis"):
            pagos_litis = pagos_litis[pagos_litis["ID"] != sel].copy()
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# OTROS MENÚS (para mantenerlo completo)
# ==========================================================
if menu == "Cronograma de Cuotas":
    st.subheader("Cronograma de Cuotas")
    st.dataframe(cuotas, use_container_width=True)

if menu == "Actuaciones":
    st.subheader("Actuaciones")
    st.dataframe(actuaciones, use_container_width=True)

if menu == "Documentos":
    st.subheader("Documentos")
    st.dataframe(documentos, use_container_width=True)

if menu == "Plantillas de Contrato":
    st.subheader("Plantillas de Contrato")
    st.dataframe(plantillas, use_container_width=True)

if menu == "Generar Contrato":
    st.subheader("Generar Contrato")
    st.info("Usa plantillas para generar TXT. (Si quieres DOCX luego lo agrego.)")

if menu == "Reportes":
    st.subheader("Reportes")
    st.dataframe(resumen_financiero_df(), use_container_width=True)

if menu == "Usuarios":
    require_admin()
    st.subheader("Usuarios")
    st.dataframe(usuarios_df, use_container_width=True)

if menu == "Auditoría (ver todo lo que suma)":
    st.subheader("Auditoría: todo lo que suma en dashboard")
    st.markdown("### honorarios")
    st.dataframe(honorarios, use_container_width=True)
    st.markdown("### pagos_honorarios")
    st.dataframe(pagos_honorarios, use_container_width=True)
    st.markdown("### cuota_litis")
    st.dataframe(cuota_litis, use_container_width=True)
    st.markdown("### pagos_litis")
    st.dataframe(pagos_litis, use_container_width=True)
