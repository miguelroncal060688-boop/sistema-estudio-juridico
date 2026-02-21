import streamlit as st
import pandas as pd
import os
import hashlib
import shutil
from datetime import date, datetime

# ==========================================================
# MARCA 004 – VERSIÓN ESTABLE OPERATIVA
# Estado: FUNCIONA TODO – NO MODIFICAR NI REDUCIR
# Añadidos: Edit/Borrar Honorarios + Ficha/Historial Actuaciones (con link OneDrive)
#           + Módulo Consultas (con proforma e historial)
# ==========================================================
APP_VERSION = "MARCA 004"

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================
APP_NAME = "Estudio Jurídico Roncal Liñan y Asociados"
# ✅ Leer credenciales desde Secrets (Streamlit Cloud)
CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")  # panel de control (fallback local)
ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")  # admin inicial (fallback)
PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")  # opcional (mejora hash)

DATA_DIR = "."
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
GENERADOS_DIR = os.path.join(DATA_DIR, "generados")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(GENERADOS_DIR, exist_ok=True)

st.set_page_config(page_title=f"⚖️ {APP_NAME} – {APP_VERSION}", layout="wide")

# ==========================================================
# ARCHIVOS
# ==========================================================
FILES = {
    "usuarios": "usuarios.csv",
    "clientes": "clientes.csv",
    "abogados": "abogados.csv",
    "casos": "casos.csv",

    "honorarios": "honorarios.csv",
    "honorarios_etapas": "honorarios_etapas.csv",

    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",

    "cuotas": "cuotas.csv",
    "actuaciones": "actuaciones.csv",
    "documentos": "documentos.csv",
    "plantillas": "plantillas_contratos.csv",

    # ✅ NUEVO: consultas
    "consultas": "consultas.csv",
}

# ==========================================================
# ESQUEMAS
# ==========================================================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","AbogadoID","Activo","Creado"],
    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Instancia","Pretension","Observaciones","EstadoCaso","FechaInicio"],

    "honorarios": ["ID","Caso","Monto Pactado","Notas","FechaRegistro"],
    "honorarios_etapas": ["ID","Caso","Etapa","Monto Pactado","Notas","FechaRegistro"],

    # ✅ pagos honorarios por etapa (si venía antiguo, se migra)
    "pagos_honorarios": ["ID","Caso","Etapa","FechaPago","Monto","Observacion"],

    "cuota_litis": ["ID","Caso","Monto Base","Porcentaje","Notas","FechaRegistro"],
    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],

    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"],

    # ✅ ACTUACIONES: agrego Cliente y LinkOneDrive (sin romper datos antiguos)
    "actuaciones": ["ID","Caso","Cliente","Fecha","TipoActuacion","Resumen","ProximaAccion","FechaProximaAccion","LinkOneDrive","Notas"],

    "documentos": ["ID","Caso","Tipo","NombreArchivo","Ruta","Fecha","Notas"],
    "plantillas": ["ID","Nombre","Contenido","Notas","Creado"],

    # ✅ CONSULTAS: nuevo módulo
    "consultas": ["ID","Fecha","Cliente","Caso","Consulta","Estrategia","HonorariosPropuestos","Proforma","LinkOneDrive","Notas"],
}

ETAPAS_HONORARIOS = ["Primera instancia", "Segunda instancia", "Casación", "Otros"]
TIPOS_CUOTA = ["Honorarios", "CuotaLitis"]

# ==========================================================
# UTILIDADES
# ==========================================================
# ✅ Esta variable debe existir (la definiremos en el cambio B)
# PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")

def sha256(text: str) -> str:
    base = (PASSWORD_PEPPER or "") + str(text)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

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

# ==========================================================
# ensure_csv (NO destruye datos; guarda corrupto antes)
# ==========================================================
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
        try:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(path, os.path.join(BACKUP_DIR, f"{os.path.basename(path)}.{stamp}.corrupt.bak"))
        except Exception:
            pass
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    df = drop_unnamed(df)

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df = df.reindex(columns=cols)
    df.to_csv(path, index=False)

# ==========================================================
# load_df (migraciones suaves)
# ==========================================================
def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    try:
        df = pd.read_csv(FILES[key])
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=SCHEMAS[key])

    df = drop_unnamed(df)

    # Migración actuaciones si venían con nombres antiguos
    if key == "actuaciones":
        rename_map = {
            "ActuaciónID": "ID",
            "CasoID": "Caso",
            "TipoActuación": "TipoActuacion",
            "PróximaAcción": "ProximaAccion",
            "FechaPróximaAcción": "FechaProximaAccion",
            "Link": "LinkOneDrive",
            "Enlace": "LinkOneDrive",
        }
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # Migración pagos_honorarios si era esquema antiguo sin Etapa
    if key == "pagos_honorarios":
        if "Etapa" not in df.columns:
            df["Etapa"] = ""

    # Migración casos: si no existía Instancia
    if key == "casos":
        if "Instancia" not in df.columns:
            df["Instancia"] = ""

    # Migración consultas si existiera algo previo
    if key == "consultas":
        for col in SCHEMAS["consultas"]:
            if col not in df.columns:
                df[col] = ""

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
    st.caption(f"Versión: {APP_VERSION}")

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
        "PasswordHash": sha256(ADMIN_BOOTSTRAP_PASSWORD),
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

    u = st.text_input(
    "Usuario",
    value="",
    key="login_user",
    placeholder="Escribe tu usuario",
    autocomplete="off"
)
p = st.text_input(
    "Contraseña",
    value="",
    key="login_pass",
    type="password",
    placeholder="Escribe tu contraseña",
    autocomplete="new-password"
)

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
honorarios_etapas = ensure_ids(load_df("honorarios_etapas"))
pagos_honorarios = ensure_ids(load_df("pagos_honorarios"))

cuota_litis = ensure_ids(load_df("cuota_litis"))
pagos_litis = ensure_ids(load_df("pagos_litis"))

cuotas = ensure_ids(load_df("cuotas"))
actuaciones = ensure_ids(load_df("actuaciones"))
documentos = ensure_ids(load_df("documentos"))
plantillas = ensure_ids(load_df("plantillas"))
consultas = ensure_ids(load_df("consultas"))
usuarios = load_df("usuarios")

# normalizar claves
if "Expediente" in casos.columns:
    casos["Expediente"] = casos["Expediente"].apply(normalize_key)

for df in [honorarios, honorarios_etapas, pagos_honorarios, cuota_litis, pagos_litis, cuotas, actuaciones, documentos]:
    if "Caso" in df.columns:
        df["Caso"] = df["Caso"].apply(normalize_key)

# normalizar Tipo de cuotas si venía con espacios
if not cuotas.empty and "Tipo" in cuotas.columns:
    cuotas["Tipo"] = cuotas["Tipo"].astype(str).str.replace(" ", "", regex=False)
    cuotas["Tipo"] = cuotas["Tipo"].replace({"CuotaLitis":"CuotaLitis","Honorarios":"Honorarios"})
    save_df("cuotas", cuotas)

