import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import date, datetime
import shutil

st.set_page_config(page_title="⚖️ Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

# =========================
# CONFIG
# =========================
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

# =========================
# ESQUEMAS
# =========================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","Activo","Creado"],
    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones","EstadoCaso","FechaInicio"],
    "honorarios": ["Caso","Monto Pactado"],
    "pagos_honorarios": ["ID","Caso","FechaPago","Monto","Observacion"],
    "cuota_litis": ["Caso","Monto Base","Porcentaje"],
    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],
    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"],
    "actuaciones": ["ID","Caso","Fecha","TipoActuacion","Resumen","ProximaAccion","FechaProximaAccion","Notas"],
    "documentos": ["ID","Caso","Tipo","NombreArchivo","Ruta","Fecha","Notas"],
    "plantillas": ["ID","Nombre","Contenido","Notas","Creado"],
}

# =========================
# UTILIDADES
# =========================
def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

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

def ensure_csv(key: str):
    path = FILES[key]
    cols = SCHEMAS[key]

    # crear si no existe
    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    # si está vacío (0 bytes), recrear
    try:
        if os.path.getsize(path) == 0:
            pd.DataFrame(columns=cols).to_csv(path, index=False)
            return
    except OSError:
        pass

    # leer seguro
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    df = drop_unnamed(df)

    # columnas faltantes
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    # normalizar columnas / orden
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

