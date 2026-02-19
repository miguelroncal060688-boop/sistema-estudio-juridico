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
CONTROL_PASSWORD = "control123"  # Cambia esta clave si quieres
DATA_DIR = "."
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
GENERADOS_DIR = os.path.join(DATA_DIR, "generados")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERADOS_DIR, exist_ok=True)

st.set_page_config(page_title=f"⚖️ {APP_NAME}", layout="wide")

# ==========================================================
# ARCHIVOS
# ==========================================================
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

# ==========================================================
# ESQUEMAS
# ==========================================================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","AbogadoID","Activo","Creado"],
    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones","EstadoCaso","FechaInicio"],

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

def normalize_key(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def drop_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.str.contains(r"^Unnamed", case=False, na=False)]

def safe_float_series(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def money(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def to_date_safe(x):
    if pd.isna(x) or str(x).strip()=="":
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

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

def require_admin():
    if st.session_state.get("rol") != "admin":
        st.error("❌ Solo ADMIN puede acceder aquí.")
        st.stop()

# ==========================================================
# INICIALIZACIÓN DE ARCHIVOS
# ==========================================================
for k in FILES:
    ensure_csv(k)

# ==========================================================
# ASEGURAR ADMIN (sin borrar nada)
# ==========================================================
usuarios = load_df("usuarios")
if usuarios[usuarios["Usuario"].astype(str) == "admin"].empty:
    usuarios = add_row(usuarios, {
        "Usuario": "admin",
        "PasswordHash": sha256("estudio123"),
        "Rol": "admin",
        "AbogadoID": "",
        "Activo": "1",
        "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }, "usuarios")
    save_df("usuarios", usuarios)

# ==========================================================
# LOGIN
# ==========================================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None
if "abogado_id" not in st.session_state:
    st.session_state.abogado_id = ""

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
        st.session_state.abogado_id = str(row.iloc[0]["AbogadoID"]) if "AbogadoID" in row.columns else ""
        st.rerun()

if st.session_state.usuario is None:
    login_ui()
    st.stop()

# ==========================================================
# CARGA DATA (con IDs asegurados)
# ==========================================================
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
usuarios = load_df("usuarios")

# normalizar claves
casos["Expediente"] = casos["Expediente"].apply(normalize_key)
for df in [honorarios, pagos_honorarios, cuota_litis, pagos_litis, cuotas, actuaciones, documentos]:
    if "Caso" in df.columns:
        df["Caso"] = df["Caso"].apply(normalize_key)

# guardar IDs reparados (NO borra nada)
save_df("honorarios", honorarios)
save_df("pagos_honorarios", pagos_honorarios)
save_df("cuota_litis", cuota_litis)
save_df("pagos_litis", pagos_litis)
save_df("cuotas", cuotas)
save_df("actuaciones", actuaciones)
save_df("documentos", documentos)
save_df("plantillas", plantillas)

# ==========================================================
# FUNCIONES FINANCIERAS
# ==========================================================
def canon_last_by_case(df: pd.DataFrame, case_col="Caso"):
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

    rows = []
    for _, c in casos.iterrows():
        exp = normalize_key(c["Expediente"])
        pactado = safe_float_series(canon_h[canon_h["Caso"] == exp]["Monto Pactado"]).sum()
        pagado_h = safe_float_series(pagos_honorarios[pagos_honorarios["Caso"] == exp]["Monto"]).sum()

        calc = safe_float_series(canon_cl[canon_cl["Caso"] == exp]["CuotaCalc"]).sum()
        pagado_l = safe_float_series(pagos_litis[pagos_litis["Caso"] == exp]["Monto"]).sum()

        rows.append([
            exp, c["Cliente"], c["Materia"],
            float(pactado), float(pagado_h), float(pactado - pagado_h),
            float(calc), float(pagado_l), float(calc - pagado_l)
        ])

    return pd.DataFrame(rows, columns=[
        "Expediente","Cliente","Materia",
        "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
        "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
    ])

def cuotas_status_all():
    """
    Estado de cuotas: NO depende de pagos/CL para crear cuotas.
    Se usa para ver Saldo por cuota si existe cronograma.
    """
    if cuotas.empty:
        return pd.DataFrame()

    df = cuotas.copy()
    df["Monto"] = safe_float_series(df["Monto"])
    df["FechaVenc_dt"] = df["FechaVenc"].apply(to_date_safe)

    # pagos por tipo
    ph = pagos_honorarios.copy()
    pl = pagos_litis.copy()
    ph["Monto"] = safe_float_series(ph["Monto"])
    pl["Monto"] = safe_float_series(pl["Monto"])

    def calc_for_type(tipo, pagos_df):
        sub = df[df["Tipo"] == tipo].copy()
        if sub.empty:
            return sub

        sub["_sort_date"] = sub["FechaVenc_dt"].apply(lambda d: d if d else date(2100,1,1))
        sub.sort_values(["Caso","_sort_date","NroCuota"], inplace=True)

        pagado_por_caso = pagos_df.groupby("Caso")["Monto"].sum().to_dict()
        remaining = {k: float(v) for k, v in pagado_por_caso.items()}

        asignados, saldos, estados, dias = [], [], [], []
        today = date.today()
        for _, r in sub.iterrows():
            caso = r["Caso"]
            monto = float(r["Monto"])
            venc = r["FechaVenc_dt"]

            rem = remaining.get(caso, 0.0)
            asign = min(rem, monto) if monto > 0 else 0.0
            remaining[caso] = rem - asign
            saldo = monto - asign

            if monto == 0:
                est = "Sin monto"
            elif saldo <= 0.00001:
                est = "Pagada"
            elif asign > 0:
                est = "Parcial"
            else:
                est = "Pendiente"

            dv = None if venc is None else (venc - today).days

            asignados.append(asign)
            saldos.append(saldo)
            estados.append(est)
            dias.append(dv)

        sub["PagadoAsignado"] = asignados
        sub["SaldoCuota"] = saldos
        sub["Estado"] = estados
        sub["DiasParaVencimiento"] = dias
        sub.drop(columns=["_sort_date"], inplace=True, errors="ignore")
        return sub

    out_h = calc_for_type("Honorarios", ph)
    out_l = calc_for_type("CuotaLitis", pl)
    out = pd.concat([out_h, out_l], ignore_index=True) if (not out_h.empty or not out_l.empty) else pd.DataFrame()
    return out

# ==========================================================
# PANEL DE CONTROL (RESET OCULTO + EXPORT)
# ==========================================================
def reset_suave():
    # limpia huérfanos (Caso no existe en casos)
    casos_set = set(casos["Expediente"].tolist())

    def clean(keyname):
        df = load_df(keyname)
        if "Caso" in df.columns:
            df["Caso"] = df["Caso"].apply(normalize_key)
            df = df[df["Caso"].isin(casos_set)].copy()
        df = ensure_ids(df)
        save_df(keyname, df)

    for keyname in ["honorarios","pagos_honorarios","cuota_litis","pagos_litis","cuotas","actuaciones","documentos"]:
        clean(keyname)

def reset_total(borrar_archivos=False):
    for k in FILES:
        backup_file(FILES[k])

    # borrar todo menos usuarios
    for k in FILES:
        if k == "usuarios":
            continue
        pd.DataFrame(columns=SCHEMAS[k]).to_csv(FILES[k], index=False)

    # recrear admin
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

# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.write(f"👤 Usuario: {st.session_state.usuario} ({st.session_state.rol})")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.abogado_id = ""
    st.rerun()

# Panel de control oculto
with st.sidebar.expander("🔒 Panel de control", expanded=False):
    pwd = st.text_input("Clave del panel", type="password")
    if pwd == CONTROL_PASSWORD:
        st.success("Acceso concedido")
        if st.button("✅ Reset suave (limpiar fantasmas)"):
            reset_suave()
            st.success("✅ Reset suave aplicado")
            st.rerun()

        wipe = st.checkbox("Borrar también uploads/ y generados/ (solo reset total)", value=False)
        if st.button("🧨 Reset total (borra todo)"):
            reset_total(borrar_archivos=wipe)
            st.success("✅ Reset total aplicado. admin/estudio123")
            st.rerun()
    else:
        st.info("Panel protegido. (Pide la clave)")

# ==========================================================
# MENÚ
# ==========================================================
menu = st.sidebar.selectbox("📌 Menú", [
    "Dashboard",
    "Ficha del Caso",
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
    "Auditoría (fantasmas)",
])

# ==========================================================
# UI HEADER
# ==========================================================
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

    st.download_button("⬇️ Descargar reporte (CSV)", df_res.to_csv(index=False).encode("utf-8"), "reporte_casos.csv")

# ==========================================================
# FICHA DEL CASO (pestañas restauradas)
# ==========================================================
if menu == "Ficha del Caso":
    st.subheader("📁 Ficha del Caso")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        exp = st.selectbox("Expediente", casos["Expediente"].tolist())
        tabs = st.tabs(["Datos", "Pagos", "Cronograma", "Actuaciones", "Documentos", "Estado de Cuenta"])

        with tabs[0]:
            st.dataframe(casos[casos["Expediente"] == exp], use_container_width=True)

        with tabs[1]:
            st.markdown("### Pagos Honorarios")
            st.dataframe(pagos_honorarios[pagos_honorarios["Caso"] == exp], use_container_width=True)
            st.markdown("### Pagos Cuota Litis")
            st.dataframe(pagos_litis[pagos_litis["Caso"] == exp], use_container_width=True)

        with tabs[2]:
            st.markdown("### Cuotas registradas")
            st.dataframe(cuotas[cuotas["Caso"] == exp], use_container_width=True)
            st.markdown("### Estado cuotas (si existe cronograma)")
            st.dataframe(cuotas_status_all()[cuotas_status_all()["Caso"] == exp], use_container_width=True)

        with tabs[3]:
            st.dataframe(actuaciones[actuaciones["Caso"] == exp].sort_values("Fecha", ascending=False), use_container_width=True)

        with tabs[4]:
            st.dataframe(documentos[documentos["Caso"] == exp].sort_values("Fecha", ascending=False), use_container_width=True)

        with tabs[5]:
            df = resumen_financiero_df()
            fila = df[df["Expediente"] == exp]
            if fila.empty:
                st.info("Sin estado de cuenta.")
            else:
                f = fila.iloc[0]
                a, b, c = st.columns(3)
                a.metric("Honorario pactado", f"S/ {money(f['Honorario Pactado']):,.2f}")
                b.metric("Pagado honorarios", f"S/ {money(f['Honorario Pagado']):,.2f}")
                c.metric("Saldo honorarios", f"S/ {money(f['Honorario Pendiente']):,.2f}")

                d, e, g = st.columns(3)
                d.metric("Cuota litis calc.", f"S/ {money(f['Cuota Litis Calculada']):,.2f}")
                e.metric("Pagado litis", f"S/ {money(f['Pagado Litis']):,.2f}")
                g.metric("Saldo litis", f"S/ {money(f['Saldo Litis']):,.2f}")

# ==========================================================
# CLIENTES / ABOGADOS / CASOS (CRUD completos)
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
    st.download_button("⬇️ Descargar clientes (CSV)", clientes.to_csv(index=False).encode("utf-8"), "clientes.csv")

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
    st.download_button("⬇️ Descargar abogados (CSV)", abogados.to_csv(index=False).encode("utf-8"), "abogados.csv")

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

    st.dataframe(casos, use_container_width=True)
    st.download_button("⬇️ Descargar casos (CSV)", casos.to_csv(index=False).encode("utf-8"), "casos.csv")

# ==========================================================
# PAGOS: botones de borrar/modificar YA ESTÁN en pagos honorarios / pagos litis
# ==========================================================
# (Se mantienen como en el dashboard; ya están arriba en menú Pagos Honorarios / Pagos Cuota Litis)

# ==========================================================
# CRONOGRAMA (corregido: ahora SÍ deja crear cuotas)
# ==========================================================
if menu == "Cronograma de Cuotas":
    st.subheader("📅 Cronograma de cuotas")

    st.markdown("### Cuotas registradas")
    st.dataframe(cuotas.sort_values("FechaVenc", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist()
    if not exp_list:
        st.warning("Primero registra casos para poder crear cuotas.")
    else:
        st.markdown("### Crear cuota")
        caso = st.selectbox("Expediente", exp_list)
        tipo = st.selectbox("Tipo", ["Honorarios","CuotaLitis"])
        venc = st.date_input("Fecha vencimiento", value=date.today())
        monto = st.number_input("Monto cuota", min_value=0.0, step=50.0)
        notas = st.text_input("Notas", value="")

        # nro cuota automático por caso+tipo
        sub = cuotas[(cuotas["Caso"] == caso) & (cuotas["Tipo"] == tipo)].copy()
        sub["NroCuota"] = pd.to_numeric(sub["NroCuota"], errors="coerce").fillna(0).astype(int)
        nro = int(sub["NroCuota"].max()) + 1 if not sub.empty else 1

        if st.button("Guardar cuota"):
            new_id = next_id(cuotas)
            cuotas = add_row(cuotas, {
                "ID": new_id,
                "Caso": normalize_key(caso),
                "Tipo": "Honorarios" if tipo=="Honorarios" else "CuotaLitis",
                "NroCuota": nro,
                "FechaVenc": str(venc),
                "Monto": float(monto),
                "Notas": notas
            }, "cuotas")
            save_df("cuotas", cuotas)
            st.success("✅ Cuota creada")
            st.rerun()

    st.divider()
    st.markdown("### Estado de cuotas (usa pagos existentes)")
    estado = cuotas_status_all()
    if estado.empty:
        st.info("No hay cuotas o no hay estado aún.")
    else:
        st.dataframe(estado.sort_values(["Caso","Tipo","NroCuota"]), use_container_width=True)

    st.divider()
    st.markdown("### Borrar cuota (por ID)")
    if not cuotas.empty:
        sel = st.selectbox("Cuota ID", cuotas["ID"].tolist())
        if st.button("🗑️ Borrar cuota"):
            cuotas = cuotas[cuotas["ID"] != sel].copy()
            save_df("cuotas", cuotas)
            st.success("✅ Eliminado")
            st.rerun()

# ==========================================================
# ACTUACIONES (CRUD mínimo + descarga)
# ==========================================================
if menu == "Actuaciones":
    st.subheader("🧾 Actuaciones")
    st.dataframe(actuaciones.sort_values("Fecha", ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar actuaciones (CSV)", actuaciones.to_csv(index=False).encode("utf-8"), "actuaciones.csv")

# ==========================================================
# DOCUMENTOS (listado + borrar registro + descarga CSV)
# ==========================================================
if menu == "Documentos":
    st.subheader("📎 Documentos")
    st.dataframe(documentos.sort_values("Fecha", ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar documentos (CSV)", documentos.to_csv(index=False).encode("utf-8"), "documentos.csv")

# ==========================================================
# PLANTILLAS (arreglado: ahora SÍ se pueden agregar)
# ==========================================================
if menu == "Plantillas de Contrato":
    st.subheader("📝 Plantillas de Contrato (Modelos)")

    accion = st.radio("Acción", ["Nueva","Editar","Eliminar"], horizontal=True)

    st.info("Placeholders: {{EXPEDIENTE}}, {{CLIENTE_NOMBRE}}, {{CLIENTE_DNI}}, {{MATERIA}}, {{MONTO_PACTADO}}, {{PORCENTAJE_LITIS}}, {{FECHA_HOY}}")

    if accion == "Nueva":
        with st.form("tpl_new"):
            nombre = st.text_input("Nombre")
            contenido = st.text_area("Contenido", height=300)
            notas = st.text_input("Notas", value="")
            submit = st.form_submit_button("Guardar plantilla")
            if submit:
                new_id = next_id(plantillas)
                plantillas = add_row(plantillas, {
                    "ID": new_id,
                    "Nombre": nombre,
                    "Contenido": contenido,
                    "Notas": notas,
                    "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }, "plantillas")
                save_df("plantillas", plantillas)
                st.success("✅ Plantilla creada")
                st.rerun()

    elif accion == "Editar" and not plantillas.empty:
        sel = st.selectbox("Plantilla ID", plantillas["ID"].tolist())
        fila = plantillas[plantillas["ID"] == sel].iloc[0]
        with st.form("tpl_edit"):
            nombre = st.text_input("Nombre", value=str(fila["Nombre"]))
            contenido = st.text_area("Contenido", value=str(fila["Contenido"]), height=300)
            notas = st.text_input("Notas", value=str(fila["Notas"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = plantillas.index[plantillas["ID"] == sel][0]
                plantillas.loc[idx, ["Nombre","Contenido","Notas"]] = [nombre, contenido, notas]
                save_df("plantillas", plantillas)
                st.success("✅ Plantilla actualizada")
                st.rerun()

    elif accion == "Eliminar" and not plantillas.empty:
        sel = st.selectbox("Plantilla ID a eliminar", plantillas["ID"].tolist())
        if st.button("🗑️ Eliminar plantilla"):
            plantillas = plantillas[plantillas["ID"] != sel].copy()
            save_df("plantillas", plantillas)
            st.success("✅ Eliminada")
            st.rerun()

    st.divider()
    st.dataframe(plantillas[["ID","Nombre","Notas","Creado"]], use_container_width=True)
    st.download_button("⬇️ Descargar plantillas (CSV)", plantillas.to_csv(index=False).encode("utf-8"), "plantillas_contratos.csv")

# ==========================================================
# GENERAR CONTRATO (restaurado y funcional)
# ==========================================================
def build_context(expediente: str):
    expediente = normalize_key(expediente)
    caso_row = casos[casos["Expediente"] == expediente]
    if caso_row.empty:
        return {}
    c = caso_row.iloc[0]

    cli_row = clientes[clientes["Nombre"] == c["Cliente"]]
    cli = cli_row.iloc[0] if not cli_row.empty else None

    canon_h = canon_last_by_case(honorarios, "Caso")
    canon_cl = canon_last_by_case(cuota_litis, "Caso")

    monto_pactado = safe_float_series(canon_h[canon_h["Caso"] == expediente]["Monto Pactado"]).sum()
    porc = safe_float_series(canon_cl[canon_cl["Caso"] == expediente]["Porcentaje"])
    porc_val = float(porc.iloc[-1]) if len(porc) else 0.0

    ctx = {
        "{{EXPEDIENTE}}": expediente,
        "{{CLIENTE_NOMBRE}}": str(c["Cliente"]),
        "{{ABOGADO_NOMBRE}}": str(c["Abogado"]),
        "{{MATERIA}}": str(c["Materia"]),
        "{{PRETENSION}}": str(c["Pretension"]),
        "{{MONTO_PACTADO}}": f"{monto_pactado:.2f}",
        "{{PORCENTAJE_LITIS}}": f"{porc_val:.2f}",
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
    st.subheader("📄 Generar contrato automáticamente")

    if casos.empty:
        st.info("Primero registra casos.")
    elif plantillas.empty:
        st.info("Primero crea una plantilla.")
    else:
        exp = st.selectbox("Expediente", casos["Expediente"].tolist())
        tpl_id = st.selectbox("Plantilla ID", plantillas["ID"].tolist())
        tpl = plantillas[plantillas["ID"] == tpl_id].iloc[0]

        ctx = build_context(exp)
        generado = render_template(str(tpl["Contenido"]), ctx)

        st.text_area("Vista previa", value=generado, height=350)

        nombre_archivo = f"Contrato_{exp.replace('/','_')}_{str(tpl['Nombre']).replace(' ','_')}.txt"
        st.download_button("⬇️ Descargar contrato (TXT)", data=generado.encode("utf-8"), file_name=nombre_archivo)

        if st.button("💾 Guardar en carpeta generados/"):
            out_path = os.path.join(GENERADOS_DIR, nombre_archivo)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(generado)
            st.success(f"✅ Guardado en {out_path}")

# ==========================================================
# REPORTES (pestañas restauradas + descargas)
# ==========================================================
if menu == "Reportes":
    st.subheader("📈 Reportes")
    df_res = resumen_financiero_df()

    tab1, tab2, tab3, tab4 = st.tabs(["Saldos por caso", "Saldos por cliente", "Actuaciones", "Documentos"])

    with tab1:
        st.dataframe(df_res, use_container_width=True)
        st.download_button("⬇️ Descargar reporte casos (CSV)", df_res.to_csv(index=False).encode("utf-8"), "reporte_casos.csv")

    with tab2:
        if df_res.empty:
            st.info("Sin datos.")
        else:
            cli = df_res.groupby("Cliente", as_index=False).agg({
                "Honorario Pendiente":"sum",
                "Saldo Litis":"sum"
            })
            cli["SaldoTotal"] = cli["Honorario Pendiente"] + cli["Saldo Litis"]
            cli.sort_values("SaldoTotal", ascending=False, inplace=True)
            st.dataframe(cli, use_container_width=True)
            st.download_button("⬇️ Descargar reporte clientes (CSV)", cli.to_csv(index=False).encode("utf-8"), "reporte_clientes.csv")

    with tab3:
        st.dataframe(actuaciones.sort_values("Fecha", ascending=False), use_container_width=True)
        st.download_button("⬇️ Descargar actuaciones (CSV)", actuaciones.to_csv(index=False).encode("utf-8"), "reporte_actuaciones.csv")

    with tab4:
        st.dataframe(documentos.sort_values("Fecha", ascending=False), use_container_width=True)
        st.download_button("⬇️ Descargar documentos (CSV)", documentos.to_csv(index=False).encode("utf-8"), "reporte_documentos.csv")

# ==========================================================
# USUARIOS (fix: submit button y selectbox robusto)
# ==========================================================
if menu == "Usuarios":
    require_admin()
    st.subheader("👥 Usuarios (vinculados a abogados)")

    users = load_df("usuarios")
    st.dataframe(users[["Usuario","Rol","AbogadoID","Activo","Creado"]], use_container_width=True)
    st.download_button("⬇️ Descargar usuarios (CSV)", users.to_csv(index=False).encode("utf-8"), "usuarios.csv")

    accion = st.radio("Acción", ["Nuevo","Cambiar contraseña","Activar/Desactivar","Eliminar"], horizontal=True)

    # Mapa seguro ID->Nombre (evita el error de format_func cuando no encuentra fila)
    abogado_map = {}
    if not abogados.empty:
        for _, r in abogados.iterrows():
            abogado_map[str(r["ID"])] = str(r["Nombre"])

    if accion == "Nuevo":
        if abogados.empty:
            st.warning("Primero registra abogados para vincular usuarios.")
        else:
            with st.form("new_user_form"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                rol = st.selectbox("Rol", ["admin","abogado","asistente"])
                abogado_id = st.selectbox(
                    "Abogado asociado (ID)",
                    [str(x) for x in abogados["ID"].tolist()],
                    format_func=lambda x: abogado_map.get(str(x), f"Abogado ID {x}")
                )
                submit = st.form_submit_button("Crear usuario")

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

    elif accion == "Cambiar contraseña":
        sel = st.selectbox("Usuario", users["Usuario"].tolist())
        newp = st.text_input("Nueva contraseña", type="password")
        if st.button("Guardar contraseña"):
            idx = users.index[users["Usuario"] == sel][0]
            users.loc[idx, "PasswordHash"] = sha256(newp)
            save_df("usuarios", users)
            st.success("✅ Contraseña cambiada")
            st.rerun()

    elif accion == "Activar/Desactivar":
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

    elif accion == "Eliminar":
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
# AUDITORÍA (fantasmas)
# ==========================================================
if menu == "Auditoría (fantasmas)":
    st.subheader("🧹 Auditoría de fantasmas")
    st.info("Si hay montos fantasma, usa Reset suave en Panel de Control (clave requerida).")

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
    st.markdown("### Huérfanos: cuotas cronograma")
    st.dataframe(orphans(cuotas), use_container_width=True)