# guardar IDs reparados (NO borra nada)
save_df("honorarios", honorarios)
save_df("honorarios_etapas", honorarios_etapas)
save_df("pagos_honorarios", pagos_honorarios)
save_df("cuota_litis", cuota_litis)
save_df("pagos_litis", pagos_litis)
save_df("cuotas", cuotas)
save_df("actuaciones", actuaciones)
save_df("documentos", documentos)
save_df("plantillas", plantillas)
save_df("consultas", consultas)

# ==========================================================
# FINANZAS
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

        etapas_exp = honorarios_etapas[honorarios_etapas["Caso"] == exp].copy()
        if not etapas_exp.empty:
            pactado = safe_float_series(etapas_exp["Monto Pactado"]).sum()
        else:
            pactado = safe_float_series(canon_h[canon_h["Caso"] == exp]["Monto Pactado"]).sum()

        pagado_h = safe_float_series(pagos_honorarios[pagos_honorarios["Caso"] == exp]["Monto"]).sum()

        calc = safe_float_series(canon_cl[canon_cl["Caso"] == exp]["CuotaCalc"]).sum()
        pagado_l = safe_float_series(pagos_litis[pagos_litis["Caso"] == exp]["Monto"]).sum()

        rows.append([
            exp, c.get("Cliente",""), c.get("Materia",""),
            float(pactado), float(pagado_h), float(pactado - pagado_h),
            float(calc), float(pagado_l), float(calc - pagado_l)
        ])

    return pd.DataFrame(rows, columns=[
        "Expediente","Cliente","Materia",
        "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
        "Cuota Litis Calculada","Pagado Litis","Saldo Litis"
    ])

def cuotas_status_all():
    if cuotas.empty:
        return pd.DataFrame()

    df = cuotas.copy()
    df["Monto"] = safe_float_series(df["Monto"])
    df["FechaVenc_dt"] = df["FechaVenc"].apply(to_date_safe)

    ph = pagos_honorarios.copy()
    pl = pagos_litis.copy()
    ph["Monto"] = safe_float_series(ph["Monto"])
    pl["Monto"] = safe_float_series(pl["Monto"])

    def calc_for_type(tipo, pagos_df):
        sub = df[df["Tipo"] == tipo].copy()
        if sub.empty:
            return sub

        sub["_sort_date"] = sub["FechaVenc_dt"].apply(lambda d: d if d else date(2100,1,1))
        sub["NroCuota"] = pd.to_numeric(sub["NroCuota"], errors="coerce").fillna(0).astype(int)
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
            asignados.append(asign); saldos.append(saldo); estados.append(est); dias.append(dv)

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
# PANEL DE CONTROL (RESET OCULTO)
# ==========================================================
def reset_suave():
    casos_set = set(casos["Expediente"].tolist())

    def clean(keyname):
        df = load_df(keyname)
        if "Caso" in df.columns:
            df["Caso"] = df["Caso"].apply(normalize_key)
            df = df[df["Caso"].isin(casos_set)].copy()
        df = ensure_ids(df)
        save_df(keyname, df)

    for keyname in ["honorarios","honorarios_etapas","pagos_honorarios","cuota_litis","pagos_litis","cuotas","actuaciones","documentos","consultas"]:
        clean(keyname)