def to_date_safe(x):
    if pd.isna(x) or str(x).strip() == "":
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def money(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def safe_float_series(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

# =========================
# Inicializar archivos
# =========================
for k in FILES:
    ensure_csv(k)

# =========================
# Cargar usuarios y asegurar admin
# =========================
usuarios_df = load_df("usuarios")
if usuarios_df.empty:
    usuarios_df = add_row(usuarios_df, {
        "Usuario": "admin",
        "PasswordHash": sha256("estudio123"),
        "Rol": "admin",
        "Activo": "1",
        "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, "usuarios")
    save_df("usuarios", usuarios_df)
else:
    # si no existe admin, crearlo
    if not (usuarios_df["Usuario"] == "admin").any():
        usuarios_df = add_row(usuarios_df, {
            "Usuario": "admin",
            "PasswordHash": sha256("estudio123"),
            "Rol": "admin",
            "Activo": "1",
            "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, "usuarios")
        save_df("usuarios", usuarios_df)

# =========================
# SESSION + LOGIN
# =========================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "rol" not in st.session_state:
    st.session_state.rol = None

def login_ui():
    st.title("⚖️ Estudio Jurídico Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")

    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        users = load_df("usuarios")
        users = users[users["Activo"].astype(str) == "1"].copy()
        row = users[users["Usuario"].astype(str) == str(u)].copy()
        if row.empty:
            st.error("Credenciales incorrectas")
            st.stop()
        if row.iloc[0]["PasswordHash"] != sha256(p):
            st.error("Credenciales incorrectas")
            st.stop()
        st.session_state.usuario = u
        st.session_state.rol = row.iloc[0]["Rol"]
        st.rerun()

if st.session_state.usuario is None:
    login_ui()
    st.stop()

st.sidebar.write(f"👤 Usuario: {st.session_state.usuario} ({st.session_state.rol})")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.session_state.rol = None
    st.rerun()

# =========================
# CARGAR DATA PRINCIPAL
# =========================
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

# =========================
# BOTÓN REPARAR SISTEMA
# =========================
if st.sidebar.button("🛠️ Reparar sistema (CSV)"):
    for k in FILES:
        ensure_csv(k)
    st.success("✅ Sistema reparado (CSVs verificados).")
    st.rerun()

# =========================
# MENÚ
# =========================
menu_items = [
    "Dashboard",
    "Búsqueda",
    "Clientes",
    "Abogados",
    "Casos",
    "Ficha del Caso",
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
]

menu = st.sidebar.selectbox("📌 Menú", menu_items)

# =========================
# FINANZAS
# =========================
def resumen_financiero_df():
    if casos.empty:
        return pd.DataFrame(columns=[
            "Expediente","Cliente","Materia",
            "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
            "Monto Base","Porcentaje","Cuota Litis Calculada","Pagado Litis","Saldo Litis"
        ])

    resumen = []
    for _, c in casos.iterrows():
        exp = c["Expediente"]
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
            float(base), float(porcentaje), float(calculada),
            float(pagado_l), float(calculada - pagado_l)
        ])

    return pd.DataFrame(resumen, columns=[
        "Expediente","Cliente","Materia",
        "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
        "Monto Base","Porcentaje","Cuota Litis Calculada","Pagado Litis","Saldo Litis"
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

def estado_cuenta_expediente(expediente: str):
    df_res = resumen_financiero_df()
    fila = df_res[df_res["Expediente"] == expediente]
    if fila.empty:
        return None, None, None
    f = fila.iloc[0]

    pagosH = pagos_honorarios[pagos_honorarios["Caso"] == expediente].copy()
    pagosL = pagos_litis[pagos_litis["Caso"] == expediente].copy()
    pagosH["Monto"] = safe_float_series(pagosH["Monto"])
    pagosL["Monto"] = safe_float_series(pagosL["Monto"])

    cuotas_status = cuotas_status_all()
    cuotas_exp = cuotas_status[cuotas_status["Caso"] == expediente].copy() if not cuotas_status.empty else pd.DataFrame()

    return f, pagosH, pagosL, cuotas_exp

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

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard General")

    df_res = resumen_financiero_df()
    df_status = cuotas_status_all()
    df_pend = cuotas_pendientes(df_status)

    total_pactado = df_res["Honorario Pactado"].sum() if not df_res.empty else 0
    total_pagado_h = df_res["Honorario Pagado"].sum() if not df_res.empty else 0
    total_pend_h = df_res["Honorario Pendiente"].sum() if not df_res.empty else 0

    total_litis = df_res["Cuota Litis Calculada"].sum() if not df_res.empty else 0
    total_pagado_l = df_res["Pagado Litis"].sum() if not df_res.empty else 0
    total_pend_l = df_res["Saldo Litis"].sum() if not df_res.empty else 0

    st.subheader("💰 Indicadores Económicos (Saldo total)")
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Honorarios Pactados (S/)", f"{total_pactado:,.2f}")
    c2.metric("✅ Honorarios Pagados (S/)", f"{total_pagado_h:,.2f}")
    c3.metric("⏳ Honorarios Pendientes (S/)", f"{total_pend_h:,.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("⚖️ Cuota Litis Calculada (S/)", f"{total_litis:,.2f}")
    c5.metric("✅ Cuota Litis Pagada (S/)", f"{total_pagado_l:,.2f}")
    c6.metric("⏳ Cuota Litis Pendiente (S/)", f"{total_pend_l:,.2f}")

    st.divider()

    st.subheader("📅 Cuotas (Cronograma)")
    vencidas = pd.DataFrame()
    por_vencer = pd.DataFrame()

    if not df_pend.empty:
        vencidas = df_pend[df_pend["DiasParaVencimiento"].notna() & (df_pend["DiasParaVencimiento"] < 0)]
        por_vencer = df_pend[df_pend["DiasParaVencimiento"].notna() & (df_pend["DiasParaVencimiento"].between(0, 7))]

    total_vencidas = float(safe_float_series(vencidas["SaldoCuota"]).sum()) if not vencidas.empty else 0.0
    total_por_vencer = float(safe_float_series(por_vencer["SaldoCuota"]).sum()) if not por_vencer.empty else 0.0
    total_pend_cuotas = float(safe_float_series(df_pend["SaldoCuota"]).sum()) if not df_pend.empty else 0.0

    d1, d2, d3 = st.columns(3)
    d1.metric("🚨 Vencidas (S/)", f"{total_vencidas:,.2f}")
    d2.metric("⏱️ Por vencer (7 días) (S/)", f"{total_por_vencer:,.2f}")
    d3.metric("📌 Total cuotas pendientes (S/)", f"{total_pend_cuotas:,.2f}")

    st.divider()

    st.subheader("👤 Saldos por Cliente (Top deudores)")
    scli = saldo_por_cliente()
    st.dataframe(scli.head(20), use_container_width=True)

    st.subheader("🚨 Cuotas vencidas")
    if vencidas.empty:
        st.info("No hay cuotas vencidas con saldo.")
    else:
        st.dataframe(vencidas[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]], use_container_width=True)

# =========================
# BÚSQUEDA GLOBAL
# =========================
if menu == "Búsqueda":
    st.title("🔎 Búsqueda global (DNI / Cliente / Expediente)")

    q = st.text_input("Escribe DNI, nombre o expediente").strip().lower()

    if q:
        res_clientes = clientes[
            clientes["DNI"].astype(str).str.lower().str.contains(q, na=False) |
            clientes["Nombre"].astype(str).str.lower().str.contains(q, na=False)
        ].copy()

        res_casos = casos[
            casos["Expediente"].astype(str).str.lower().str.contains(q, na=False) |
            casos["Cliente"].astype(str).str.lower().str.contains(q, na=False) |
            casos["Materia"].astype(str).str.lower().str.contains(q, na=False)
        ].copy()

        st.subheader("Clientes encontrados")
        st.dataframe(res_clientes, use_container_width=True)

        st.subheader("Casos encontrados")
        st.dataframe(res_casos, use_container_width=True)
    else:
        st.info("Escribe algo para buscar.")

# =========================
# CLIENTES (CRUD)
# =========================
if menu == "Clientes":
    st.title("Clientes")
    accion = st.radio("Acción", ["Nuevo", "Editar", "Eliminar"], horizontal=True)

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

    elif accion == "Editar":
        if clientes.empty:
            st.info("No hay clientes.")
        else:
            sel = st.selectbox("Cliente (ID)", clientes["ID"].tolist())
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
                    st.success("✅ Cliente actualizado")
                    st.rerun()

    elif accion == "Eliminar":
        if clientes.empty:
            st.info("No hay clientes.")
        else:
            sel = st.selectbox("Cliente (ID) a eliminar", clientes["ID"].tolist())
            st.warning("⚠️ Eliminar cliente no elimina casos automáticamente.")
            if st.button("Eliminar cliente"):
                clientes = clientes[clientes["ID"] != sel].copy()
                save_df("clientes", clientes)
                st.success("🗑️ Cliente eliminado")
                st.rerun()

    st.subheader("Listado")
    st.dataframe(clientes, use_container_width=True)

# =========================
# ABOGADOS (CRUD)
# =========================
if menu == "Abogados":
    st.title("Abogados")
    accion = st.radio("Acción", ["Nuevo", "Editar", "Eliminar"], horizontal=True)

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

    elif accion == "Editar":
        if abogados.empty:
            st.info("No hay abogados.")
        else:
            sel = st.selectbox("Abogado (ID)", abogados["ID"].tolist())
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
                    st.success("✅ Abogado actualizado")
                    st.rerun()

    elif accion == "Eliminar":
        if abogados.empty:
            st.info("No hay abogados.")
        else:
            sel = st.selectbox("Abogado (ID) a eliminar", abogados["ID"].tolist())
            st.warning("⚠️ Eliminar abogado no elimina casos automáticamente.")
            if st.button("Eliminar abogado"):
                abogados = abogados[abogados["ID"] != sel].copy()
                save_df("abogados", abogados)
                st.success("🗑️ Abogado eliminado")
                st.rerun()

    st.subheader("Listado")
    st.dataframe(abogados, use_container_width=True)

# =========================
# CASOS (CRUD)
# =========================
if menu == "Casos":
    st.title("Casos")
    accion = st.radio("Acción", ["Nuevo", "Editar", "Eliminar"], horizontal=True)

    clientes_list = clientes["Nombre"].tolist() if not clientes.empty else []
    abogados_list = abogados["Nombre"].tolist() if not abogados.empty else [""]

    if accion == "Nuevo":
        with st.form("nuevo_caso"):
            cliente = st.selectbox("Cliente", clientes_list)
            abogado = st.selectbox("Abogado", abogados_list)
            expediente = st.text_input("Número de Expediente")
            anio = st.text_input("Año")
            materia = st.text_input("Materia")
            pretension = st.text_input("Pretensión")
            obs = st.text_area("Observaciones")
            estado = st.selectbox("Estado del caso", ["Activo","En pausa","Cerrado","Archivado"])
            fecha_inicio = st.date_input("Fecha inicio", value=date.today())
            submit = st.form_submit_button("Guardar")
            if submit:
                new_id = next_id(casos)
                casos = add_row(casos, {
                    "ID": new_id, "Cliente": cliente, "Abogado": abogado, "Expediente": expediente,
                    "Año": anio, "Materia": materia, "Pretension": pretension, "Observaciones": obs,
                    "EstadoCaso": estado, "FechaInicio": str(fecha_inicio)
                }, "casos")
                save_df("casos", casos)
                st.success("✅ Caso registrado")
                st.rerun()

    elif accion == "Editar":
        if casos.empty:
            st.info("No hay casos.")
        else:
            sel = st.selectbox("Caso (ID)", casos["ID"].tolist())
            fila = casos[casos["ID"] == sel].iloc[0]
            with st.form("edit_caso"):
                cliente = st.selectbox("Cliente", clientes_list, index=clientes_list.index(fila["Cliente"]) if fila["Cliente"] in clientes_list else 0)
                abogado = st.selectbox("Abogado", abogados_list, index=abogados_list.index(fila["Abogado"]) if fila["Abogado"] in abogados_list else 0)
                expediente = st.text_input("Número de Expediente", value=str(fila["Expediente"]))
                anio = st.text_input("Año", value=str(fila["Año"]))
                materia = st.text_input("Materia", value=str(fila["Materia"]))
                pretension = st.text_input("Pretensión", value=str(fila["Pretension"]))
                obs = st.text_area("Observaciones", value=str(fila["Observaciones"]))
                estado = st.selectbox("Estado del caso", ["Activo","En pausa","Cerrado","Archivado"], index=["Activo","En pausa","Cerrado","Archivado"].index(fila["EstadoCaso"]) if fila["EstadoCaso"] in ["Activo","En pausa","Cerrado","Archivado"] else 0)
                fi = to_date_safe(fila["FechaInicio"]) or date.today()
                fecha_inicio = st.date_input("Fecha inicio", value=fi)
                submit = st.form_submit_button("Guardar cambios")
                if submit:
                    idx = casos.index[casos["ID"] == sel][0]
                    casos.loc[idx, :] = [sel, cliente, abogado, expediente, anio, materia, pretension, obs, estado, str(fecha_inicio)]
                    save_df("casos", casos)
                    st.success("✅ Caso actualizado")
                    st.rerun()

    elif accion == "Eliminar":
        if casos.empty:
            st.info("No hay casos.")
        else:
            sel = st.selectbox("Caso (ID) a eliminar", casos["ID"].tolist())
            fila = casos[casos["ID"] == sel].iloc[0]
            st.warning(f"⚠️ Se eliminará el caso: {fila['Expediente']}")
            if st.button("Eliminar caso"):
                casos = casos[casos["ID"] != sel].copy()
                save_df("casos", casos)
                st.success("🗑️ Caso eliminado")
                st.rerun()

    st.subheader("Listado")
    st.dataframe(casos, use_container_width=True)

# =========================
# FICHA DEL CASO (Pestañas)
# =========================
if menu == "Ficha del Caso":
    st.title("📁 Ficha del Caso")

    if casos.empty:
        st.info("Primero registra un caso.")
    else:
        exp = st.selectbox("Selecciona expediente", casos["Expediente"].tolist())
        f, pagosH, pagosL, cuotasExp = estado_cuenta_expediente(exp)

        tabs = st.tabs(["Datos", "Pagos", "Cuotas", "Actuaciones", "Documentos", "Estado de cuenta"])

        with tabs[0]:
            st.subheader("Datos del caso")
            st.dataframe(casos[casos["Expediente"] == exp], use_container_width=True)

        with tabs[1]:
            st.subheader("Pagos Honorarios")
            st.dataframe(pagos_honorarios[pagos_honorarios["Caso"] == exp], use_container_width=True)
            st.subheader("Pagos Cuota Litis")
            st.dataframe(pagos_litis[pagos_litis["Caso"] == exp], use_container_width=True)

        with tabs[2]:
            st.subheader("Cuotas (cronograma)")
            st.dataframe(cuotas[cuotas["Caso"] == exp], use_container_width=True)
            st.subheader("Estado cuotas (asignación automática de pagos)")
            if cuotasExp is None or cuotasExp.empty:
                st.info("No hay cuotas registradas para este caso.")
            else:
                st.dataframe(cuotasExp, use_container_width=True)

        with tabs[3]:
            st.subheader("Actuaciones del caso (timeline)")
            st.dataframe(actuaciones[actuaciones["Caso"] == exp].sort_values("Fecha", ascending=False), use_container_width=True)

        with tabs[4]:
            st.subheader("Documentos del caso")
            st.dataframe(documentos[documentos["Caso"] == exp].sort_values("Fecha", ascending=False), use_container_width=True)

        with tabs[5]:
            st.subheader("Estado de cuenta")
            if f is None:
                st.info("No hay datos de estado de cuenta.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Honorario pactado (S/)", f"{money(f['Honorario Pactado']):,.2f}")
                c2.metric("Honorario pagado (S/)", f"{money(f['Honorario Pagado']):,.2f}")
                c3.metric("Saldo honorarios (S/)", f"{money(f['Honorario Pendiente']):,.2f}")

                d1, d2, d3 = st.columns(3)
                d1.metric("Cuota litis calc. (S/)", f"{money(f['Cuota Litis Calculada']):,.2f}")
                d2.metric("Cuota litis pagada (S/)", f"{money(f['Pagado Litis']):,.2f}")
                d3.metric("Saldo cuota litis (S/)", f"{money(f['Saldo Litis']):,.2f}")

# =========================
# HONORARIOS
# =========================
if menu == "Honorarios":
    st.title("Honorarios Pactados")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        monto = st.number_input("Monto Pactado", min_value=0.0, step=50.0)
        if st.button("Guardar Honorario"):
            honorarios = add_row(honorarios, {"Caso": caso, "Monto Pactado": float(monto)}, "honorarios")
            save_df("honorarios", honorarios)
            st.success("✅ Guardado")
            st.rerun()

        st.subheader("Eliminar fila de honorarios")
        if not honorarios.empty:
            idx = st.selectbox("Fila (índice) a borrar", honorarios.index.tolist())
            if st.button("🗑️ Borrar fila honorarios"):
                honorarios = honorarios.drop(index=idx).reset_index(drop=True)
                save_df("honorarios", honorarios)
                st.success("✅ Borrado")
                st.rerun()

    st.dataframe(honorarios, use_container_width=True)

# =========================
# PAGOS HONORARIOS (Borrar incluido)
# =========================
if menu == "Pagos Honorarios":
    st.title("Pagos de Honorarios")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        fecha = st.date_input("Fecha de pago", value=date.today())
        monto = st.number_input("Monto Pagado", min_value=0.0, step=50.0)
        obs = st.text_input("Observación (opcional)")

        if st.button("Registrar Pago"):
            new_id = next_id(pagos_honorarios)
            pagos_honorarios = add_row(pagos_honorarios, {
                "ID": new_id, "Caso": caso, "FechaPago": str(fecha), "Monto": float(monto), "Observacion": obs
            }, "pagos_honorarios")
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Pago registrado")
            st.rerun()

        st.divider()
        st.subheader("Editar / Eliminar pago (Honorarios)")
        if pagos_honorarios.empty:
            st.info("No hay pagos.")
        else:
            sel = st.selectbox("Pago ID", pagos_honorarios["ID"].tolist())
            fila = pagos_honorarios[pagos_honorarios["ID"] == sel].iloc[0]
            with st.form("edit_pago_h"):
                caso_e = st.text_input("Caso", value=str(fila["Caso"]))
                fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
                monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
                obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
                saveb = st.form_submit_button("Guardar cambios")
                if saveb:
                    idx = pagos_honorarios.index[pagos_honorarios["ID"] == sel][0]
                    pagos_honorarios.loc[idx, :] = [sel, caso_e, fecha_e, float(monto_e), obs_e]
                    save_df("pagos_honorarios", pagos_honorarios)
                    st.success("✅ Actualizado")
                    st.rerun()

            if st.button("🗑️ Borrar pago honorarios"):
                pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
                save_df("pagos_honorarios", pagos_honorarios)
                st.success("✅ Pago eliminado")
                st.rerun()

    st.dataframe(pagos_honorarios, use_container_width=True)

# =========================
# CUOTA LITIS
# =========================
if menu == "Cuota Litis":
    st.title("Cuota Litis")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        base = st.number_input("Monto Base", min_value=0.0, step=100.0)
        porcentaje = st.number_input("Porcentaje (%)", min_value=0.0, step=1.0)

        if st.button("Guardar Cuota Litis"):
            cuota_litis = add_row(cuota_litis, {"Caso": caso, "Monto Base": float(base), "Porcentaje": float(porcentaje)}, "cuota_litis")
            save_df("cuota_litis", cuota_litis)
            st.success("✅ Guardado")
            st.rerun()

        st.subheader("Eliminar fila cuota litis")
        if not cuota_litis.empty:
            idx = st.selectbox("Fila (índice) a borrar", cuota_litis.index.tolist())
            if st.button("🗑️ Borrar fila cuota litis"):
                cuota_litis = cuota_litis.drop(index=idx).reset_index(drop=True)
                save_df("cuota_litis", cuota_litis)
                st.success("✅ Borrado")
                st.rerun()

    st.dataframe(cuota_litis, use_container_width=True)

# =========================
# PAGOS CUOTA LITIS (Borrar incluido)
# =========================
if menu == "Pagos Cuota Litis":
    st.title("Pagos Cuota Litis")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        fecha = st.date_input("Fecha de pago", value=date.today())
        monto = st.number_input("Monto Pagado", min_value=0.0, step=50.0)
        obs = st.text_input("Observación (opcional)")

        if st.button("Registrar Pago Litis"):
            new_id = next_id(pagos_litis)
            pagos_litis = add_row(pagos_litis, {
                "ID": new_id, "Caso": caso, "FechaPago": str(fecha), "Monto": float(monto), "Observacion": obs
            }, "pagos_litis")
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Pago registrado")
            st.rerun()

        st.divider()
        st.subheader("Editar / Eliminar pago (Cuota litis)")
        if pagos_litis.empty:
            st.info("No hay pagos.")
        else:
            sel = st.selectbox("Pago ID", pagos_litis["ID"].tolist())
            fila = pagos_litis[pagos_litis["ID"] == sel].iloc[0]
            with st.form("edit_pago_l"):
                caso_e = st.text_input("Caso", value=str(fila["Caso"]))
                fecha_e = st.text_input("FechaPago (YYYY-MM-DD)", value=str(fila["FechaPago"]))
                monto_e = st.number_input("Monto", min_value=0.0, value=money(fila["Monto"]), step=50.0)
                obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
                saveb = st.form_submit_button("Guardar cambios")
                if saveb:
                    idx = pagos_litis.index[pagos_litis["ID"] == sel][0]
                    pagos_litis.loc[idx, :] = [sel, caso_e, fecha_e, float(monto_e), obs_e]
                    save_df("pagos_litis", pagos_litis)
                    st.success("✅ Actualizado")
                    st.rerun()

            if st.button("🗑️ Borrar pago cuota litis"):
                pagos_litis = pagos_litis[pagos_litis["ID"] != sel].copy()
                save_df("pagos_litis", pagos_litis)
                st.success("✅ Pago eliminado")
                st.rerun()

    st.dataframe(pagos_litis, use_container_width=True)

# =========================
# CRONOGRAMA DE CUOTAS
# =========================
if menu == "Cronograma de Cuotas":
    st.title("📅 Cronograma de Cuotas")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        st.subheader("Agregar cuota")
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        tipo = st.selectbox("Tipo", ["Honorarios", "CuotaLitis"])
        fecha_venc = st.date_input("Fecha vencimiento", value=date.today())
        monto = st.number_input("Monto cuota", min_value=0.0, step=50.0)
        notas = st.text_input("Notas (opcional)")

        subset = cuotas[(cuotas["Caso"] == caso) & (cuotas["Tipo"] == tipo)].copy()
        nro = int(pd.to_numeric(subset["NroCuota"], errors="coerce").max()) + 1 if not subset.empty else 1

        if st.button("Guardar cuota"):
            new_id = next_id(cuotas)
            cuotas = add_row(cuotas, {
                "ID": new_id, "Caso": caso, "Tipo": tipo, "NroCuota": nro,
                "FechaVenc": str(fecha_venc), "Monto": float(monto), "Notas": notas
            }, "cuotas")
            save_df("cuotas", cuotas)
            st.success("✅ Cuota agregada")
            st.rerun()

    st.divider()
    st.subheader("Estado cuotas (asignación automática de pagos)")
    df_status = cuotas_status_all()
    st.dataframe(df_status, use_container_width=True)

    st.subheader("Eliminar cuota")
    if not cuotas.empty:
        sel_id = st.selectbox("Cuota ID a eliminar", cuotas["ID"].tolist())
        if st.button("🗑️ Eliminar cuota"):
            cuotas = cuotas[cuotas["ID"] != sel_id].copy()
            save_df("cuotas", cuotas)
            st.success("✅ Cuota eliminada")
            st.rerun()

# =========================
# ACTUACIONES
# =========================
if menu == "Actuaciones":
    st.title("🧾 Actuaciones / Seguimiento procesal (Timeline)")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        with st.form("nueva_act"):
            fecha = st.date_input("Fecha", value=date.today())
            tipo = st.text_input("Tipo de actuación (ej: Demanda, Audiencia, Sentencia, Apelación...)")
            resumen = st.text_area("Resumen")
            prox = st.text_input("Próxima acción (opcional)")
            prox_fecha = st.text_input("Fecha próxima acción (YYYY-MM-DD opcional)")
            notas = st.text_input("Notas (opcional)")
            submit = st.form_submit_button("Guardar actuación")
            if submit:
                new_id = next_id(actuaciones)
                actuaciones = add_row(actuaciones, {
                    "ID": new_id, "Caso": caso, "Fecha": str(fecha),
                    "TipoActuacion": tipo, "Resumen": resumen,
                    "ProximaAccion": prox, "FechaProximaAccion": prox_fecha,
                    "Notas": notas
                }, "actuaciones")
                save_df("actuaciones", actuaciones)
                st.success("✅ Actuación registrada")
                st.rerun()

        st.divider()
        st.subheader("Listado por caso")
        st.dataframe(actuaciones[actuaciones["Caso"] == caso].sort_values("Fecha", ascending=False), use_container_width=True)

        st.subheader("Eliminar actuación")
        acts = actuaciones[actuaciones["Caso"] == caso].copy()
        if not acts.empty:
            sel = st.selectbox("Actuación ID a borrar", acts["ID"].tolist())
            if st.button("🗑️ Eliminar actuación"):
                actuaciones = actuaciones[actuaciones["ID"] != sel].copy()
                save_df("actuaciones", actuaciones)
                st.success("✅ Eliminada")
                st.rerun()

# =========================
# DOCUMENTOS (subida)
# =========================
if menu == "Documentos":
    st.title("📎 Documentos")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        tipo = st.selectbox("Tipo", ["Contrato","Escrito","Resolución","Anexo","Otro"])
        notas = st.text_input("Notas (opcional)")

        up = st.file_uploader("Subir archivo", type=None)
        if st.button("Guardar documento"):
            if up is None:
                st.error("Sube un archivo primero.")
            else:
                exp_dir = os.path.join(UPLOADS_DIR, caso.replace("/", "_"))
                os.makedirs(exp_dir, exist_ok=True)
                filename = up.name
                path = os.path.join(exp_dir, filename)
                with open(path, "wb") as f:
                    f.write(up.getbuffer())

                new_id = next_id(documentos)
                documentos = add_row(documentos, {
                    "ID": new_id, "Caso": caso, "Tipo": tipo,
                    "NombreArchivo": filename, "Ruta": path,
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Notas": notas
                }, "documentos")
                save_df("documentos", documentos)
                st.success("✅ Documento guardado")
                st.rerun()

        st.divider()
        st.subheader("Listado documentos del caso")
        docs_case = documentos[documentos["Caso"] == caso].copy()
        st.dataframe(docs_case.sort_values("Fecha", ascending=False), use_container_width=True)

        st.subheader("Descargar / Eliminar")
        if not docs_case.empty:
            sel = st.selectbox("Documento ID", docs_case["ID"].tolist())
            row = docs_case[docs_case["ID"] == sel].iloc[0]
            file_path = row["Ruta"]
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.download_button("⬇️ Descargar archivo", f, file_name=row["NombreArchivo"])
            if st.button("🗑️ Eliminar registro documento"):
                documentos = documentos[documentos["ID"] != sel].copy()
                save_df("documentos", documentos)
                st.success("✅ Eliminado")
                st.rerun()

# =========================
# PLANTILLAS DE CONTRATO (CRUD)
# =========================
if menu == "Plantillas de Contrato":
    st.title("📝 Plantillas de Contrato (Modelos)")

    accion = st.radio("Acción", ["Nueva", "Editar", "Eliminar"], horizontal=True)

    st.info("Usa placeholders tipo {{CLIENTE_NOMBRE}}, {{CLIENTE_DNI}}, {{EXPEDIENTE}}, {{MATERIA}}, {{MONTO_PACTADO}}, {{PORCENTAJE_LITIS}}, etc.")

    if accion == "Nueva":
        with st.form("new_tpl"):
            nombre = st.text_input("Nombre de plantilla")
            contenido = st.text_area("Contenido (texto del contrato)", height=300)
            notas = st.text_input("Notas (opcional)")
            submit = st.form_submit_button("Guardar plantilla")
            if submit:
                new_id = next_id(plantillas)
                plantillas = add_row(plantillas, {
                    "ID": new_id,
                    "Nombre": nombre,
                    "Contenido": contenido,
                    "Notas": notas,
                    "Creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, "plantillas")
                save_df("plantillas", plantillas)
                st.success("✅ Plantilla guardada")
                st.rerun()

    elif accion == "Editar":
        if plantillas.empty:
            st.info("No hay plantillas.")
        else:
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

    elif accion == "Eliminar":
        if plantillas.empty:
            st.info("No hay plantillas.")
        else:
            sel = st.selectbox("Plantilla ID a eliminar", plantillas["ID"].tolist())
            if st.button("🗑️ Eliminar plantilla"):
                plantillas = plantillas[plantillas["ID"] != sel].copy()
                save_df("plantillas", plantillas)
                st.success("✅ Eliminada")
                st.rerun()

    st.subheader("Listado")
    st.dataframe(plantillas[["ID","Nombre","Notas","Creado"]], use_container_width=True)

# =========================
# GENERAR CONTRATO AUTOMÁTICO
# =========================
def build_context(expediente: str):
    caso_row = casos[casos["Expediente"] == expediente]
    if caso_row.empty:
        return {}
    c = caso_row.iloc[0]

    cli_row = clientes[clientes["Nombre"] == c["Cliente"]]
    cli = cli_row.iloc[0] if not cli_row.empty else None

    hon = safe_float_series(honorarios[honorarios["Caso"] == expediente]["Monto Pactado"]).sum()
    base = safe_float_series(cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"]).sum()
    porc = safe_float_series(cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"])
    porc_val = float(porc.iloc[-1]) if len(porc) else 0.0

    pagH = safe_float_series(pagos_honorarios[pagos_honorarios["Caso"] == expediente]["Monto"]).sum()
    pagL = safe_float_series(pagos_litis[pagos_litis["Caso"] == expediente]["Monto"]).sum()

    ctx = {
        "{{EXPEDIENTE}}": str(expediente),
        "{{MATERIA}}": str(c["Materia"]),
        "{{PRETENSION}}": str(c["Pretension"]),
        "{{CLIENTE_NOMBRE}}": str(c["Cliente"]),
        "{{ABOGADO_NOMBRE}}": str(c["Abogado"]),
        "{{MONTO_PACTADO}}": f"{hon:.2f}",
        "{{PAGADO_HONORARIOS}}": f"{pagH:.2f}",
        "{{SALDO_HONORARIOS}}": f"{(hon-pagH):.2f}",
        "{{MONTO_BASE}}": f"{base:.2f}",
        "{{PORCENTAJE_LITIS}}": f"{porc_val:.2f}",
        "{{PAGADO_LITIS}}": f"{pagL:.2f}",
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
    st.title("📄 Generar contrato automáticamente")

    if plantillas.empty:
        st.info("Primero crea una plantilla en 'Plantillas de Contrato'.")
    elif casos.empty:
        st.info("Primero registra casos.")
    else:
        exp = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        tpl_id = st.selectbox("Plantilla", plantillas["ID"].tolist())
        tpl = plantillas[plantillas["ID"] == tpl_id].iloc[0]
        ctx = build_context(exp)
        generado = render_template(str(tpl["Contenido"]), ctx)

        st.subheader("Vista previa")
        st.text_area("Contrato generado", value=generado, height=350)

        nombre_archivo = f"Contrato_{exp.replace('/','_')}_{tpl['Nombre'].replace(' ','_')}.txt"
        st.download_button("⬇️ Descargar contrato (TXT)", data=generado.encode("utf-8"), file_name=nombre_archivo)

        if st.button("💾 Guardar contrato en 'generados/'"):
            out_path = os.path.join(GENERADOS_DIR, nombre_archivo)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(generado)
            st.success(f"✅ Guardado en: {out_path}")

        st.divider()
        st.subheader("Placeholders disponibles (más usados)")
        st.code(
            "\n".join(sorted(list(build_context(exp).keys()))),
            language="text"
        )

# =========================
# REPORTES
# =========================
if menu == "Reportes":
    st.title("📈 Reportes")

    df_res = resumen_financiero_df()
    scli = saldo_por_cliente()

    tab1, tab2, tab3 = st.tabs(["Saldos por cliente", "Saldos por caso", "Exportaciones"])

    with tab1:
        st.subheader("Saldos por cliente (sumando todos los casos) ✅")
        st.dataframe(scli, use_container_width=True)

    with tab2:
        st.subheader("Saldos por caso")
        st.dataframe(df_res, use_container_width=True)

    with tab3:
        st.subheader("Exportar CSV")
        st.download_button("Descargar reporte por cliente (CSV)", scli.to_csv(index=False).encode("utf-8"), "reporte_clientes.csv")
        st.download_button("Descargar reporte por casos (CSV)", df_res.to_csv(index=False).encode("utf-8"), "reporte_casos.csv")

# =========================
# USUARIOS (CRUD + roles)
# =========================
if menu == "Usuarios":
    st.title("👥 Usuarios")
    if st.session_state.rol != "admin":
        st.error("Solo admin puede administrar usuarios.")
    else:
        users = load_df("usuarios")
        accion = st.radio("Acción", ["Nuevo", "Cambiar contraseña", "Activar/Desactivar", "Eliminar"], horizontal=True)

        if accion == "Nuevo":
            with st.form("new_user"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                rol = st.selectbox("Rol", ["admin","usuario"])
                submit = st.form_submit_button("Crear usuario")
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
            estado = row["Activo"]
            st.write("Estado actual:", "Activo" if str(estado) == "1" else "Inactivo")
            if st.button("Alternar estado"):
                idx = users.index[users["Usuario"] == sel][0]
                users.loc[idx, "Activo"] = "0" if str(estado) == "1" else "1"
                save_df("usuarios", users)
                st.success("✅ Estado actualizado")
                st.rerun()

        elif accion == "Eliminar":
            sel = st.selectbox("Usuario a eliminar", users["Usuario"].tolist())
            if sel == "admin":
                st.error("No puedes eliminar admin.")
            else:
                if st.button("🗑️ Eliminar usuario"):
                    users = users[users["Usuario"] != sel].copy()
                    save_df("usuarios", users)
                    st.success("✅ Usuario eliminado")
                    st.rerun()

        st.subheader("Listado")
        st.dataframe(users[["Usuario","Rol","Activo","Creado"]], use_container_width=True)

# =========================
# RESUMEN FINANCIERO (pantalla)
# =========================
if menu == "Resumen Financiero":
    st.title("Resumen Financiero")
    df_res = resumen_financiero_df()
    st.dataframe(df_res, use_container_width=True)

    st.subheader("Pendientes por cronograma (cuotas)")
    df_status = cuotas_status_all()
    df_pend = cuotas_pendientes(df_status)
    st.dataframe(df_pend, use_container_width=True)
