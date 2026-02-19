import streamlit as st
import pandas as pd
import os
import hashlib
import shutil
from datetime import date, datetime

# =========================
# CONFIG
# =========================
APP_NAME = "Estudio Jurídico Roncal Liñan y Asociados"
st.set_page_config(page_title=f"⚖️ {APP_NAME}", layout="wide")

DATA_DIR = "."
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
GENERADOS_DIR = os.path.join(DATA_DIR, "generados")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERADOS_DIR, exist_ok=True)

# =========================
# ARCHIVOS
# =========================
FILES = {
    "usuarios": "usuarios.csv",
    "clientes": "clientes.csv",
    "abogados": "abogados.csv",
    "casos": "casos.csv",
    "honorarios": "honorarios.csv",
    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",
    "cuotas": "cuotas.csv",
    "actuaciones": "actuaciones.csv",
    "documentos": "documentos.csv",
    "plantillas": "plantillas_contratos.csv",
}

# =========================
# ESQUEMAS (con ID donde corresponde)
# =========================
SCHEMAS = {
    "usuarios": ["Usuario", "PasswordHash", "Rol", "AbogadoID", "Activo", "Creado"],
    "clientes": ["ID", "Nombre", "DNI", "Celular", "Correo", "Direccion", "Observaciones"],
    "abogados": ["ID", "Nombre", "DNI", "Celular", "Correo", "Colegiatura", "Domicilio Procesal", "Casilla Electronica", "Casilla Judicial"],
    "casos": ["ID", "Cliente", "Abogado", "Expediente", "Año", "Materia", "Pretension", "Observaciones", "EstadoCaso", "FechaInicio"],

    "honorarios": ["ID", "Caso", "Monto Pactado", "Notas", "FechaRegistro"],
    "pagos_honorarios": ["ID", "Caso", "FechaPago", "Monto", "Observacion"],

    "cuota_litis": ["ID", "Caso", "Monto Base", "Porcentaje", "Notas", "FechaRegistro"],
    "pagos_litis": ["ID", "Caso", "FechaPago", "Monto", "Observacion"],

    "cuotas": ["ID", "Caso", "Tipo", "NroCuota", "FechaVenc", "Monto", "Notas"],
    "actuaciones": ["ID", "Caso", "Fecha", "TipoActuacion", "Resumen", "ProximaAccion", "FechaProximaAccion", "Notas"],

    "documentos": ["ID", "Caso", "Tipo", "NombreArchivo", "Ruta", "Fecha", "Notas"],
    "plantillas": ["ID", "Nombre", "Contenido", "Notas", "Creado"],
}