def reset_total(borrar_archivos=False):
    for k in FILES:
        backup_file(FILES[k])

    for k in FILES:
        if k == "usuarios":
            continue
        pd.DataFrame(columns=SCHEMAS[k]).to_csv(FILES[k], index=False)

    users = pd.DataFrame(columns=SCHEMAS["usuarios"])
    users = pd.concat([users, pd.DataFrame([{
        "Usuario":"admin",
        "PasswordHash": sha256(ADMIN_BOOTSTRAP_PASSWORD)
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
st.sidebar.markdown(f"### 🏷️ {APP_VERSION}")
st.sidebar.write(f"👤 Usuario: {st.session_state.usuario} ({st.session_state.rol})")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.abogado_id = ""
    st.rerun()

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
            st.success("✅ Reset total aplicado. Usuario: admin. Contraseña: la configurada en Secrets.")
            st.rerun()
    else:
        st.info("Panel protegido. (Pide la clave)")

# ==========================================================
# MENÚ MARCA 004 (sin reducir)
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
    "Consultas",
    "Documentos",
    "Plantillas de Contrato",
    "Generar Contrato",
    "Usuarios",
    "Reportes",
    "Auditoría",
])

# ==========================================================
# UI HEADER
# ==========================================================
brand_header()

# ==========================================================
# DASHBOARD COMPLETO
# ==========================================================
if menu == "Dashboard":
    df_res = resumen_financiero_df()
    df_estado = cuotas_status_all()

    total_pactado = df_res["Honorario Pactado"].sum() if not df_res.empty else 0
    total_pagado_h = df_res["Honorario Pagado"].sum() if not df_res.empty else 0
    total_pend_h = df_res["Honorario Pendiente"].sum() if not df_res.empty else 0

    total_litis = df_res["Cuota Litis Calculada"].sum() if not df_res.empty else 0
    total_pagado_l = df_res["Pagado Litis"].sum() if not df_res.empty else 0
    total_pend_l = df_res["Saldo Litis"].sum() if not df_res.empty else 0

    st.subheader("📊 Dashboard General")

    r1c1, r1c2, r1c3 = st.columns(3)
    r1c1.metric("👥 Clientes", f"{len(clientes)}")
    r1c2.metric("👨‍⚖️ Abogados", f"{len(abogados)}")
    r1c3.metric("📁 Casos", f"{len(casos)}")

    st.markdown("### 💰 Indicadores Económicos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Honorarios pactados (S/)", f"{total_pactado:,.2f}")
    c2.metric("Honorarios pagados (S/)", f"{total_pagado_h:,.2f}")
    c3.metric("Honorarios pendientes (S/)", f"{total_pend_h:,.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Cuota litis calculada (S/)", f"{total_litis:,.2f}")
    c5.metric("Cuota litis pagada (S/)", f"{total_pagado_l:,.2f}")
    c6.metric("Cuota litis pendiente (S/)", f"{total_pend_l:,.2f}")

    st.divider()
    st.markdown("### 📌 Detalle por caso")
    st.dataframe(df_res, use_container_width=True)

    st.divider()
    st.markdown("### 📅 Cuotas vencidas / por vencer")
    if df_estado.empty or "SaldoCuota" not in df_estado.columns:
        st.info("Aún no hay cronograma calculable.")
    else:
        df_pend = df_estado[safe_float_series(df_estado["SaldoCuota"]) > 0].copy()
        vencidas = df_pend[df_pend["DiasParaVencimiento"].notna() & (df_pend["DiasParaVencimiento"] < 0)]
        por_vencer = df_pend[df_pend["DiasParaVencimiento"].notna() & (df_pend["DiasParaVencimiento"].between(0, 7))]
        st.markdown("**Vencidas**")
        st.dataframe(vencidas, use_container_width=True)
        st.markdown("**Por vencer (7 días)**")
        st.dataframe(por_vencer, use_container_width=True)

    st.download_button("⬇️ Descargar reporte casos (CSV)", df_res.to_csv(index=False).encode("utf-8"), "reporte_casos.csv")

# ==========================================================
# FICHA DEL CASO (sin cambios)
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
            estado_cuotas = cuotas_status_all()
            if estado_cuotas is None or estado_cuotas.empty or "Caso" not in estado_cuotas.columns:
                st.info("No hay estado de cuotas disponible.")
            else:
                st.dataframe(estado_cuotas[estado_cuotas["Caso"] == exp], use_container_width=True)

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

# ==========================================================
# CASOS (CRUD) — incluye Instancia
# ==========================================================
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
                instancia = st.selectbox("Instancia", ETAPAS_HONORARIOS)
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
                        "Instancia": instancia,
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
# HONORARIOS (Total + Por etapa) + ✅ EDITAR/BORRAR
# ==========================================================
if menu == "Honorarios":
    st.subheader("🧾 Honorarios")

    tab_total, tab_etapas = st.tabs(["Total (como siempre)", "Por etapa (nuevo)"])

    with tab_total:
        st.markdown("### Honorario total")
        st.dataframe(honorarios.sort_values("ID", ascending=False), use_container_width=True)

        exp_list = casos["Expediente"].tolist()
        if exp_list:
            exp = st.selectbox("Expediente", exp_list, key="hon_total_exp")
            monto = st.number_input("Monto pactado (total)", min_value=0.0, step=50.0, key="hon_total_monto")
            notas = st.text_input("Notas", value="", key="hon_total_notas")
            if st.button("Guardar honorario total"):
                new_id = next_id(honorarios)
                honorarios = add_row(honorarios, {
                    "ID": new_id, "Caso": normalize_key(exp),
                    "Monto Pactado": float(monto), "Notas": notas,
                    "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, "honorarios")
                save_df("honorarios", honorarios)
                st.success("✅ Guardado")
                st.rerun()

        st.divider()
        st.markdown("### Editar / borrar honorario total (por ID)")
        if not honorarios.empty:
            sel = st.selectbox("Honorario ID", honorarios["ID"].tolist(), key="hon_total_sel")
            fila = honorarios[honorarios["ID"] == sel].iloc[0]
            with st.form("hon_total_edit"):
                caso_e = st.text_input("Caso (Expediente)", value=str(fila["Caso"]))
                monto_e = st.number_input("Monto Pactado", min_value=0.0, value=money(fila["Monto Pactado"]), step=50.0)
                notas_e = st.text_input("Notas", value=str(fila["Notas"]))
                submit = st.form_submit_button("Guardar cambios")
                if submit:
                    idx = honorarios.index[honorarios["ID"] == sel][0]
                    honorarios.loc[idx, ["Caso","Monto Pactado","Notas"]] = [normalize_key(caso_e), float(monto_e), notas_e]
                    save_df("honorarios", honorarios)
                    st.success("✅ Actualizado")
                    st.rerun()
            if st.button("🗑️ Borrar honorario total", key="hon_total_del"):
                honorarios = honorarios[honorarios["ID"] != sel].copy()
                save_df("honorarios", honorarios)
                st.success("✅ Eliminado")
                st.rerun()

        st.download_button("⬇️ Descargar honorarios total (CSV)", honorarios.to_csv(index=False).encode("utf-8"), "honorarios.csv")

    with tab_etapas:
        st.markdown("### Honorarios por etapa")
        st.dataframe(honorarios_etapas.sort_values("ID", ascending=False), use_container_width=True)

        exp_list = casos["Expediente"].tolist()
        if exp_list:
            exp = st.selectbox("Expediente", exp_list, key="hon_et_exp")
            etapa = st.selectbox("Etapa", ETAPAS_HONORARIOS, key="hon_et_etapa")
            monto = st.number_input("Monto pactado (etapa)", min_value=0.0, step=50.0, key="hon_et_monto")
            notas = st.text_input("Notas", value="", key="hon_et_notas")

            if st.button("Guardar honorario por etapa"):
                new_id = next_id(honorarios_etapas)
                honorarios_etapas = add_row(honorarios_etapas, {
                    "ID": new_id,
                    "Caso": normalize_key(exp),
                    "Etapa": etapa,
                    "Monto Pactado": float(monto),
                    "Notas": notas,
                    "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, "honorarios_etapas")
                save_df("honorarios_etapas", honorarios_etapas)
                st.success("✅ Guardado por etapa")
                st.rerun()

        st.divider()
        st.markdown("### Editar / borrar honorario por etapa (por ID)")
        if not honorarios_etapas.empty:
            sel = st.selectbox("Honorario Etapa ID", honorarios_etapas["ID"].tolist(), key="hon_et_sel")
            fila = honorarios_etapas[honorarios_etapas["ID"] == sel].iloc[0]
            with st.form("hon_et_edit"):
                caso_e = st.text_input("Caso (Expediente)", value=str(fila["Caso"]))
                etapa_e = st.selectbox("Etapa", ETAPAS_HONORARIOS, index=ETAPAS_HONORARIOS.index(fila["Etapa"]) if fila["Etapa"] in ETAPAS_HONORARIOS else 0)
                monto_e = st.number_input("Monto Pactado", min_value=0.0, value=money(fila["Monto Pactado"]), step=50.0)
                notas_e = st.text_input("Notas", value=str(fila["Notas"]))
                submit = st.form_submit_button("Guardar cambios")
                if submit:
                    idx = honorarios_etapas.index[honorarios_etapas["ID"] == sel][0]
                    honorarios_etapas.loc[idx, ["Caso","Etapa","Monto Pactado","Notas"]] = [normalize_key(caso_e), etapa_e, float(monto_e), notas_e]
                    save_df("honorarios_etapas", honorarios_etapas)
                    st.success("✅ Actualizado")
                    st.rerun()
            if st.button("🗑️ Borrar honorario por etapa", key="hon_et_del"):
                honorarios_etapas = honorarios_etapas[honorarios_etapas["ID"] != sel].copy()
                save_df("honorarios_etapas", honorarios_etapas)
                st.success("✅ Eliminado")
                st.rerun()

        st.download_button("⬇️ Descargar honorarios por etapa (CSV)", honorarios_etapas.to_csv(index=False).encode("utf-8"), "honorarios_etapas.csv")

# ==========================================================
# PAGOS HONORARIOS (por etapa + editar/borrar)
# ==========================================================
if menu == "Pagos Honorarios":
    st.subheader("💳 Pagos Honorarios (con etapa)")
    st.dataframe(pagos_honorarios.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist()
    if exp_list:
        exp = st.selectbox("Expediente", exp_list, key="ph_exp")
        etapa = st.selectbox("Etapa", ETAPAS_HONORARIOS, key="ph_etapa")
        fecha = st.date_input("Fecha pago", value=date.today(), key="ph_fecha")
        monto = st.number_input("Monto pagado", min_value=0.0, step=50.0, key="ph_monto")
        obs = st.text_input("Observación", value="", key="ph_obs")

        if st.button("Registrar pago honorarios"):
            new_id = next_id(pagos_honorarios)
            pagos_honorarios = add_row(pagos_honorarios, {
                "ID": new_id, "Caso": normalize_key(exp), "Etapa": etapa,
                "FechaPago": str(fecha), "Monto": float(monto), "Observacion": obs
            }, "pagos_honorarios")
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Pago registrado")
            st.rerun()

    st.divider()
    st.markdown("### Editar / borrar pago (por ID)")
    if not pagos_honorarios.empty:
        sel = st.selectbox("Pago ID", pagos_honorarios["ID"].tolist(), key="ph_sel")
        fila = pagos_honorarios[pagos_honorarios["ID"] == sel].iloc[0]

        with st.form("ph_edit_form"):
            exp_e = st.selectbox("Expediente", exp_list, index=exp_list.index(fila["Caso"]) if fila["Caso"] in exp_list else 0)
            etapa_e = st.selectbox("Etapa", ETAPAS_HONORARIOS, index=ETAPAS_HONORARIOS.index(fila["Etapa"]) if fila["Etapa"] in ETAPAS_HONORARIOS else 0)
            fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
            obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = pagos_honorarios.index[pagos_honorarios["ID"] == sel][0]
                pagos_honorarios.loc[idx, :] = [sel, normalize_key(exp_e), etapa_e, fecha_e, float(monto_e), obs_e]
                save_df("pagos_honorarios", pagos_honorarios)
                st.success("✅ Actualizado")
                st.rerun()

        if st.button("🗑️ Borrar pago honorarios", key="ph_del"):
            pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Eliminado")
            st.rerun()

    st.download_button("⬇️ Descargar pagos honorarios (CSV)", pagos_honorarios.to_csv(index=False).encode("utf-8"), "pagos_honorarios.csv")

# ==========================================================
# CUOTA LITIS
# ==========================================================
if menu == "Cuota Litis":
    st.subheader("⚖️ Cuota Litis")
    st.dataframe(cuota_litis.sort_values("ID", ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar cuota litis (CSV)", cuota_litis.to_csv(index=False).encode("utf-8"), "cuota_litis.csv")

# ==========================================================
# PAGOS CUOTA LITIS (editar/borrar)
# ==========================================================
if menu == "Pagos Cuota Litis":
    st.subheader("💳 Pagos Cuota Litis")
    st.dataframe(pagos_litis.sort_values("FechaPago", ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar pagos litis (CSV)", pagos_litis.to_csv(index=False).encode("utf-8"), "pagos_litis.csv")

# ==========================================================
# CRONOGRAMA DE CUOTAS (blindado/restablecido)
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
        caso = st.selectbox("Expediente", exp_list, key="cr_caso")
        tipo = st.selectbox("Tipo", TIPOS_CUOTA, key="cr_tipo")
        venc = st.date_input("Fecha vencimiento", value=date.today(), key="cr_venc")
        monto = st.number_input("Monto cuota", min_value=0.0, step=50.0, key="cr_monto")
        notas = st.text_input("Notas", value="", key="cr_notas")

        caso = normalize_key(caso)
        tipo = "Honorarios" if tipo == "Honorarios" else "CuotaLitis"

        sub = cuotas[(cuotas["Caso"] == caso) & (cuotas["Tipo"] == tipo)].copy()
        sub["NroCuota"] = pd.to_numeric(sub["NroCuota"], errors="coerce").fillna(0).astype(int)
        nro = int(sub["NroCuota"].max()) + 1 if not sub.empty else 1

        if st.button("Guardar cuota", key="cr_save"):
            new_id = next_id(cuotas)
            cuotas = add_row(cuotas, {
                "ID": new_id,
                "Caso": caso,
                "Tipo": tipo,
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

    st.download_button("⬇️ Descargar cronograma (CSV)", cuotas.to_csv(index=False).encode("utf-8"), "cuotas.csv")

# ==========================================================
# ACTUACIONES (FICHA por caso/cliente + historial desplegable + reporte)
# ==========================================================
if menu == "Actuaciones":
    st.subheader("🧾 Actuaciones – Ficha por caso y cliente")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        tab_reg, tab_hist, tab_rep = st.tabs(["Registrar actuación", "Historial (desplegable)", "Reporte"])

        exp_list = casos["Expediente"].tolist()

        with tab_reg:
            exp = st.selectbox("Expediente", exp_list, key="act_exp")
            fila_caso = casos[casos["Expediente"] == exp].iloc[0]
            cliente = str(fila_caso.get("Cliente",""))

            st.write(f"**Cliente:** {cliente}")
            with st.form("act_new_form"):
                fecha = st.date_input("Fecha", value=date.today())
                tipo = st.text_input("Tipo de actuación (ej: Demanda, Audiencia, Sentencia, Apelación...)")
                resumen = st.text_area("Resumen (amplio)", height=160)
                prox = st.text_input("Próxima acción (opcional)")
                prox_fecha = st.text_input("Fecha próxima acción (YYYY-MM-DD opcional)")
                link = st.text_input("Link OneDrive (opcional)")
                notas = st.text_area("Notas (opcional)", height=100)
                submit = st.form_submit_button("Guardar actuación")

                if submit:
                    new_id = next_id(actuaciones)
                    actuaciones = add_row(actuaciones, {
                        "ID": new_id,
                        "Caso": normalize_key(exp),
                        "Cliente": cliente,
                        "Fecha": str(fecha),
                        "TipoActuacion": tipo,
                        "Resumen": resumen,
                        "ProximaAccion": prox,
                        "FechaProximaAccion": prox_fecha,
                        "LinkOneDrive": link,
                        "Notas": notas
                    }, "actuaciones")
                    save_df("actuaciones", actuaciones)
                    st.success("✅ Actuación registrada")
                    st.rerun()

        with tab_hist:
            exp_h = st.selectbox("Selecciona expediente para historial", exp_list, key="act_hist_exp")
            hist = actuaciones[actuaciones["Caso"] == normalize_key(exp_h)].copy()
            if hist.empty:
                st.info("No hay actuaciones registradas para este caso.")
            else:
                # orden por fecha (string) y luego ID
                hist["_Fecha_dt"] = hist["Fecha"].apply(lambda x: pd.to_datetime(x, errors="coerce"))
                hist.sort_values(["_Fecha_dt","ID"], ascending=[False, False], inplace=True)
                for _, r in hist.iterrows():
                    titulo = f"{r['Fecha']} – {r['TipoActuacion']} (ID {r['ID']})"
                    with st.expander(titulo, expanded=False):
                        st.write(f"**Cliente:** {r.get('Cliente','')}")
                        st.write(f"**Resumen:** {r.get('Resumen','')}")
                        st.write(f"**Próxima acción:** {r.get('ProximaAccion','')}")
                        st.write(f"**Fecha próxima acción:** {r.get('FechaProximaAccion','')}")
                        if str(r.get("LinkOneDrive","")).strip():
                            st.markdown(f"**Link OneDrive:** {r.get('LinkOneDrive')}")
                        st.write(f"**Notas:** {r.get('Notas','')}")

                st.divider()
                st.markdown("### Editar / borrar actuación (por ID)")
                sel = st.selectbox("Actuación ID", hist["ID"].tolist(), key="act_edit_id")
                fila = actuaciones[actuaciones["ID"] == sel].iloc[0]
                with st.form("act_edit_form"):
                    fecha_e = st.text_input("Fecha (YYYY-MM-DD)", value=str(fila["Fecha"]))
                    tipo_e = st.text_input("TipoActuacion", value=str(fila["TipoActuacion"]))
                    resumen_e = st.text_area("Resumen", value=str(fila["Resumen"]), height=160)
                    prox_e = st.text_input("ProximaAccion", value=str(fila["ProximaAccion"]))
                    prox_fecha_e = st.text_input("FechaProximaAccion", value=str(fila["FechaProximaAccion"]))
                    link_e = st.text_input("LinkOneDrive", value=str(fila.get("LinkOneDrive","")))
                    notas_e = st.text_area("Notas", value=str(fila["Notas"]), height=100)
                    submit = st.form_submit_button("Guardar cambios")
                    if submit:
                        idx = actuaciones.index[actuaciones["ID"] == sel][0]
                        actuaciones.loc[idx, ["Fecha","TipoActuacion","Resumen","ProximaAccion","FechaProximaAccion","LinkOneDrive","Notas"]] = [
                            fecha_e, tipo_e, resumen_e, prox_e, prox_fecha_e, link_e, notas_e
                        ]
                        save_df("actuaciones", actuaciones)
                        st.success("✅ Actualizado")
                        st.rerun()

                if st.button("🗑️ Borrar actuación", key="act_del_btn"):
                    actuaciones = actuaciones[actuaciones["ID"] != sel].copy()
                    save_df("actuaciones", actuaciones)
                    st.success("✅ Eliminado")
                    st.rerun()

        with tab_rep:
            st.markdown("### Reporte de historial de actuaciones")
            exp_r = st.selectbox("Expediente para reporte", exp_list, key="act_rep_exp")
            rep = actuaciones[actuaciones["Caso"] == normalize_key(exp_r)].copy()
            rep = rep.sort_values("Fecha", ascending=False) if not rep.empty else rep

            st.dataframe(rep, use_container_width=True)
            st.download_button(
                "⬇️ Descargar historial (CSV)",
                rep.to_csv(index=False).encode("utf-8"),
                f"historial_actuaciones_{exp_r.replace('/','_')}.csv"
            )

            # Reporte TXT
            lines = [f"HISTORIAL DE ACTUACIONES – EXPEDIENTE: {exp_r}", "-"*60]
            if rep.empty:
                lines.append("No hay actuaciones registradas.")
            else:
                for _, r in rep.iterrows():
                    lines.append(f"Fecha: {r.get('Fecha','')}")
                    lines.append(f"Tipo: {r.get('TipoActuacion','')}")
                    lines.append(f"Resumen: {r.get('Resumen','')}")
                    lines.append(f"Próxima acción: {r.get('ProximaAccion','')}")
                    lines.append(f"Fecha próxima acción: {r.get('FechaProximaAccion','')}")
                    if str(r.get("LinkOneDrive","")).strip():
                        lines.append(f"Link OneDrive: {r.get('LinkOneDrive','')}")
                    lines.append(f"Notas: {r.get('Notas','')}")
                    lines.append("-"*60)

            txt = "\n".join(lines)
            st.download_button("⬇️ Descargar historial (TXT)", txt.encode("utf-8"), f"historial_actuaciones_{exp_r.replace('/','_')}.txt")

# ==========================================================
# CONSULTAS (nuevo): formulario + proforma + historial desplegable
# ==========================================================
if menu == "Consultas":
    st.subheader("🗂️ Consultas – Registro, proforma e historial")

    tab_new, tab_hist, tab_rep = st.tabs(["Nueva consulta", "Historial (desplegable)", "Reporte"])

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    clientes_list = clientes["Nombre"].tolist() if not clientes.empty else []

    with tab_new:
        with st.form("cons_new_form"):
            fecha = st.date_input("Fecha", value=date.today())
            cliente = st.selectbox("Cliente", clientes_list) if clientes_list else st.text_input("Cliente")
            caso = st.selectbox("Expediente (opcional)", [""] + exp_list) if exp_list else st.text_input("Expediente (opcional)")
            consulta_txt = st.text_area("Consulta (amplio)", height=180)
            estrategia_txt = st.text_area("Propuesta de estrategia (amplio)", height=180)
            honorarios_prop = st.number_input("Honorarios propuestos (S/)", min_value=0.0, step=50.0)
            link = st.text_input("Link OneDrive (opcional)")
            notas = st.text_area("Notas (opcional)", height=100)

            # Proforma (texto)
            proforma = (
                f"PROFORMA – {APP_NAME}\n"
                f"Fecha: {fecha}\n"
                f"Cliente: {cliente}\n"
                f"Expediente: {caso}\n"
                f"{'-'*60}\n"
                f"CONSULTA:\n{consulta_txt}\n\n"
                f"PROPUESTA DE ESTRATEGIA:\n{estrategia_txt}\n\n"
                f"HONORARIOS PROPUESTOS: S/ {honorarios_prop:,.2f}\n"
                f"{'-'*60}\n"
                f"Notas: {notas}\n"
            )

            submit = st.form_submit_button("Guardar consulta y proforma")
            if submit:
                new_id = next_id(consultas)
                consultas = add_row(consultas, {
                    "ID": new_id,
                    "Fecha": str(fecha),
                    "Cliente": cliente,
                    "Caso": normalize_key(caso),
                    "Consulta": consulta_txt,
                    "Estrategia": estrategia_txt,
                    "HonorariosPropuestos": float(honorarios_prop),
                    "Proforma": proforma,
                    "LinkOneDrive": link,
                    "Notas": notas
                }, "consultas")
                save_df("consultas", consultas)
                st.success("✅ Consulta guardada")
                st.rerun()

        if 'proforma' in locals():
            st.download_button("⬇️ Descargar proforma (TXT)", proforma.encode("utf-8"), f"proforma_{date.today()}.txt")

    with tab_hist:
        if consultas.empty:
            st.info("Aún no hay consultas registradas.")
        else:
            # desplegable por ID con etiqueta amigable
            def label_consulta(row):
                return f"ID {row['ID']} – {row.get('Fecha','')} – {row.get('Cliente','')}"
            consultas_view = consultas.copy()
            consultas_view["_label"] = consultas_view.apply(label_consulta, axis=1)

            sel_label = st.selectbox("Selecciona una consulta", consultas_view["_label"].tolist())
            row = consultas_view[consultas_view["_label"] == sel_label].iloc[0]

            st.markdown("### Detalle de consulta")
            st.write(f"**Fecha:** {row.get('Fecha','')}")
            st.write(f"**Cliente:** {row.get('Cliente','')}")
            st.write(f"**Expediente:** {row.get('Caso','')}")
            if str(row.get("LinkOneDrive","")).strip():
                st.markdown(f"**Link OneDrive:** {row.get('LinkOneDrive')}")
            st.markdown("**Consulta:**")
            st.write(row.get("Consulta",""))
            st.markdown("**Estrategia:**")
            st.write(row.get("Estrategia",""))
            st.markdown(f"**Honorarios propuestos:** S/ {money(row.get('HonorariosPropuestos',0)):,.2f}")

            st.divider()
            st.markdown("### Proforma")
            st.text_area("Proforma (texto)", value=str(row.get("Proforma","")), height=260)
            st.download_button("⬇️ Descargar proforma seleccionada (TXT)", str(row.get("Proforma","")).encode("utf-8"), f"proforma_consulta_{row['ID']}.txt")

            st.divider()
            st.markdown("### Editar / borrar consulta (por ID)")
            sel_id = int(row["ID"])
            fila = consultas[consultas["ID"] == sel_id].iloc[0]
            with st.form("cons_edit_form"):
                fecha_e = st.text_input("Fecha", value=str(fila.get("Fecha","")))
                cliente_e = st.text_input("Cliente", value=str(fila.get("Cliente","")))
                caso_e = st.text_input("Expediente", value=str(fila.get("Caso","")))
                consulta_e = st.text_area("Consulta", value=str(fila.get("Consulta","")), height=160)
                estrategia_e = st.text_area("Estrategia", value=str(fila.get("Estrategia","")), height=160)
                honor_e = st.number_input("Honorarios propuestos (S/)", min_value=0.0, value=money(fila.get("HonorariosPropuestos",0)), step=50.0)
                link_e = st.text_input("Link OneDrive", value=str(fila.get("LinkOneDrive","")))
                notas_e = st.text_area("Notas", value=str(fila.get("Notas","")), height=100)
                submit = st.form_submit_button("Guardar cambios")
                if submit:
                    # regenerar proforma actualizada
                    proforma_new = (
                        f"PROFORMA – {APP_NAME}\n"
                        f"Fecha: {fecha_e}\n"
                        f"Cliente: {cliente_e}\n"
                        f"Expediente: {caso_e}\n"
                        f"{'-'*60}\n"
                        f"CONSULTA:\n{consulta_e}\n\n"
                        f"PROPUESTA DE ESTRATEGIA:\n{estrategia_e}\n\n"
                        f"HONORARIOS PROPUESTOS: S/ {float(honor_e):,.2f}\n"
                        f"{'-'*60}\n"
                        f"Notas: {notas_e}\n"
                    )
                    idx = consultas.index[consultas["ID"] == sel_id][0]
                    consultas.loc[idx, ["Fecha","Cliente","Caso","Consulta","Estrategia","HonorariosPropuestos","Proforma","LinkOneDrive","Notas"]] = [
                        fecha_e, cliente_e, normalize_key(caso_e), consulta_e, estrategia_e, float(honor_e), proforma_new, link_e, notas_e
                    ]
                    save_df("consultas", consultas)
                    st.success("✅ Consulta actualizada")
                    st.rerun()

            if st.button("🗑️ Borrar consulta", key="cons_del"):
                consultas = consultas[consultas["ID"] != sel_id].copy()
                save_df("consultas", consultas)
                st.success("✅ Eliminada")
                st.rerun()

    with tab_rep:
        st.markdown("### Reporte de consultas")
        st.dataframe(consultas.sort_values("Fecha", ascending=False), use_container_width=True)
        st.download_button("⬇️ Descargar consultas (CSV)", consultas.to_csv(index=False).encode("utf-8"), "consultas.csv")

# ==========================================================
# DOCUMENTOS
# ==========================================================
if menu == "Documentos":
    st.subheader("📎 Documentos")
    st.dataframe(documentos.sort_values("Fecha", ascending=False), use_container_width=True)
    st.download_button("⬇️ Descargar documentos (CSV)", documentos.to_csv(index=False).encode("utf-8"), "documentos.csv")

# ==========================================================
# PLANTILLAS DE CONTRATO
# ==========================================================
if menu == "Plantillas de Contrato":
    st.subheader("📝 Plantillas de Contrato (Modelos)")
    accion = st.radio("Acción", ["Nueva","Editar","Eliminar"], horizontal=True)

    st.info("Placeholders: {{EXPEDIENTE}}, {{CLIENTE_NOMBRE}}, {{CLIENTE_DNI}}, {{MATERIA}}, {{INSTANCIA}}, {{MONTO_PACTADO}}, {{PORCENTAJE_LITIS}}, {{FECHA_HOY}}")

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

    st.divider()
    st.dataframe(plantillas, use_container_width=True)
    st.download_button("⬇️ Descargar plantillas (CSV)", plantillas.to_csv(index=False).encode("utf-8"), "plantillas_contratos.csv")

# ==========================================================
# GENERAR CONTRATO
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

    etapas_exp = honorarios_etapas[honorarios_etapas["Caso"] == expediente]
    if not etapas_exp.empty:
        monto_pactado = safe_float_series(etapas_exp["Monto Pactado"]).sum()
    else:
        monto_pactado = safe_float_series(canon_h[canon_h["Caso"] == expediente]["Monto Pactado"]).sum()

    porc = safe_float_series(canon_cl[canon_cl["Caso"] == expediente]["Porcentaje"])
    porc_val = float(porc.iloc[-1]) if len(porc) else 0.0

    ctx = {
        "{{EXPEDIENTE}}": expediente,
        "{{CLIENTE_NOMBRE}}": str(c.get("Cliente","")),
        "{{ABOGADO_NOMBRE}}": str(c.get("Abogado","")),
        "{{MATERIA}}": str(c.get("Materia","")),
        "{{INSTANCIA}}": str(c.get("Instancia","")),
        "{{PRETENSION}}": str(c.get("Pretension","")),
        "{{MONTO_PACTADO}}": f"{monto_pactado:.2f}",
        "{{PORCENTAJE_LITIS}}": f"{porc_val:.2f}",
        "{{FECHA_HOY}}": date.today().strftime("%Y-%m-%d"),
    }
    if cli is not None:
        ctx.update({
            "{{CLIENTE_DNI}}": str(cli.get("DNI","")),
            "{{CLIENTE_CELULAR}}": str(cli.get("Celular","")),
            "{{CLIENTE_CORREO}}": str(cli.get("Correo","")),
            "{{CLIENTE_DIRECCION}}": str(cli.get("Direccion","")),
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
        exp = st.selectbox("Expediente", casos["Expediente"].tolist(), key="gc_exp")
        tpl_id = st.selectbox("Plantilla ID", plantillas["ID"].tolist(), key="gc_tpl")
        tpl = plantillas[plantillas["ID"] == tpl_id].iloc[0]

        ctx = build_context(exp)
        generado = render_template(str(tpl["Contenido"]), ctx)

        st.text_area("Vista previa", value=generado, height=350)
        nombre_archivo = f"Contrato_{exp.replace('/','_')}_{str(tpl['Nombre']).replace(' ','_')}.txt"
        st.download_button("⬇️ Descargar contrato (TXT)", data=generado.encode("utf-8"), file_name=nombre_archivo)

        if st.button("💾 Guardar en carpeta generados/", key="gc_save"):
            out_path = os.path.join(GENERADOS_DIR, nombre_archivo)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(generado)
            st.success(f"✅ Guardado en {out_path}")

# ==========================================================
# USUARIOS
# ==========================================================
if menu == "Usuarios":
    require_admin()
    st.subheader("👥 Usuarios (vinculados a abogados)")
    users = load_df("usuarios")
    st.dataframe(users[["Usuario","Rol","AbogadoID","Activo","Creado"]], use_container_width=True)
    st.download_button("⬇️ Descargar usuarios (CSV)", users.to_csv(index=False).encode("utf-8"), "usuarios.csv")

    abogado_map = {str(r["ID"]): str(r["Nombre"]) for _, r in abogados.iterrows()} if not abogados.empty else {}
    accion = st.radio("Acción", ["Nuevo","Cambiar contraseña","Activar/Desactivar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        if abogados.empty:
            st.warning("Primero registra abogados para vincular usuarios.")
        else:
            with st.form("new_user_form"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                rol = st.selectbox("Rol", ["admin","abogado","asistente"])
                abogado_id = st.selectbox(
                    "Abogado asociado",
                    options=list(abogado_map.keys()),
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

# ==========================================================
# REPORTES (pestañas)
# ==========================================================
if menu == "Reportes":
    st.subheader("📈 Reportes")
    df_res = resumen_financiero_df()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Saldos por caso", "Saldos por cliente", "Actuaciones", "Consultas", "Documentos"])

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
        st.dataframe(consultas.sort_values("Fecha", ascending=False), use_container_width=True)
        st.download_button("⬇️ Descargar consultas (CSV)", consultas.to_csv(index=False).encode("utf-8"), "reporte_consultas.csv")

    with tab5:
        st.dataframe(documentos.sort_values("Fecha", ascending=False), use_container_width=True)
        st.download_button("⬇️ Descargar documentos (CSV)", documentos.to_csv(index=False).encode("utf-8"), "reporte_documentos.csv")

# ==========================================================
# AUDITORÍA (huérfanos)
# ==========================================================
if menu == "Auditoría":
    st.subheader("🧹 Auditoría")
    st.info("Muestra registros huérfanos (Caso no existe en casos). Útil para detectar montos/pagos fantasmas.")

    casos_set = set(casos["Expediente"].tolist())

    def orphans(df):
        if df.empty or "Caso" not in df.columns:
            return df
        tmp = df.copy()
        tmp["Caso"] = tmp["Caso"].apply(normalize_key)
        return tmp[~tmp["Caso"].isin(casos_set)].copy()

    st.markdown("### Honorarios total huérfanos")
    st.dataframe(orphans(honorarios), use_container_width=True)

    st.markdown("### Honorarios por etapa huérfanos")
    st.dataframe(orphans(honorarios_etapas), use_container_width=True)

    st.markdown("### Pagos honorarios huérfanos")
    st.dataframe(orphans(pagos_honorarios), use_container_width=True)

    st.markdown("### Cuota litis huérfana")
    st.dataframe(orphans(cuota_litis), use_container_width=True)

    st.markdown("### Pagos litis huérfanos")
    st.dataframe(orphans(pagos_litis), use_container_width=True)

    st.markdown("### Cuotas cronograma huérfanas")
    st.dataframe(orphans(cuotas), use_container_width=True)

    st.markdown("### Actuaciones huérfanas")
    st.dataframe(orphans(actuaciones.rename(columns={"Caso":"Caso"})), use_container_width=True)

    st.markdown("### Consultas huérfanas (si expediente no existe)")
    if not consultas.empty:
        tmp = consultas.copy()
        tmp["Caso"] = tmp["Caso"].apply(normalize_key)
        hu = tmp[(tmp["Caso"] != "") & (~tmp["Caso"].isin(casos_set))].copy()
        st.dataframe(hu, use_container_width=True)
    else:
        st.info("No hay consultas.")
# ==========================================================
# ======= PARCHE MARCA 004 (INSERTAR DESPUÉS DE LÍNEA 1575) ==
# Objetivo: NO recortar nada, solo mejorar lo indicado:
#  - Dashboard: cronograma visible aunque df_estado esté vacío
#  - Resumen económico: tabla consolidada visible
#  - Cuota Litis y Pagos Litis: CRUD completo visible
#  - Reporte por abogado y sus casos
# ==========================================================

# ----------------------------------------------------------
# 1) DASHBOARD: Cronograma visible aunque no haya pagos
#    (No toca tu dashboard, solo añade salida si corresponde)
# ----------------------------------------------------------
try:
    if 'menu' in globals() and menu == "Dashboard":
        # Mostrar cronograma base si hay cuotas aunque df_estado sea vacío
        st.divider()
        st.markdown("### 📅 Cronograma (visible aunque no haya pagos)")

        # Si existe cuotas.csv se debe mostrar siempre
        if 'cuotas' in globals() and not cuotas.empty:
            # Si df_estado está vacío o no tiene columnas esperadas, mostrar cronograma base
            if ('df_estado' not in globals()) or (df_estado is None) or (getattr(df_estado, "empty", True)) or ("SaldoCuota" not in getattr(df_estado, "columns", [])):
                st.info("Hay cuotas registradas, pero aún no hay pagos asignados. Mostrando cronograma base.")
                st.dataframe(
                    cuotas.sort_values(["Caso", "Tipo", "NroCuota"], ascending=[True, True, True]),
                    use_container_width=True
                )
            else:
                st.dataframe(
                    df_estado.sort_values(["Caso", "Tipo", "NroCuota"], ascending=[True, True, True]),
                    use_container_width=True
                )
        else:
            st.info("No hay cuotas registradas aún.")

        # Resumen económico consolidado (tabla)
        st.divider()
        st.markdown("### 📊 Resumen económico consolidado")
        if 'resumen_financiero_df' in globals():
            df_res_local = resumen_financiero_df()
            st.dataframe(df_res_local, use_container_width=True)
except Exception:
    pass

# ----------------------------------------------------------
# 2) CUOTA LITIS: asegurar CRUD visible (no borra tu menú)
# ----------------------------------------------------------
def _patch_render_cuota_litis_menu():
    st.subheader("⚖️ Cuota Litis (restaurado)")
    st.dataframe(cuota_litis.sort_values("ID", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    if exp_list:
        exp = st.selectbox("Expediente", exp_list, key="patch_cl_exp")
        base = st.number_input("Monto base", min_value=0.0, step=100.0, key="patch_cl_base")
        porc = st.number_input("Porcentaje (%)", min_value=0.0, step=1.0, key="patch_cl_porc")
        notas = st.text_input("Notas", value="", key="patch_cl_notas")

        if st.button("Guardar cuota litis", key="patch_cl_save"):
            new_id = next_id(cuota_litis)
            nueva = {
                "ID": new_id,
                "Caso": normalize_key(exp),
                "Monto Base": float(base),
                "Porcentaje": float(porc),
                "Notas": notas,
                "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            df2 = add_row(cuota_litis, nueva, "cuota_litis")
            save_df("cuota_litis", df2)
            st.success("✅ Cuota litis guardada")
            st.rerun()

    st.divider()
    st.markdown("### Editar / borrar (por ID)")
    if not cuota_litis.empty:
        sel = st.selectbox("Cuota Litis ID", cuota_litis["ID"].tolist(), key="patch_cl_sel")
        fila = cuota_litis[cuota_litis["ID"] == sel].iloc[0]

        with st.form("patch_cl_edit_form"):
            caso_e = st.text_input("Expediente", value=str(fila["Caso"]), key="patch_cl_caso_e")
            base_e = st.number_input("Monto base", min_value=0.0, value=money(fila["Monto Base"]), step=100.0, key="patch_cl_base_e")
            porc_e = st.number_input("Porcentaje", min_value=0.0, value=money(fila["Porcentaje"]), step=1.0, key="patch_cl_porc_e")
            notas_e = st.text_input("Notas", value=str(fila["Notas"]), key="patch_cl_notas_e")
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = cuota_litis.index[cuota_litis["ID"] == sel][0]
                cuota_litis.loc[idx, ["Caso","Monto Base","Porcentaje","Notas"]] = [normalize_key(caso_e), float(base_e), float(porc_e), notas_e]
                save_df("cuota_litis", cuota_litis)
                st.success("✅ Actualizado")
                st.rerun()

        if st.button("🗑️ Borrar cuota litis", key="patch_cl_del"):
            df2 = cuota_litis[cuota_litis["ID"] != sel].copy()
            save_df("cuota_litis", df2)
            st.success("✅ Eliminado")
            st.rerun()

    st.download_button("⬇️ Descargar cuota litis (CSV)", cuota_litis.to_csv(index=False).encode("utf-8"), "cuota_litis.csv")

# ----------------------------------------------------------
# 3) PAGOS LITIS: asegurar CRUD visible (no borra tu menú)
# ----------------------------------------------------------
def _patch_render_pagos_litis_menu():
    st.subheader("💳 Pagos Cuota Litis (restaurado)")
    st.dataframe(pagos_litis.sort_values("FechaPago", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    if exp_list:
        exp = st.selectbox("Expediente", exp_list, key="patch_pl_exp")
        fecha = st.date_input("Fecha pago", value=date.today(), key="patch_pl_fecha")
        monto = st.number_input("Monto pagado", min_value=0.0, step=50.0, key="patch_pl_monto")
        obs = st.text_input("Observación", value="", key="patch_pl_obs")

        if st.button("Registrar pago litis", key="patch_pl_save"):
            new_id = next_id(pagos_litis)
            nueva = {
                "ID": new_id,
                "Caso": normalize_key(exp),
                "FechaPago": str(fecha),
                "Monto": float(monto),
                "Observacion": obs
            }
            df2 = add_row(pagos_litis, nueva, "pagos_litis")
            save_df("pagos_litis", df2)
            st.success("✅ Pago litis guardado")
            st.rerun()

    st.divider()
    st.markdown("### Editar / borrar (por ID)")
    if not pagos_litis.empty:
        sel = st.selectbox("Pago ID", pagos_litis["ID"].tolist(), key="patch_pl_sel")
        fila = pagos_litis[pagos_litis["ID"] == sel].iloc[0]

        with st.form("patch_pl_edit_form"):
            caso_e = st.text_input("Expediente", value=str(fila["Caso"]), key="patch_pl_caso_e")
            fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]), key="patch_pl_fecha_e")
            monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0, key="patch_pl_monto_e")
            obs_e = st.text_input("Observación", value=str(fila["Observacion"]), key="patch_pl_obs_e")
            submit = st.form_submit_button("Guardar cambios")
            if submit:
                idx = pagos_litis.index[pagos_litis["ID"] == sel][0]
                pagos_litis.loc[idx, :] = [sel, normalize_key(caso_e), fecha_e, float(monto_e), obs_e]
                save_df("pagos_litis", pagos_litis)
                st.success("✅ Actualizado")
                st.rerun()

        if st.button("🗑️ Borrar pago litis", key="patch_pl_del"):
            df2 = pagos_litis[pagos_litis["ID"] != sel].copy()
            save_df("pagos_litis", df2)
            st.success("✅ Eliminado")
            st.rerun()

    st.download_button("⬇️ Descargar pagos litis (CSV)", pagos_litis.to_csv(index=False).encode("utf-8"), "pagos_litis.csv")

# ----------------------------------------------------------
# 4) Reporte por Abogado: bloque seguro (no destruye tabs existentes)
#    Se activa dentro de menu == "Reportes" si existe df_res y casos
# ----------------------------------------------------------
def _patch_reporte_por_abogado():
    st.markdown("### 👨‍⚖️ Reporte por abogado y sus casos (añadido)")
    if casos.empty:
        st.info("No hay casos registrados.")
        return
    df_res = resumen_financiero_df() if 'resumen_financiero_df' in globals() else pd.DataFrame()
    if df_res.empty:
        st.info("No hay datos financieros aún.")
        return

    # unir abogado
    dfm = df_res.merge(casos[["Expediente","Abogado"]], on="Expediente", how="left")

    rep_ab = dfm.groupby("Abogado", as_index=False).agg({
        "Honorario Pactado":"sum",
        "Honorario Pagado":"sum",
        "Honorario Pendiente":"sum",
        "Saldo Litis":"sum"
    })

    st.dataframe(rep_ab, use_container_width=True)
    st.download_button("⬇️ Descargar reporte por abogado (CSV)", rep_ab.to_csv(index=False).encode("utf-8"), "reporte_por_abogado.csv")

    st.divider()
    st.markdown("#### Detalle de casos por abogado")
    abogados_disp = [a for a in rep_ab["Abogado"].dropna().tolist() if str(a).strip() != ""]
    if not abogados_disp:
        st.info("No hay abogado asociado en los casos.")
        return

    ab_sel = st.selectbox("Selecciona abogado", abogados_disp, key="patch_ab_sel")
    det = dfm[dfm["Abogado"] == ab_sel].copy()
    st.dataframe(det, use_container_width=True)
    st.download_button("⬇️ Descargar detalle abogado (CSV)", det.to_csv(index=False).encode("utf-8"), f"reporte_detalle_{ab_sel}.csv")

# ----------------------------------------------------------
# Activación “sin tocar tu código”: si el menú coincide, muestra el bloque
# ----------------------------------------------------------
try:
    if 'menu' in globals() and menu == "Cuota Litis":
        _patch_render_cuota_litis_menu()
except Exception:
    pass

try:
    if 'menu' in globals() and menu == "Pagos Cuota Litis":
        _patch_render_pagos_litis_menu()
except Exception:
    pass

try:
    if 'menu' in globals() and menu == "Reportes":
        st.divider()
        _patch_reporte_por_abogado()
except Exception:
    pass

# =================== FIN PARCHE MARCA 004 ==================