# =========================
# UTILIDADES
# =========================
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def brand_header():
    st.markdown(
        f"""
        <div style="padding:10px 0 0 0;">
            <h1 style="margin-bottom:0;">⚖️ {APP_NAME}</h1>
            <p style="margin-top:2px;color:#666;">Sistema de gestión de clientes, casos, pagos, cuotas y contratos</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def drop_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.str.contains(r"^Unnamed", case=False, na=False)]

def backup_file(path: str):
    if not os.path.exists(path):
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(path)
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

    # si está vacío
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
    backup_file(FILES[key])
    df = drop_unnamed(df)
    df = df.reindex(columns=SCHEMAS[key])
    df.to_csv(FILES[key], index=False)

def next_id(df: pd.DataFrame, col="ID") -> int:
    if df.empty:
        return 1
    m = pd.to_numeric(df[col], errors="coerce").max()
    return int(m) + 1 if pd.notna(m) else len(df) + 1

def ensure_ids(df: pd.DataFrame) -> pd.DataFrame:
    # Asigna IDs faltantes (para poder borrar cualquier “fantasma”)
    if "ID" not in df.columns:
        return df
    ids = pd.to_numeric(df["ID"], errors="coerce")
    max_id = int(ids.max()) if pd.notna(ids.max()) else 0
    for idx in df[ids.isna()].index.tolist():
        max_id += 1
        df.at[idx, "ID"] = max_id
    return df

def add_row(df: pd.DataFrame, row_dict: dict, schema_key: str) -> pd.DataFrame:
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df2 = df2.reindex(columns=SCHEMAS[schema_key])
    return df2

def require_admin():
    if st.session_state.rol != "admin":
        st.error("❌ Solo ADMIN puede acceder a esta opción.")
        st.stop()

# =========================
# INIT CSVs
# =========================
for k in FILES:
    ensure_csv(k)

# =========================
# ASEGURAR ADMIN (no pisa datos existentes)
# =========================
usuarios_df = load_df("usuarios")
if usuarios_df[usuarios_df["Usuario"].astype(str) == "admin"].empty:
    usuarios_df = add_row(usuarios_df, {
        "Usuario": "admin",
        "PasswordHash": sha256("estudio123"),
        "Rol": "admin",
        "AbogadoID": "",
        "Activo": "1",
        "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }, "usuarios")
    save_df("usuarios", usuarios_df)

# =========================
# LOGIN
# =========================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None
if "abogado_id" not in st.session_state:
    st.session_state.abogado_id = None

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
        st.session_state.abogado_id = row.iloc[0]["AbogadoID"] if "AbogadoID" in row.columns else ""
        st.rerun()

if st.session_state.usuario is None:
    login_ui()
    st.stop()

# =========================
# CARGAR DATA
# =========================
clientes = load_df("clientes")
abogados = load_df("abogados")
casos = load_df("casos")

honorarios = ensure_ids(load_df("honorarios"))
pagos_honorarios = ensure_ids(load_df("pagos_honorarios"))
cuota_litis = ensure_ids(load_df("cuota_litis"))
pagos_litis = ensure_ids(load_df("pagos_litis"))

cuotas = ensure_ids(load_df("cuotas"))
actuaciones = ensure_ids(load_df("actuaciones"))
documentos = ensure_ids(load_df("documentos"))
plantillas = ensure_ids(load_df("plantillas"))

# Normalizar claves
casos["Expediente"] = casos["Expediente"].apply(normalize_key)
for dfname in [honorarios, pagos_honorarios, cuota_litis, pagos_litis, cuotas, actuaciones, documentos]:
    if "Caso" in dfname.columns:
        dfname["Caso"] = dfname["Caso"].apply(normalize_key)

# Guardar reparaciones de IDs (no borra datos)
save_df("honorarios", honorarios)
save_df("pagos_honorarios", pagos_honorarios)
save_df("cuota_litis", cuota_litis)
save_df("pagos_litis", pagos_litis)
save_df("cuotas", cuotas)
save_df("actuaciones", actuaciones)
save_df("documentos", documentos)
save_df("plantillas", plantillas)

# =========================
# CÁLCULOS (anti fantasmas)
# =========================
def canon_last_by_case(df: pd.DataFrame, case_col="Caso"):
    # usa el último registro (por ID) para evitar sumas dobles antiguas
    if df.empty:
        return df
    tmp = df.copy()
    tmp[case_col] = tmp[case_col].apply(normalize_key)
    tmp["_id"] = pd.to_numeric(tmp["ID"], errors="coerce").fillna(0).astype(int)
    tmp.sort_values([case_col, "_id"], inplace=True)
    tmp = tmp.groupby(case_col, as_index=False).tail(1)
    tmp.drop(columns=["_id"], inplace=True, errors="ignore")
    return tmp

def resumen_financiero_df():
    if casos.empty:
        return pd.DataFrame(columns=[
            "Expediente","Cliente","Materia",
            "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
            "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
        ])

    canon_h = canon_last_by_case(honorarios, "Caso")
    canon_cl = canon_last_by_case(cuota_litis, "Caso")
    canon_cl["Monto Base"] = safe_float_series(canon_cl["Monto Base"])
    canon_cl["Porcentaje"] = safe_float_series(canon_cl["Porcentaje"])
    canon_cl["CuotaCalc"] = canon_cl["Monto Base"] * canon_cl["Porcentaje"] / 100.0

    resumen = []
    for _, c in casos.iterrows():
        exp = normalize_key(c["Expediente"])
        pactado = safe_float_series(canon_h[canon_h["Caso"] == exp]["Monto Pactado"]).sum()
        pagado_h = safe_float_series(pagos_honorarios[pagos_honorarios["Caso"] == exp]["Monto"]).sum()

        calc = safe_float_series(canon_cl[canon_cl["Caso"] == exp]["CuotaCalc"]).sum()
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

# =========================
# RESET (solo por botón, NO borra solo)
# =========================
def reset_suave():
    # Limpia huérfanos (Caso no existe) + normaliza + re-asigna IDs
    casos_set = set(casos["Expediente"].apply(normalize_key).tolist())

    def clean_df(keyname):
        df = load_df(keyname)
        if "Caso" in df.columns:
            df["Caso"] = df["Caso"].apply(normalize_key)
            df = df[df["Caso"].isin(casos_set)].copy()
        df = ensure_ids(df)
        save_df(keyname, df)

    for k in ["honorarios","pagos_honorarios","cuota_litis","pagos_litis","cuotas","actuaciones","documentos"]:
        clean_df(k)

def reset_total(borrar_archivos=False):
    # Borra todo menos usuarios (y recrea admin)
    for k in FILES:
        backup_file(FILES[k])

    for k in FILES:
        if k == "usuarios":
            continue
        pd.DataFrame(columns=SCHEMAS[k]).to_csv(FILES[k], index=False)

    users = pd.DataFrame(columns=SCHEMAS["usuarios"])
    users = pd.concat([users, pd.DataFrame([{
        "Usuario":"admin",
        "PasswordHash": sha256("estudio123"),
        "Rol":"admin",
        "AbogadoID":"",
        "Activo":"1",
        "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])], ignore_index=True)
    users.to_csv(FILES["usuarios"], index=False)

    if borrar_archivos:
        for folder in [UPLOADS_DIR, GENERADOS_DIR]:
            try:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass

# =========================
# SIDEBAR
# =========================
st.sidebar.write(f"👤 Usuario: {st.session_state.usuario} ({st.session_state.rol})")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.abogado_id = None
    st.rerun()

with st.sidebar.expander("🧨 Resetear sistema"):
    st.write("Reset suave limpia huérfanos/IDs sin borrar casos válidos.")
    st.write("Reset total borra todo (deja admin).")
    token = st.text_input("Escribe RESET para habilitar", value="")
    if token.strip().upper() == "RESET":
        if st.button("✅ Reset suave (limpiar fantasmas)"):
            reset_suave()
            st.success("✅ Reset suave aplicado")
            st.rerun()

        borrar = st.checkbox("Borrar también uploads/ y generados/ (solo reset total)", value=False)
        if st.button("🧨 Reset total (borra todo)"):
            reset_total(borrar_archivos=borrar)
            st.success("✅ Reset total aplicado. admin/estudio123")
            st.rerun()
    else:
        st.info("Escribe RESET para habilitar.")

# =========================
# MENÚ
# =========================
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
    "Auditoría (fantasmas)"
])

# =========================
# UI HEADER
# =========================
brand_header()

# =========================
# DASHBOARD
# =========================
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

# =========================
# CLIENTES (CRUD)
# =========================
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
                    "ID": new_id, "Nombre": nombre, "DNI": dni, "Celular": celular,
                    "Correo": correo, "Direccion": direccion, "Observaciones": obs
                }, "clientes")
                save_df("clientes", clientes)
                st.success("✅ Cliente registrado")
                st.rerun()

    elif accion == "Editar" and not clientes.empty:
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

    elif accion == "Eliminar" and not clientes.empty:
        sel = st.selectbox("Cliente ID a eliminar", clientes["ID"].tolist())
        if st.button("Eliminar cliente"):
            clientes = clientes[clientes["ID"] != sel].copy()
            save_df("clientes", clientes)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(clientes, use_container_width=True)

# =========================
# ABOGADOS (CRUD)
# =========================
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

    elif accion == "Editar" and not abogados.empty:
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

    elif accion == "Eliminar" and not abogados.empty:
        sel = st.selectbox("Abogado ID a eliminar", abogados["ID"].tolist())
        if st.button("Eliminar abogado"):
            abogados = abogados[abogados["ID"] != sel].copy()
            save_df("abogados", abogados)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(abogados, use_container_width=True)

# =========================
# CASOS (CRUD) - pagos SIEMPRE se vinculan aquí
# =========================
if menu == "Casos":
    st.subheader("📁 Casos")
    accion = st.radio("Acción", ["Nuevo","Editar","Eliminar"], horizontal=True)

    clientes_list = clientes["Nombre"].tolist() if not clientes.empty else []
    abogados_list = abogados["Nombre"].tolist() if not abogados.empty else []

    if accion == "Nuevo":
        if not clientes_list:
            st.warning("Primero registra clientes.")
        elif not abogados_list:
            st.warning("Primero registra abogados.")
        else:
            with st.form("nuevo_caso"):
                cliente = st.selectbox("Cliente", clientes_list)
                abogado = st.selectbox("Abogado", abogados_list)
                expediente = st.text_input("Expediente")
                anio = st.text_input("Año")
                materia = st.text_input("Materia")
                pret = st.text_input("Pretensión")
                obs = st.text_area("Observaciones")
                estado = st.selectbox("EstadoCaso", ["Activo","En pausa","Cerrado","Archivado"])
                fi = st.date_input("Fecha inicio", value=date.today())
                submit = st.form_submit_button("Guardar")
                if submit:
                    new_id = next_id(casos)
                    casos = add_row(casos, {
                        "ID": new_id,
                        "Cliente": cliente,
                        "Abogado": abogado,
                        "Expediente": normalize_key(expediente),
                        "Año": anio,
                        "Materia": materia,
                        "Pretension": pret,
                        "Observaciones": obs,
                        "EstadoCaso": estado,
                        "FechaInicio": str(fi)
                    }, "casos")
                    save_df("casos", casos)
                    st.success("✅ Caso registrado")
                    st.rerun()

    elif accion == "Editar" and not casos.empty:
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
            fi2 = st.date_input("Fecha inicio", value=fi)
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = casos.index[casos["ID"] == sel][0]
                casos.loc[idx, :] = [sel, cliente, abogado, normalize_key(expediente), anio, materia, pret, obs, estado, str(fi2)]
                save_df("casos", casos)
                st.success("✅ Actualizado")
                st.rerun()

    elif accion == "Eliminar" and not casos.empty:
        sel = st.selectbox("Caso ID a eliminar", casos["ID"].tolist())
        if st.button("Eliminar caso"):
            casos = casos[casos["ID"] != sel].copy()
            save_df("casos", casos)
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(casos, use_container_width=True)

# =========================
# HONORARIOS (config)
# =========================
if menu == "Honorarios":
    st.subheader("🧾 Honorarios (configuración)")
    st.dataframe(honorarios.sort_values("ID", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    if exp_list:
        exp = st.selectbox("Expediente", exp_list)
        monto = st.number_input("Monto pactado", min_value=0.0, step=50.0)
        notas = st.text_input("Notas", value="")
        if st.button("Guardar honorario"):
            new_id = next_id(honorarios)
            honorarios = add_row(honorarios, {
                "ID": new_id, "Caso": normalize_key(exp), "Monto Pactado": float(monto),
                "Notas": notas, "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, "honorarios")
            save_df("honorarios", honorarios)
            st.success("✅ Guardado")
            st.rerun()

    st.divider()
    st.markdown("### Borrar/Modificar honorario (por ID)")
    if not honorarios.empty:
        sel = st.selectbox("Honorario ID", honorarios["ID"].tolist())
        fila = honorarios[honorarios["ID"] == sel].iloc[0]
        with st.form("edit_hon"):
            caso_e = st.text_input("Caso", value=str(fila["Caso"]))
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto Pactado"]), step=50.0)
            notas_e = st.text_input("Notas", value=str(fila["Notas"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = honorarios.index[honorarios["ID"] == sel][0]
                honorarios.loc[idx, ["Caso","Monto Pactado","Notas"]] = [normalize_key(caso_e), float(monto_e), notas_e]
                save_df("honorarios", honorarios)
                st.success("✅ Actualizado")
                st.rerun()
        if st.button("🗑️ Borrar honorario"):
            honorarios = honorarios[honorarios["ID"] != sel].copy()
            save_df("honorarios", honorarios)
            st.success("✅ Eliminado")
            st.rerun()

# =========================
# PAGOS HONORARIOS (solo vincula a casos existentes + Editar/Borrar)
# =========================
if menu == "Pagos Honorarios":
    st.subheader("💳 Pagos Honorarios")
    st.dataframe(pagos_honorarios.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist()
    if exp_list:
        exp = st.selectbox("Expediente (obligatorio)", exp_list)
        fecha = st.date_input("Fecha", value=date.today())
        monto = st.number_input("Monto", min_value=0.0, step=50.0)
        obs = st.text_input("Observación", value="")
        if st.button("Registrar pago honorarios"):
            new_id = next_id(pagos_honorarios)
            pagos_honorarios = add_row(pagos_honorarios, {
                "ID": new_id, "Caso": normalize_key(exp), "FechaPago": str(fecha),
                "Monto": float(monto), "Observacion": obs
            }, "pagos_honorarios")
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Registrado")
            st.rerun()

    st.divider()
    st.markdown("### Editar/Borrar pago (por ID)")
    if not pagos_honorarios.empty:
        sel = st.selectbox("Pago ID", pagos_honorarios["ID"].tolist())
        fila = pagos_honorarios[pagos_honorarios["ID"] == sel].iloc[0]
        with st.form("edit_ph"):
            caso_e = st.selectbox("Expediente", exp_list, index=exp_list.index(fila["Caso"]) if fila["Caso"] in exp_list else 0)
            fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
            obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = pagos_honorarios.index[pagos_honorarios["ID"] == sel][0]
                pagos_honorarios.loc[idx, :] = [sel, normalize_key(caso_e), fecha_e, float(monto_e), obs_e]
                save_df("pagos_honorarios", pagos_honorarios)
                st.success("✅ Actualizado")
                st.rerun()
        if st.button("🗑️ Borrar pago honorarios"):
            pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Eliminado")
            st.rerun()

# =========================
# CUOTA LITIS (config) + Editar/Borrar
# =========================
if menu == "Cuota Litis":
    st.subheader("⚖️ Cuota Litis (configuración)")
    st.dataframe(cuota_litis.sort_values("ID", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist()
    if exp_list:
        exp = st.selectbox("Expediente", exp_list)
        base = st.number_input("Monto base", min_value=0.0, step=100.0)
        porc = st.number_input("Porcentaje (%)", min_value=0.0, step=1.0)
        notas = st.text_input("Notas", value="")
        if st.button("Guardar cuota litis"):
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
    st.markdown("### Editar/Borrar cuota litis (por ID)")
    if not cuota_litis.empty:
        sel = st.selectbox("CuotaLitis ID", cuota_litis["ID"].tolist())
        fila = cuota_litis[cuota_litis["ID"] == sel].iloc[0]
        with st.form("edit_cl"):
            caso_e = st.selectbox("Expediente", exp_list, index=exp_list.index(fila["Caso"]) if fila["Caso"] in exp_list else 0)
            base_e = st.number_input("Monto base", min_value=0.0, value=money(fila["Monto Base"]), step=100.0)
            porc_e = st.number_input("Porcentaje", min_value=0.0, value=money(fila["Porcentaje"]), step=1.0)
            notas_e = st.text_input("Notas", value=str(fila["Notas"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = cuota_litis.index[cuota_litis["ID"] == sel][0]
                cuota_litis.loc[idx, ["Caso","Monto Base","Porcentaje","Notas"]] = [normalize_key(caso_e), float(base_e), float(porc_e), notas_e]
                save_df("cuota_litis", cuota_litis)
                st.success("✅ Actualizado")
                st.rerun()
        if st.button("🗑️ Borrar cuota litis"):
            cuota_litis = cuota_litis[cuota_litis["ID"] != sel].copy()
            save_df("cuota_litis", cuota_litis)
            st.success("✅ Eliminado")
            st.rerun()

# =========================
# PAGOS CUOTA LITIS (solo vincula a casos existentes + Editar/Borrar)
# =========================
if menu == "Pagos Cuota Litis":
    st.subheader("💳 Pagos Cuota Litis")
    st.dataframe(pagos_litis.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist()
    if exp_list:
        exp = st.selectbox("Expediente (obligatorio)", exp_list)
        fecha = st.date_input("Fecha", value=date.today())
        monto = st.number_input("Monto", min_value=0.0, step=50.0)
        obs = st.text_input("Observación", value="")
        if st.button("Registrar pago cuota litis"):
            new_id = next_id(pagos_litis)
            pagos_litis = add_row(pagos_litis, {
                "ID": new_id, "Caso": normalize_key(exp), "FechaPago": str(fecha),
                "Monto": float(monto), "Observacion": obs
            }, "pagos_litis")
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Registrado")
            st.rerun()

    st.divider()
    st.markdown("### Editar/Borrar pago (por ID)")
    if not pagos_litis.empty:
        sel = st.selectbox("Pago ID", pagos_litis["ID"].tolist())
        fila = pagos_litis[pagos_litis["ID"] == sel].iloc[0]
        with st.form("edit_pl"):
            caso_e = st.selectbox("Expediente", exp_list, index=exp_list.index(fila["Caso"]) if fila["Caso"] in exp_list else 0)
            fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
            obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = pagos_litis.index[pagos_litis["ID"] == sel][0]
                pagos_litis.loc[idx, :] = [sel, normalize_key(caso_e), fecha_e, float(monto_e), obs_e]
                save_df("pagos_litis", pagos_litis)
                st.success("✅ Actualizado")
                st.rerun()
        if st.button("🗑️ Borrar pago cuota litis"):
            pagos_litis = pagos_litis[pagos_litis["ID"] != sel].copy()
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Eliminado")
            st.rerun()

# =========================
# CRONOGRAMA / ACTUACIONES / DOCUMENTOS / PLANTILLAS / CONTRATOS / REPORTES / USUARIOS / AUDITORÍA
# (Se mantienen para no recortar; muestran tablas y permiten borrado por ID)
# =========================
if menu == "Cronograma de Cuotas":
    st.subheader("📅 Cronograma de Cuotas")
    st.dataframe(cuotas, use_container_width=True)
    if not cuotas.empty:
        sel = st.selectbox("Cuota ID a borrar", cuotas["ID"].tolist())
        if st.button("🗑️ Borrar cuota"):
            cuotas = cuotas[cuotas["ID"] != sel].copy()
            save_df("cuotas", cuotas)
            st.success("✅ Eliminado")
            st.rerun()

if menu == "Actuaciones":
    st.subheader("🧾 Actuaciones")
    st.dataframe(actuaciones, use_container_width=True)
    if not actuaciones.empty:
        sel = st.selectbox("Actuación ID a borrar", actuaciones["ID"].tolist())
        if st.button("🗑️ Borrar actuación"):
            actuaciones = actuaciones[actuaciones["ID"] != sel].copy()
            save_df("actuaciones", actuaciones)
            st.success("✅ Eliminado")
            st.rerun()

if menu == "Documentos":
    st.subheader("📎 Documentos")
    st.dataframe(documentos, use_container_width=True)
    if not documentos.empty:
        sel = st.selectbox("Documento ID a borrar", documentos["ID"].tolist())
        if st.button("🗑️ Borrar documento (registro)"):
            documentos = documentos[documentos["ID"] != sel].copy()
            save_df("documentos", documentos)
            st.success("✅ Eliminado")
            st.rerun()

if menu == "Plantillas de Contrato":
    st.subheader("📝 Plantillas")
    st.dataframe(plantillas, use_container_width=True)
    if not plantillas.empty:
        sel = st.selectbox("Plantilla ID a borrar", plantillas["ID"].tolist())
        if st.button("🗑️ Borrar plantilla"):
            plantillas = plantillas[plantillas["ID"] != sel].copy()
            save_df("plantillas", plantillas)
            st.success("✅ Eliminado")
            st.rerun()

if menu == "Generar Contrato":
    st.subheader("📄 Generar Contrato")
    st.info("Aquí puedes ampliar el generador con placeholders. (Se mantuvo la opción.)")

if menu == "Reportes":
    st.subheader("📈 Reportes")
    df_res = resumen_financiero_df()
    st.dataframe(df_res, use_container_width=True)
    st.download_button("Descargar reporte casos (CSV)", df_res.to_csv(index=False).encode("utf-8"), "reporte_casos.csv")

if menu == "Usuarios":
    require_admin()
    st.subheader("👥 Usuarios (vinculados a abogados)")

    users = load_df("usuarios")
    st.dataframe(users[["Usuario","Rol","AbogadoID","Activo","Creado"]], use_container_width=True)

    accion = st.radio("Acción", ["Nuevo","Cambiar contraseña","Activar/Desactivar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        if abogados.empty:
            st.warning("Primero registra abogados.")
        else:
            with st.form("new_user"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                rol = st.selectbox("Rol", ["admin","abogado","asistente"])
                abogado_id = st.selectbox(
                    "Abogado asociado (ID)",
                    abogados["ID"].tolist(),
                    format_func=lambda x: abogados[abogados["ID"] == x].iloc[0]["Nombre"]
                )
                submit = st.form_submit_button("Crear")
                if submit:
                    if (users["Usuario"].astype(str) == str(u)).any():
                        st.error("Ese usuario ya existe.")
                    else:
                        users = add_row(users, {
                            "Usuario": u,
                            "PasswordHash": sha256(p),
                            "Rol": rol,
                            "AbogadoID": str(abogado_id),
                            "Activo": "1",
                            "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }, "usuarios")
                        save_df("usuarios", users)
                        st.success("✅ Usuario creado y vinculado")
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

if menu == "Auditoría (fantasmas)":
    st.subheader("🧹 Auditoría de fantasmas")
    st.info("Aquí ves registros huérfanos o duplicados. Usa Reset suave si hay montos fantasma.")

    casos_set = set(casos["Expediente"].tolist())

    def orphans(df):
        if df.empty or "Caso" not in df.columns:
            return df
        tmp = df.copy()
        tmp["Caso"] = tmp["Caso"].apply(normalize_key)
        return tmp[~tmp["Caso"].isin(casos_set)].copy()

    st.markdown("### Huérfanos: honorarios")
    st.dataframe(orphans(honorarios), use_container_width=True)
    st.markdown("### Huérfanos: pagos honorarios")
    st.dataframe(orphans(pagos_honorarios), use_container_width=True)
    st.markdown("### Huérfanos: cuota litis")
    st.dataframe(orphans(cuota_litis), use_container_width=True)
    st.markdown("### Huérfanos: pagos litis")
    st.dataframe(orphans(pagos_litis), use_container_width=True)
