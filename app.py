import streamlit as st
import pandas as pd
import os
import hashlib
import shutil
from datetime import date, datetime

# ==========================================================
# MARCA 006 – SISTEMA INTEGRAL (CAMBIOS 1 AL 19)
# Estudio Jurídico Roncal Liñan y Asociados
# ==========================================================

APP_VERSION = "MARCA 006"
APP_NAME = "Estudio Jurídico Roncal Liñan y Asociados"

# ==========================================================
# SEGURIDAD / SECRETS
# ==========================================================
CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")
ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")
PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")

# ==========================================================
# DIRECTORIOS
# ==========================================================
DATA_DIR = "."
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
GENERADOS_DIR = os.path.join(DATA_DIR, "generados")

for d in [BACKUP_DIR, UPLOADS_DIR, GENERADOS_DIR]:
    os.makedirs(d, exist_ok=True)

st.set_page_config(
    page_title=f"⚖️ {APP_NAME} – {APP_VERSION}",
    layout="wide"
)

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
    "honorarios_tipo": "honorarios_tipo.csv",

    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",
    "cuotas": "cuotas.csv",

    "actuaciones": "actuaciones.csv",
    "instancias": "instancias.csv",

    "consultas": "consultas.csv",
    "documentos": "documentos.csv",

    "plantillas": "plantillas_contratos.csv",
    "contratos": "contratos.csv",

    "auditoria_mod": "auditoria_mod.csv",
}

# ==========================================================
# ESQUEMAS (COMPLETOS – SIN KEYERROR)
# ==========================================================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","AbogadoID","Activo","Creado"],

    "clientes": [
        "ID","TipoCliente","Nombre","DNI","Celular","Correo","Direccion","Observaciones",
        "ContactoEmergencia","CelularEmergencia",
        "RazonSocial","RUC","RepresentanteLegal","PartidaElectronica","SedeRegistral"
    ],

    "abogados": [
        "ID","Nombre","DNI","Celular","Correo","Colegiatura",
        "ColegioProfesional","DistritoJudicial",
        "Domicilio Procesal","ReferenciaDomicilio",
        "Casilla Electronica","Casilla Judicial",
        "Notas"
    ],

    "casos": [
        "ID","Cliente","Abogado","Expediente","Año","Materia","Instancia","Pretension",
        "Juzgado","DistritoJudicial","Contraparte","ContraparteDoc",
        "Observaciones","EstadoCaso","FechaInicio"
    ],

    "instancias": [
        "ID","Caso","TipoInstancia","EstadoActual",
        "Resultado","Accion","Honorarios","FechaRegistro"
    ],

    "honorarios": ["ID","Caso","Monto Pactado","Notas","FechaRegistro"],

    "honorarios_etapas": ["ID","Caso","Etapa","Monto Pactado","Notas","FechaRegistro"],

    "honorarios_tipo": ["ID","Caso","Tipo","Monto","Notas","FechaRegistro"],

    "pagos_honorarios": ["ID","Caso","Etapa","FechaPago","Monto","Observacion"],

    "cuota_litis": ["ID","Caso","Monto Base","Porcentaje","Notas","FechaRegistro"],

    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],

    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"],

    "actuaciones": [
        "ID","Caso","Cliente","Fecha","TipoActuacion","Resumen",
        "ProximaAccion","FechaProximaAccion",
        "CostasAranceles","Gastos",
        "LinkOneDrive","Notas"
    ],

    "consultas": [
        "ID","Fecha","Cliente","Caso","Abogado",
        "Consulta","Estrategia",
        "CostoConsulta","HonorariosPropuestos",
        "Proforma","LinkOneDrive","Notas"
    ],

    "documentos": ["ID","Caso","Tipo","NombreArchivo","Ruta","Fecha","Notas"],

    "plantillas": ["ID","Nombre","Contenido","Notas","Creado"],

    "contratos": [
        "ID","Numero","Año","Sigla","NombreContrato",
        "Caso","Cliente","Abogado","Estado","Archivo","Fecha"
    ],

    "auditoria_mod": [
        "ID","Fecha","Usuario","Rol","Accion","Entidad","EntidadID","Detalle"
    ],
}

# ==========================================================
# UTILIDADES BÁSICAS
# ==========================================================
def sha256(text: str) -> str:
    base = (PASSWORD_PEPPER or "") + str(text)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
import streamlit as st
import pandas as pd
import os
import hashlib
import shutil
from datetime import date, datetime

# ==========================================================
# MARCA 006 – SISTEMA INTEGRAL (CAMBIOS 1 AL 19)
# Estudio Jurídico Roncal Liñan y Asociados
# ==========================================================

APP_VERSION = "MARCA 006"
APP_NAME = "Estudio Jurídico Roncal Liñan y Asociados"

# ==========================================================
# SEGURIDAD / SECRETS
# ==========================================================
CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")
ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")
PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")

# ==========================================================
# DIRECTORIOS
# ==========================================================
DATA_DIR = "."
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
GENERADOS_DIR = os.path.join(DATA_DIR, "generados")

for d in [BACKUP_DIR, UPLOADS_DIR, GENERADOS_DIR]:
    os.makedirs(d, exist_ok=True)

st.set_page_config(
    page_title=f"⚖️ {APP_NAME} – {APP_VERSION}",
    layout="wide"
)

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
    "honorarios_tipo": "honorarios_tipo.csv",

    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",
    "cuotas": "cuotas.csv",

    "actuaciones": "actuaciones.csv",
    "instancias": "instancias.csv",

    "consultas": "consultas.csv",
    "documentos": "documentos.csv",

    "plantillas": "plantillas_contratos.csv",
    "contratos": "contratos.csv",

    "auditoria_mod": "auditoria_mod.csv",
}

# ==========================================================
# ESQUEMAS (COMPLETOS – SIN KEYERROR)
# ==========================================================
SCHEMAS = {
    "usuarios": ["Usuario","PasswordHash","Rol","AbogadoID","Activo","Creado"],

    "clientes": [
        "ID","TipoCliente","Nombre","DNI","Celular","Correo","Direccion","Observaciones",
        "ContactoEmergencia","CelularEmergencia",
        "RazonSocial","RUC","RepresentanteLegal","PartidaElectronica","SedeRegistral"
    ],

    "abogados": [
        "ID","Nombre","DNI","Celular","Correo","Colegiatura",
        "ColegioProfesional","DistritoJudicial",
        "Domicilio Procesal","ReferenciaDomicilio",
        "Casilla Electronica","Casilla Judicial",
        "Notas"
    ],

    "casos": [
        "ID","Cliente","Abogado","Expediente","Año","Materia","Instancia","Pretension",
        "Juzgado","DistritoJudicial","Contraparte","ContraparteDoc",
        "Observaciones","EstadoCaso","FechaInicio"
    ],

    "instancias": [
        "ID","Caso","TipoInstancia","EstadoActual",
        "Resultado","Accion","Honorarios","FechaRegistro"
    ],

    "honorarios": ["ID","Caso","Monto Pactado","Notas","FechaRegistro"],

    "honorarios_etapas": ["ID","Caso","Etapa","Monto Pactado","Notas","FechaRegistro"],

    "honorarios_tipo": ["ID","Caso","Tipo","Monto","Notas","FechaRegistro"],

    "pagos_honorarios": ["ID","Caso","Etapa","FechaPago","Monto","Observacion"],

    "cuota_litis": ["ID","Caso","Monto Base","Porcentaje","Notas","FechaRegistro"],

    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],

    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"],

    "actuaciones": [
        "ID","Caso","Cliente","Fecha","TipoActuacion","Resumen",
        "ProximaAccion","FechaProximaAccion",
        "CostasAranceles","Gastos",
        "LinkOneDrive","Notas"
    ],

    "consultas": [
        "ID","Fecha","Cliente","Caso","Abogado",
        "Consulta","Estrategia",
        "CostoConsulta","HonorariosPropuestos",
        "Proforma","LinkOneDrive","Notas"
    ],

    "documentos": ["ID","Caso","Tipo","NombreArchivo","Ruta","Fecha","Notas"],

    "plantillas": ["ID","Nombre","Contenido","Notas","Creado"],

    "contratos": [
        "ID","Numero","Año","Sigla","NombreContrato",
        "Caso","Cliente","Abogado","Estado","Archivo","Fecha"
    ],

    "auditoria_mod": [
        "ID","Fecha","Usuario","Rol","Accion","Entidad","EntidadID","Detalle"
    ],
}

# ==========================================================
# UTILIDADES BÁSICAS
# ==========================================================
def sha256(text: str) -> str:
    base = (PASSWORD_PEPPER or "") + str(text)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
# ==========================================================
# BLOQUE 3 – CORRECCIONES + DASHBOARD + CRUD (Clientes/Abogados/Casos) + INSTANCIAS + CONTRATOS
# ==========================================================

# ----------------------------------------------------------
# 0) FIX: Re-define load_df / save_df / add_row (sobrescribe bugs del bloque anterior)
# ----------------------------------------------------------
def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    try:
        df = pd.read_csv(FILES[key])
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=SCHEMAS[key])
    except Exception:
        df = pd.DataFrame(columns=SCHEMAS[key])

    df = drop_unnamed(df)
    # Asegurar columnas del esquema
    for col in SCHEMAS[key]:
        if col not in df.columns:
            df[col] = ""
    df = df.reindex(columns=SCHEMAS[key])
    return df

def save_df(key: str, df: pd.DataFrame):
    backup_file(FILES[key])
    df = drop_unnamed(df)
    # Asegurar columnas del esquema
    for col in SCHEMAS[key]:
        if col not in df.columns:
            df[col] = ""
    df = df.reindex(columns=SCHEMAS[key])
    df.to_csv(FILES[key], index=False)

def add_row(df: pd.DataFrame, row_dict: dict, schema_key: str) -> pd.DataFrame:
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    for col in SCHEMAS[schema_key]:
        if col not in df2.columns:
            df2[col] = ""
    df2 = df2.reindex(columns=SCHEMAS[schema_key])
    return df2

# ----------------------------------------------------------
# 1) Roles (asistente solo lectura)
# ----------------------------------------------------------
def is_readonly():
    return st.session_state.get("rol") == "asistente"

def can_edit():
    return st.session_state.get("rol") in ["admin", "abogado"]

# ----------------------------------------------------------
# 2) Filtro de casos por rol (abogado solo sus casos)
# ----------------------------------------------------------
def abogado_nombre_desde_id():
    try:
        aid = str(st.session_state.get("abogado_id", "")).strip()
        if not aid:
            return None
        df = abogados.copy()
        hit = df[df["ID"].astype(str) == aid]
        if hit.empty:
            return None
        return str(hit.iloc[0].get("Nombre", "")).strip()
    except Exception:
        return None

def filter_casos_por_rol(df_casos: pd.DataFrame) -> pd.DataFrame:
    if st.session_state.get("rol") == "abogado":
        nombre = abogado_nombre_desde_id()
        if nombre:
            return df_casos[df_casos["Abogado"].astype(str) == nombre].copy()
    return df_casos

# aplicar filtro visual solo a la variable casos (no destruye CSV)
try:
    casos = filter_casos_por_rol(casos)
except Exception:
    pass

# ==========================================================
# 3) FINANZAS BASE (resumen + estado de cuotas)
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
# 4) DASHBOARD con semáforo de actuaciones pendientes
# ==========================================================
if "menu" in globals() and menu == "Dashboard"":
    st.subheader("📊 Dashboard General")

    df_res = resumen_financiero_df()
    df_estado = cuotas_status_all()

    r1c1, r1c2, r1c3 = st.columns(3)
    r1c1.metric("👥 Clientes", f"{len(clientes)}")
    r1c2.metric("👨‍⚖️ Abogados", f"{len(abogados)}")
    r1c3.metric("📁 Casos", f"{len(casos)}")

    st.markdown("### 💰 Indicadores Económicos")
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

    st.divider()
    st.markdown("### ⏱️ Actuaciones pendientes (semáforo)")
    if actuaciones.empty:
        st.info("No hay actuaciones registradas.")
    else:
        def _dias(x):
            d = to_date_safe(x)
            return None if d is None else (d - date.today()).days

        tmp = actuaciones.copy()
        tmp["Dias"] = tmp["FechaProximaAccion"].apply(_dias)
        tmp = tmp[tmp["Dias"].notna()].copy()
        tmp = tmp[tmp["Dias"] >= 0].copy()

        def _sem(d):
            if d <= 2: return "🔴"
            if 3 <= d <= 5: return "🟡"
            return "🟢"

        tmp["Sem"] = tmp["Dias"].apply(_sem)
        tmp.sort_values("Dias", inplace=True)
        st.dataframe(tmp[["Sem","Caso","TipoActuacion","ProximaAccion","FechaProximaAccion","Dias"]], use_container_width=True)

# ==========================================================
# 5) CLIENTES (CRUD + extendido integrado)
# ==========================================================
if menu == "Clientes":
    st.subheader("👥 Clientes")
    accion = st.radio("Acción", ["Nuevo","Editar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        with st.form("nuevo_cliente"):
            tipo = st.selectbox("Tipo de cliente", ["Natural","Jurídica"])
            nombre = st.text_input("Nombre")
            dni = st.text_input("DNI")
            celular = st.text_input("Celular")
            correo = st.text_input("Correo")
            direccion = st.text_input("Dirección")
            obs = st.text_area("Observaciones")

            # Emergencia
            contacto = st.text_input("Contacto de emergencia")
            cel_em = st.text_input("Celular de contacto (emergencia)")

            # Jurídica
            rs = st.text_input("Razón Social (si jurídica)")
            ruc = st.text_input("RUC (si jurídica)")
            rep = st.text_input("Representante legal")
            partida = st.text_input("Partida electrónica")
            sede = st.text_input("Sede registral")

            submit = st.form_submit_button("Guardar", disabled=is_readonly())
            if submit:
                new_id = next_id(clientes)
                clientes = add_row(clientes, {
                    "ID": new_id,
                    "TipoCliente": tipo,
                    "Nombre": nombre,
                    "DNI": dni,
                    "Celular": celular,
                    "Correo": correo,
                    "Direccion": direccion,
                    "Observaciones": obs,
                    "ContactoEmergencia": contacto,
                    "CelularEmergencia": cel_em,
                    "RazonSocial": rs,
                    "RUC": ruc,
                    "RepresentanteLegal": rep,
                    "PartidaElectronica": partida,
                    "SedeRegistral": sede
                }, "clientes")
                save_df("clientes", clientes)
                audit_log("ADD","clientes",new_id,nombre)
                st.success("✅ Cliente registrado")
                st.rerun()

    elif accion == "Editar" and not clientes.empty:
        sel = st.selectbox("Cliente ID", clientes["ID"].tolist())
        fila = clientes[clientes["ID"] == sel].iloc[0]

        with st.form("edit_cliente"):
            tipo = st.selectbox("Tipo de cliente", ["Natural","Jurídica"], index=0 if str(fila.get("TipoCliente","Natural"))!="Jurídica" else 1)
            nombre = st.text_input("Nombre", value=str(fila.get("Nombre","")))
            dni = st.text_input("DNI", value=str(fila.get("DNI","")))
            celular = st.text_input("Celular", value=str(fila.get("Celular","")))
            correo = st.text_input("Correo", value=str(fila.get("Correo","")))
            direccion = st.text_input("Dirección", value=str(fila.get("Direccion","")))
            obs = st.text_area("Observaciones", value=str(fila.get("Observaciones","")))

            contacto = st.text_input("Contacto de emergencia", value=str(fila.get("ContactoEmergencia","")))
            cel_em = st.text_input("Celular de contacto (emergencia)", value=str(fila.get("CelularEmergencia","")))

            rs = st.text_input("Razón Social (si jurídica)", value=str(fila.get("RazonSocial","")))
            ruc = st.text_input("RUC (si jurídica)", value=str(fila.get("RUC","")))
            rep = st.text_input("Representante legal", value=str(fila.get("RepresentanteLegal","")))
            partida = st.text_input("Partida electrónica", value=str(fila.get("PartidaElectronica","")))
            sede = st.text_input("Sede registral", value=str(fila.get("SedeRegistral","")))

            submit = st.form_submit_button("Guardar cambios", disabled=is_readonly())
            if submit:
                idx = clientes.index[clientes["ID"] == sel][0]
                clientes.loc[idx, :] = clientes.loc[idx, :].copy()
                clientes.loc[idx, "TipoCliente"] = tipo
                clientes.loc[idx, "Nombre"] = nombre
                clientes.loc[idx, "DNI"] = dni
                clientes.loc[idx, "Celular"] = celular
                clientes.loc[idx, "Correo"] = correo
                clientes.loc[idx, "Direccion"] = direccion
                clientes.loc[idx, "Observaciones"] = obs
                clientes.loc[idx, "ContactoEmergencia"] = contacto
                clientes.loc[idx, "CelularEmergencia"] = cel_em
                clientes.loc[idx, "RazonSocial"] = rs
                clientes.loc[idx, "RUC"] = ruc
                clientes.loc[idx, "RepresentanteLegal"] = rep
                clientes.loc[idx, "PartidaElectronica"] = partida
                clientes.loc[idx, "SedeRegistral"] = sede
                save_df("clientes", clientes)
                audit_log("UPDATE","clientes",sel,nombre)
                st.success("✅ Actualizado")
                st.rerun()

    elif accion == "Eliminar" and not clientes.empty:
        sel = st.selectbox("Cliente ID a eliminar", clientes["ID"].tolist())
        if st.button("Eliminar cliente", disabled=is_readonly()):
            clientes = clientes[clientes["ID"] != sel].copy()
            save_df("clientes", clientes)
            audit_log("DELETE","clientes",sel,"")
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(clientes, use_container_width=True)
    st.download_button("⬇️ Descargar clientes (CSV)", clientes.to_csv(index=False).encode("utf-8"), "clientes.csv")

# ==========================================================
# 6) ABOGADOS (CRUD + campos extendidos integrados)
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

            # nuevos
            colegio_prof = st.text_input("Colegio Profesional (texto libre)")
            distrito_jud = st.text_input("Distrito Judicial (texto libre)")

            dom = st.text_input("Domicilio Procesal")
            referencia = st.text_input("Referencia del Domicilio Procesal")

            cas_e = st.text_input("Casilla Electrónica")
            cas_j = st.text_input("Casilla Judicial")
            notas = st.text_area("Notas del abogado", height=120)

            submit = st.form_submit_button("Guardar", disabled=is_readonly())
            if submit:
                new_id = next_id(abogados)
                abogados = add_row(abogados, {
                    "ID": new_id,
                    "Nombre": nombre,
                    "DNI": dni,
                    "Celular": celular,
                    "Correo": correo,
                    "Colegiatura": coleg,
                    "ColegioProfesional": colegio_prof,
                    "DistritoJudicial": distrito_jud,
                    "Domicilio Procesal": dom,
                    "ReferenciaDomicilio": referencia,
                    "Casilla Electronica": cas_e,
                    "Casilla Judicial": cas_j,
                    "Notas": notas
                }, "abogados")
                save_df("abogados", abogados)
                audit_log("ADD","abogados",new_id,nombre)
                st.success("✅ Abogado registrado")
                st.rerun()

    elif accion == "Editar" and not abogados.empty:
        sel = st.selectbox("Abogado ID", abogados["ID"].tolist())
        fila = abogados[abogados["ID"] == sel].iloc[0]

        with st.form("edit_abogado"):
            nombre = st.text_input("Nombre", value=str(fila.get("Nombre","")))
            dni = st.text_input("DNI", value=str(fila.get("DNI","")))
            celular = st.text_input("Celular", value=str(fila.get("Celular","")))
            correo = st.text_input("Correo", value=str(fila.get("Correo","")))
            coleg = st.text_input("Colegiatura", value=str(fila.get("Colegiatura","")))

            colegio_prof = st.text_input("Colegio Profesional", value=str(fila.get("ColegioProfesional","")))
            distrito_jud = st.text_input("Distrito Judicial", value=str(fila.get("DistritoJudicial","")))

            dom = st.text_input("Domicilio Procesal", value=str(fila.get("Domicilio Procesal","")))
            referencia = st.text_input("Referencia del Domicilio Procesal", value=str(fila.get("ReferenciaDomicilio","")))

            cas_e = st.text_input("Casilla Electrónica", value=str(fila.get("Casilla Electronica","")))
            cas_j = st.text_input("Casilla Judicial", value=str(fila.get("Casilla Judicial","")))
            notas = st.text_area("Notas del abogado", value=str(fila.get("Notas","")), height=120)

            submit = st.form_submit_button("Guardar cambios", disabled=is_readonly())
            if submit:
                idx = abogados.index[abogados["ID"] == sel][0]
                abogados.loc[idx, "Nombre"] = nombre
                abogados.loc[idx, "DNI"] = dni
                abogados.loc[idx, "Celular"] = celular
                abogados.loc[idx, "Correo"] = correo
                abogados.loc[idx, "Colegiatura"] = coleg
                abogados.loc[idx, "ColegioProfesional"] = colegio_prof
                abogados.loc[idx, "DistritoJudicial"] = distrito_jud
                abogados.loc[idx, "Domicilio Procesal"] = dom
                abogados.loc[idx, "ReferenciaDomicilio"] = referencia
                abogados.loc[idx, "Casilla Electronica"] = cas_e
                abogados.loc[idx, "Casilla Judicial"] = cas_j
                abogados.loc[idx, "Notas"] = notas
                save_df("abogados", abogados)
                audit_log("UPDATE","abogados",sel,nombre)
                st.success("✅ Actualizado")
                st.rerun()

    elif accion == "Eliminar" and not abogados.empty:
        sel = st.selectbox("Abogado ID a eliminar", abogados["ID"].tolist())
        if st.button("Eliminar abogado", disabled=is_readonly()):
            abogados = abogados[abogados["ID"] != sel].copy()
            save_df("abogados", abogados)
            audit_log("DELETE","abogados",sel,"")
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(abogados, use_container_width=True)
    st.download_button("⬇️ Descargar abogados (CSV)", abogados.to_csv(index=False).encode("utf-8"), "abogados.csv")
# ==========================================================
# BLOQUE 4 – CASOS/INSTANCIAS/FINANZAS/CONTRATOS (COMPLETO)
# ==========================================================

# ----------------------------------------------------------
# 0) FIX DEFINITIVO: Sobrescribe helpers con versiones correctas (evita errores previos)
# ----------------------------------------------------------
def _ensure_schema_cols(df: pd.DataFrame, key: str) -> pd.DataFrame:
    cols = SCHEMAS[key]
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    return df.reindex(columns=cols)

def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    try:
        df = pd.read_csv(FILES[key])
    except Exception:
        df = pd.DataFrame(columns=SCHEMAS[key])
    df = drop_unnamed(df)
    df = _ensure_schema_cols(df, key)
    return df

def save_df(key: str, df: pd.DataFrame):
    backup_file(FILES[key])
    df = drop_unnamed(df)
    df = _ensure_schema_cols(df, key)
    df.to_csv(FILES[key], index=False)

def add_row(df: pd.DataFrame, row_dict: dict, schema_key: str) -> pd.DataFrame:
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df2 = _ensure_schema_cols(df2, schema_key)
    return df2

# recargar dataframes para que tengan columnas nuevas
clientes = load_df("clientes")
abogados = load_df("abogados")
casos = load_df("casos")
instancias = ensure_ids(load_df("instancias"))
honorarios_tipo = ensure_ids(load_df("honorarios_tipo"))
actuaciones = ensure_ids(load_df("actuaciones"))
consultas = ensure_ids(load_df("consultas"))
plantillas = ensure_ids(load_df("plantillas"))
contratos = ensure_ids(load_df("contratos"))

# ----------------------------------------------------------
# 1) Constantes auxiliares
# ----------------------------------------------------------
ETAPAS_HONORARIOS = ["Actuación Administrativa", "Primera Instancia", "Segunda Instancia", "Casación", "Otros"]
TIPOS_CUOTA = ["Honorarios", "CuotaLitis"]

# ----------------------------------------------------------
# 2) CRONOGRAMA: tabla de pagos por cuota (checkbox pagado)
# ----------------------------------------------------------
CUOTAS_PAGADAS_FILE = "cuotas_pagadas.csv"
if not os.path.exists(CUOTAS_PAGADAS_FILE):
    pd.DataFrame(columns=["CuotaID","Pagada","FechaPagoReal","Obs"]).to_csv(CUOTAS_PAGADAS_FILE, index=False)

def load_cuotas_pagadas():
    try:
        df = pd.read_csv(CUOTAS_PAGADAS_FILE)
    except Exception:
        df = pd.DataFrame(columns=["CuotaID","Pagada","FechaPagoReal","Obs"])
    for c in ["CuotaID","Pagada","FechaPagoReal","Obs"]:
        if c not in df.columns:
            df[c] = ""
    return df

def save_cuotas_pagadas(df):
    df.to_csv(CUOTAS_PAGADAS_FILE, index=False)

def is_cuota_pagada(cuota_id, dfp):
    hit = dfp[dfp["CuotaID"].astype(str) == str(cuota_id)]
    if hit.empty:
        return False
    v = str(hit.iloc[0].get("Pagada","")).lower().strip()
    return v in ["1","true","si","sí","x"]

# ----------------------------------------------------------
# 3) CASOS (CRUD) — con campos extendidos dentro del form
# ----------------------------------------------------------
if menu == "Casos":
    st.subheader("📁 Casos (MARCA 006)")

    accion = st.radio("Acción", ["Nuevo","Editar","Eliminar"], horizontal=True)

    clientes_list = clientes["Nombre"].tolist() if not clientes.empty else []
    abogados_list = abogados["Nombre"].tolist() if not abogados.empty else []

    if accion == "Nuevo":
        if not clientes_list:
            st.warning("Primero registra clientes.")
        elif not abogados_list:
            st.warning("Primero registra abogados.")
        else:
            with st.form("nuevo_caso_m6"):
                cliente = st.selectbox("Cliente", clientes_list)
                abogado = st.selectbox("Abogado", abogados_list)
                expediente = st.text_input("Expediente")
                anio = st.text_input("Año")
                materia = st.text_input("Materia")
                instancia = st.selectbox("Instancia (referencial)", ETAPAS_HONORARIOS)
                pret = st.text_input("Pretensión")

                st.markdown("### Datos judiciales (nuevo)")
                juzgado = st.text_input("Juzgado")
                distrito = st.text_input("Distrito Judicial")
                contraparte = st.text_input("Contraparte")
                contraparte_doc = st.text_input("DNI/RUC Contraparte")

                obs = st.text_area("Observaciones")
                estado = st.selectbox("EstadoCaso", ["Activo","En pausa","Cerrado","Archivado"])
                fi = st.date_input("Fecha inicio", value=date.today())

                submit = st.form_submit_button("Guardar", disabled=is_readonly())
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
                        "Juzgado": juzgado,
                        "DistritoJudicial": distrito,
                        "Contraparte": contraparte,
                        "ContraparteDoc": contraparte_doc,
                        "Observaciones": obs,
                        "EstadoCaso": estado,
                        "FechaInicio": str(fi)
                    }, "casos")
                    save_df("casos", casos)
                    audit_log("ADD","casos",new_id,expediente)
                    st.success("✅ Caso registrado")
                    st.rerun()

    elif accion == "Editar" and not casos.empty:
        exp_list = casos["Expediente"].tolist()
        exp = st.selectbox("Expediente", exp_list)
        fila = casos[casos["Expediente"] == exp].iloc[0]

        with st.form("edit_caso_m6"):
            cliente = st.selectbox("Cliente", clientes_list, index=clientes_list.index(fila.get("Cliente","")) if fila.get("Cliente","") in clientes_list else 0)
            abogado = st.selectbox("Abogado", abogados_list, index=abogados_list.index(fila.get("Abogado","")) if fila.get("Abogado","") in abogados_list else 0)
            anio = st.text_input("Año", value=str(fila.get("Año","")))
            materia = st.text_input("Materia", value=str(fila.get("Materia","")))
            instancia = st.selectbox("Instancia (referencial)", ETAPAS_HONORARIOS, index=ETAPAS_HONORARIOS.index(fila.get("Instancia","Otros")) if fila.get("Instancia","Otros") in ETAPAS_HONORARIOS else 0)
            pret = st.text_input("Pretensión", value=str(fila.get("Pretension","")))

            st.markdown("### Datos judiciales (nuevo)")
            juzgado = st.text_input("Juzgado", value=str(fila.get("Juzgado","")))
            distrito = st.text_input("Distrito Judicial", value=str(fila.get("DistritoJudicial","")))
            contraparte = st.text_input("Contraparte", value=str(fila.get("Contraparte","")))
            contraparte_doc = st.text_input("DNI/RUC Contraparte", value=str(fila.get("ContraparteDoc","")))

            obs = st.text_area("Observaciones", value=str(fila.get("Observaciones","")))
            estado = st.selectbox("EstadoCaso", ["Activo","En pausa","Cerrado","Archivado"], index=["Activo","En pausa","Cerrado","Archivado"].index(fila.get("EstadoCaso","Activo")) if fila.get("EstadoCaso","Activo") in ["Activo","En pausa","Cerrado","Archivado"] else 0)
            fi = st.text_input("FechaInicio (YYYY-MM-DD)", value=str(fila.get("FechaInicio","")))

            submit = st.form_submit_button("Guardar cambios", disabled=is_readonly())
            if submit:
                idx = casos.index[casos["Expediente"] == exp][0]
                casos.loc[idx, "Cliente"] = cliente
                casos.loc[idx, "Abogado"] = abogado
                casos.loc[idx, "Año"] = anio
                casos.loc[idx, "Materia"] = materia
                casos.loc[idx, "Instancia"] = instancia
                casos.loc[idx, "Pretension"] = pret
                casos.loc[idx, "Juzgado"] = juzgado
                casos.loc[idx, "DistritoJudicial"] = distrito
                casos.loc[idx, "Contraparte"] = contraparte
                casos.loc[idx, "ContraparteDoc"] = contraparte_doc
                casos.loc[idx, "Observaciones"] = obs
                casos.loc[idx, "EstadoCaso"] = estado
                casos.loc[idx, "FechaInicio"] = fi
                save_df("casos", casos)
                audit_log("UPDATE","casos",exp,"edición")
                st.success("✅ Caso actualizado")
                st.rerun()

    elif accion == "Eliminar" and not casos.empty:
        exp = st.selectbox("Expediente a eliminar", casos["Expediente"].tolist())
        if st.button("Eliminar caso", disabled=is_readonly()):
            casos = casos[casos["Expediente"] != exp].copy()
            save_df("casos", casos)
            audit_log("DELETE","casos",exp,"")
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(casos, use_container_width=True)
    st.download_button("⬇️ Descargar casos (CSV)", casos.to_csv(index=False).encode("utf-8"), "casos.csv")

# ----------------------------------------------------------
# 4) CASOS (Extendido) – por si quieres editar solo judiciales rápido
# ----------------------------------------------------------
if menu == "Casos (Extendido)":
    st.subheader("📁 Casos (Extendido) – Datos judiciales")
    if casos.empty:
        st.info("No hay casos.")
    else:
        exp = st.selectbox("Expediente", casos["Expediente"].tolist())
        fila = casos[casos["Expediente"] == exp].iloc[0]
        juzgado = st.text_input("Juzgado", value=str(fila.get("Juzgado","")))
        distrito = st.text_input("Distrito Judicial", value=str(fila.get("DistritoJudicial","")))
        contraparte = st.text_input("Contraparte", value=str(fila.get("Contraparte","")))
        doc = st.text_input("DNI/RUC Contraparte", value=str(fila.get("ContraparteDoc","")))
        if st.button("💾 Guardar", disabled=is_readonly()):
            idx = casos.index[casos["Expediente"] == exp][0]
            casos.loc[idx, ["Juzgado","DistritoJudicial","Contraparte","ContraparteDoc"]] = [juzgado,distrito,contraparte,doc]
            save_df("casos", casos)
            audit_log("UPDATE","casos",exp,"datos judiciales")
            st.success("✅ Guardado")
            st.rerun()

# ----------------------------------------------------------
# 5) INSTANCIAS – registrar estado/resultado/acción/honorarios
# ----------------------------------------------------------
if menu == "Instancias":
    st.subheader("📑 Instancias del Caso")
    if casos.empty:
        st.info("No hay casos.")
    else:
        exp = st.selectbox("Expediente", casos["Expediente"].tolist())
        df_i = load_df("instancias")
        sub = df_i[df_i["Caso"].astype(str) == str(exp)].copy()

        st.markdown("### Instancias registradas")
        st.dataframe(sub.sort_values("ID", ascending=False), use_container_width=True)

        st.divider()
        st.markdown("### Registrar nueva instancia")
        tipo = st.selectbox("Tipo", ETAPAS_HONORARIOS)
        estado = st.text_input("Estado actual")
        resultado = st.text_input("Resultado")
        accion = st.text_input("Acción")
        honor = st.number_input("Honorarios (S/)", min_value=0.0, step=100.0)

        if st.button("💾 Guardar instancia", disabled=is_readonly()):
            new_id = next_id(df_i)
            df_i = add_row(df_i, {
                "ID": new_id,
                "Caso": normalize_key(exp),
                "TipoInstancia": tipo,
                "EstadoActual": estado,
                "Resultado": resultado,
                "Accion": accion,
                "Honorarios": float(honor),
                "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, "instancias")
            save_df("instancias", df_i)
            audit_log("ADD","instancias",new_id,f"{exp}|{tipo}")
            st.success("✅ Instancia guardada")
            st.rerun()

# ----------------------------------------------------------
# 6) HONORARIOS – agregar por tipo (además del total/etapas existentes)
# ----------------------------------------------------------
if menu == "Honorarios":
    st.subheader("🧾 Honorarios (MARCA 006)")

    st.markdown("### Honorarios por tipo (nuevo)")
    df_ht = load_df("honorarios_tipo")
    st.dataframe(df_ht.sort_values("ID", ascending=False), use_container_width=True)

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    if exp_list:
        exp = st.selectbox("Expediente", exp_list, key="ht_exp")
        tipo = st.selectbox("Tipo", ETAPAS_HONORARIOS, key="ht_tipo")
        monto = st.number_input("Monto (S/)", min_value=0.0, step=100.0, key="ht_monto")
        notas = st.text_input("Notas", value="", key="ht_notas")

        if st.button("Guardar honorario por tipo", key="ht_save", disabled=is_readonly()):
            new_id = next_id(df_ht)
            df_ht = add_row(df_ht, {
                "ID": new_id,
                "Caso": normalize_key(exp),
                "Tipo": tipo,
                "Monto": float(monto),
                "Notas": notas,
                "FechaRegistro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, "honorarios_tipo")
            save_df("honorarios_tipo", df_ht)
            audit_log("ADD","honorarios_tipo",new_id,f"{exp}|{tipo}|{monto}")
            st.success("✅ Guardado")
            st.rerun()

# ----------------------------------------------------------
# 7) CRONOGRAMA DE CUOTAS – marcar pagada con ícono
# ----------------------------------------------------------
if menu == "Cronograma de Cuotas":
    st.subheader("📅 Cronograma de Cuotas (MARCA 006)")

    dfp = load_cuotas_pagadas()

    st.markdown("### Cuotas registradas")
    if cuotas.empty:
        st.info("No hay cuotas registradas.")
    else:
        view = cuotas.copy()
        view["Pagada"] = view["ID"].apply(lambda x: "✅" if is_cuota_pagada(x, dfp) else "⏳")
        st.dataframe(view.sort_values("FechaVenc", ascending=False), use_container_width=True)

        st.markdown("### Marcar cuota como pagada")
        sel_id = st.selectbox("Cuota ID", cuotas["ID"].tolist(), key="cp_sel")
        pagada = st.checkbox("Pagada ✅", value=is_cuota_pagada(sel_id, dfp))
        fecha_real = st.text_input("Fecha pago real (YYYY-MM-DD)", value="")
        obs = st.text_input("Observación", value="")

        if st.button("Guardar estado de pago", disabled=is_readonly()):
            # upsert
            idxs = dfp.index[dfp["CuotaID"].astype(str) == str(sel_id)].tolist()
            if idxs:
                i = idxs[0]
                dfp.at[i, "Pagada"] = "1" if pagada else "0"
                dfp.at[i, "FechaPagoReal"] = fecha_real
                dfp.at[i, "Obs"] = obs
            else:
                dfp.loc[len(dfp)] = [str(sel_id), "1" if pagada else "0", fecha_real, obs]
            save_cuotas_pagadas(dfp)
            audit_log("UPDATE","cuotas",sel_id,"marcado pagada")
            st.success("✅ Estado guardado")
            st.rerun()

    st.divider()
    st.markdown("### Crear cuota futura")
    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    if not exp_list:
        st.warning("Primero registra casos para crear cuotas.")
    else:
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

        if st.button("Guardar cuota", key="cr_save", disabled=is_readonly()):
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
            audit_log("ADD","cuotas",new_id,f"{caso}|{tipo}|{monto}")
            st.success("✅ Cuota creada")
            st.rerun()

# ----------------------------------------------------------
# 8) ACTUACIONES – agregar costas/aranceles y gastos
# ----------------------------------------------------------
if menu == "Actuaciones":
    st.subheader("🧾 Actuaciones (MARCA 006)")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        exp_list = casos["Expediente"].tolist()
        exp = st.selectbox("Expediente", exp_list)

        fila_caso = casos[casos["Expediente"] == exp].iloc[0]
        cliente = str(fila_caso.get("Cliente",""))

        with st.form("act_new_m6"):
            fecha = st.date_input("Fecha", value=date.today())
            tipo = st.text_input("Tipo de actuación")
            resumen = st.text_area("Resumen", height=150)
            prox = st.text_input("Próxima acción")
            prox_fecha = st.text_input("Fecha próxima acción (YYYY-MM-DD)")
            costas = st.number_input("Costas/Aranceles (S/)", min_value=0.0, step=10.0)
            gastos = st.number_input("Gastos (copias, movilidad, etc.) (S/)", min_value=0.0, step=10.0)
            link = st.text_input("Link OneDrive (opcional)")
            notas = st.text_area("Notas", height=120)

            submit = st.form_submit_button("Guardar actuación", disabled=is_readonly())
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
                    "CostasAranceles": float(costas),
                    "Gastos": float(gastos),
                    "LinkOneDrive": link,
                    "Notas": notas
                }, "actuaciones")
                save_df("actuaciones", actuaciones)
                audit_log("ADD","actuaciones",new_id,f"{exp}|{tipo}")
                st.success("✅ Actuación registrada")
                st.rerun()

        st.divider()
        st.markdown("### Historial")
        hist = actuaciones[actuaciones["Caso"] == normalize_key(exp)].copy()
        if hist.empty:
            st.info("No hay actuaciones para este caso.")
        else:
            hist.sort_values("Fecha", ascending=False, inplace=True)
            st.dataframe(hist, use_container_width=True)

# ----------------------------------------------------------
# 9) CONSULTAS – abogado a cargo + costo + reporte ingresos
# ----------------------------------------------------------
if menu == "Consultas":
    st.subheader("🗂️ Consultas (MARCA 006)")

    tab_new, tab_hist, tab_rep = st.tabs(["Nueva", "Historial", "Ingresos"])

    exp_list = casos["Expediente"].tolist() if not casos.empty else []
    clientes_list = clientes["Nombre"].tolist() if not clientes.empty else []
    abogados_list = abogados["Nombre"].tolist() if not abogados.empty else []

    with tab_new:
        with st.form("cons_new_m6"):
            fecha = st.date_input("Fecha", value=date.today())
            cliente = st.selectbox("Cliente", clientes_list) if clientes_list else st.text_input("Cliente")
            caso = st.selectbox("Expediente (opcional)", [""] + exp_list) if exp_list else st.text_input("Expediente (opcional)")
            abogado = st.selectbox("Abogado a cargo", abogados_list) if abogados_list else st.text_input("Abogado a cargo")

            consulta_txt = st.text_area("Consulta", height=140)
            estrategia_txt = st.text_area("Estrategia", height=140)
            costo = st.number_input("Costo de consulta (S/)", min_value=0.0, step=10.0)
            honor_prop = st.number_input("Honorarios propuestos (S/)", min_value=0.0, step=50.0)
            link = st.text_input("Link OneDrive (opcional)")
            notas = st.text_area("Notas", height=100)

            proforma = (
                f"PROFORMA – {APP_NAME}\n"
                f"Fecha: {fecha}\n"
                f"Cliente: {cliente}\n"
                f"Abogado: {abogado}\n"
                f"Expediente: {caso}\n"
                f"{'-'*60}\n"
                f"CONSULTA:\n{consulta_txt}\n\n"
                f"ESTRATEGIA:\n{estrategia_txt}\n\n"
                f"COSTO CONSULTA: S/ {costo:,.2f}\n"
                f"HONORARIOS PROPUESTOS: S/ {honor_prop:,.2f}\n"
                f"{'-'*60}\n"
                f"Notas: {notas}\n"
            )

            submit = st.form_submit_button("Guardar", disabled=is_readonly())
            if submit:
                new_id = next_id(consultas)
                consultas = add_row(consultas, {
                    "ID": new_id,
                    "Fecha": str(fecha),
                    "Cliente": cliente,
                    "Caso": normalize_key(caso),
                    "Abogado": abogado,
                    "Consulta": consulta_txt,
                    "Estrategia": estrategia_txt,
                    "CostoConsulta": float(costo),
                    "HonorariosPropuestos": float(honor_prop),
                    "Proforma": proforma,
                    "LinkOneDrive": link,
                    "Notas": notas
                }, "consultas")
                save_df("consultas", consultas)
                audit_log("ADD","consultas",new_id,f"{cliente}|{abogado}|{costo}")
                st.success("✅ Consulta guardada")
                st.download_button("⬇️ Descargar proforma (TXT)", proforma.encode("utf-8"), f"proforma_{date.today()}.txt")
                st.rerun()

    with tab_hist:
        if consultas.empty:
            st.info("No hay consultas.")
        else:
            st.dataframe(consultas.sort_values("Fecha", ascending=False), use_container_width=True)

    with tab_rep:
        if consultas.empty:
            st.info("No hay ingresos aún.")
        else:
            dfc = consultas.copy()
            dfc["CostoConsulta"] = safe_float_series(dfc["CostoConsulta"])
            rep = dfc.groupby("Abogado", as_index=False)["CostoConsulta"].sum().rename(columns={"CostoConsulta":"IngresosConsultas"})
            st.dataframe(rep, use_container_width=True)
            st.download_button("⬇️ Descargar ingresos (CSV)", rep.to_csv(index=False).encode("utf-8"), "ingresos_consultas.csv")

# ----------------------------------------------------------
# 10) PLANTILLAS + CONTRATOS – placeholders extendidos
# ----------------------------------------------------------
def build_context_all(expediente: str) -> dict:
    expediente = normalize_key(expediente)
    ctx = {}

    caso_row = casos[casos["Expediente"] == expediente]
    if caso_row.empty:
        return ctx
    c = caso_row.iloc[0]

    # Caso: todos los campos
    for col in SCHEMAS["casos"]:
        ctx[f"{{{{CASO_{col.upper()}}}}}"] = str(c.get(col, ""))

    # Cliente (por nombre)
    cli_row = clientes[clientes["Nombre"] == c.get("Cliente","")]
    if not cli_row.empty:
        cli = cli_row.iloc[0]
        for col in SCHEMAS["clientes"]:
            ctx[f"{{{{CLIENTE_{col.upper()}}}}}"] = str(cli.get(col, ""))

    # Abogado (por nombre)
    ab_row = abogados[abogados["Nombre"] == c.get("Abogado","")]
    if not ab_row.empty:
        ab = ab_row.iloc[0]
        for col in SCHEMAS["abogados"]:
            ctx[f"{{{{ABOGADO_{col.upper()}}}}}"] = str(ab.get(col, ""))

    # Económicos
    canon_h = canon_last_by_case(honorarios, "Caso")
    canon_cl = canon_last_by_case(cuota_litis, "Caso")

    monto_pactado = safe_float_series(canon_h[canon_h["Caso"] == expediente]["Monto Pactado"]).sum()
    porc = safe_float_series(canon_cl[canon_cl["Caso"] == expediente]["Porcentaje"])
    porc_val = float(porc.iloc[-1]) if len(porc) else 0.0

    ctx["{{MONTO_PACTADO}}"] = f"{monto_pactado:.2f}"
    ctx["{{PORCENTAJE_LITIS}}"] = f"{porc_val:.2f}"
    ctx["{{FECHA_HOY}}"] = date.today().strftime("%Y-%m-%d")
    ctx["{{EXPEDIENTE}}"] = expediente

    return ctx

def render_template(text: str, ctx: dict) -> str:
    out = str(text)
    for k, v in ctx.items():
        out = out.replace(k, v)
    return out

if menu == "Plantillas de Contrato":
    st.subheader("📝 Plantillas de Contrato (MARCA 006)")

    st.info(
        "Placeholders disponibles:\n"
        "- Básicos: {{EXPEDIENTE}}, {{MONTO_PACTADO}}, {{PORCENTAJE_LITIS}}, {{FECHA_HOY}}\n"
        "- Caso: {{CASO_<COLUMNA>}}  (ej: {{CASO_MATERIA}}, {{CASO_JUZGADO}})\n"
        "- Cliente: {{CLIENTE_<COLUMNA>}} (ej: {{CLIENTE_NOMBRE}}, {{CLIENTE_RUC}}, {{CLIENTE_RAZONSOCIAL}})\n"
        "- Abogado: {{ABOGADO_<COLUMNA>}} (ej: {{ABOGADO_NOMBRE}}, {{ABOGADO_COLEGIOPROFESIONAL}})\n"
        "Las columnas corresponden a los campos del sistema."
    )

    accion = st.radio("Acción", ["Nueva","Editar","Eliminar"], horizontal=True)
    if accion == "Nueva":
        with st.form("tpl_new_m6"):
            nombre = st.text_input("Nombre")
            contenido = st.text_area("Contenido", height=320)
            notas = st.text_input("Notas", value="")
            submit = st.form_submit_button("Guardar plantilla", disabled=is_readonly())
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
                audit_log("ADD","plantillas",new_id,nombre)
                st.success("✅ Plantilla creada")
                st.rerun()

    elif accion == "Editar" and not plantillas.empty:
        sel = st.selectbox("Plantilla ID", plantillas["ID"].tolist())
        fila = plantillas[plantillas["ID"] == sel].iloc[0]
        with st.form("tpl_edit_m6"):
            nombre = st.text_input("Nombre", value=str(fila.get("Nombre","")))
            contenido = st.text_area("Contenido", value=str(fila.get("Contenido","")), height=320)
            notas = st.text_input("Notas", value=str(fila.get("Notas","")))
            submit = st.form_submit_button("Guardar cambios", disabled=is_readonly())
            if submit:
                idx = plantillas.index[plantillas["ID"] == sel][0]
                plantillas.loc[idx, ["Nombre","Contenido","Notas"]] = [nombre, contenido, notas]
                save_df("plantillas", plantillas)
                audit_log("UPDATE","plantillas",sel,nombre)
                st.success("✅ Actualizado")
                st.rerun()

    elif accion == "Eliminar" and not plantillas.empty:
        sel = st.selectbox("Plantilla ID a eliminar", plantillas["ID"].tolist())
        if st.button("Eliminar plantilla", disabled=is_readonly()):
            plantillas = plantillas[plantillas["ID"] != sel].copy()
            save_df("plantillas", plantillas)
            audit_log("DELETE","plantillas",sel,"")
            st.success("✅ Eliminado")
            st.rerun()

    st.dataframe(plantillas, use_container_width=True)
    st.download_button("⬇️ Descargar plantillas (CSV)", plantillas.to_csv(index=False).encode("utf-8"), "plantillas_contratos.csv")

# ----------------------------------------------------------
# 11) GENERAR CONTRATO – Word si es posible + repositorio + numeración solo firmados
# ----------------------------------------------------------
def _next_contrato_numero(anio: str, sigla: str) -> int:
    try:
        df = load_df("contratos")
        df = df[df["Año"].astype(str) == str(anio)]
        df = df[df["Sigla"].astype(str) == str(sigla)]
        df = df[df["Estado"].astype(str) == "Firmado"]
        if df.empty:
            return 1
        nums = pd.to_numeric(df["Numero"], errors="coerce").dropna()
        return int(nums.max()) + 1 if not nums.empty else 1
    except Exception:
        return 1

if menu == "Generar Contrato":
    st.subheader("📄 Generar Contrato (MARCA 006)")

    if casos.empty:
        st.info("Primero registra casos.")
    elif plantillas.empty:
        st.info("Primero crea una plantilla.")
    else:
        exp = st.selectbox("Expediente", casos["Expediente"].tolist())
        tpl_id = st.selectbox("Plantilla ID", plantillas["ID"].tolist())
        tpl = plantillas[plantillas["ID"] == tpl_id].iloc[0]

        # datos de contrato
        nombre_contrato = st.text_input("Nombre del contrato (ej: Prestación de servicios)")
        sigla = st.text_input("Sigla", value="CLS")
        anio = st.text_input("Año", value=str(date.today().year))
        estado = st.selectbox("Estado", ["Borrador","Firmado"])

        ctx = build_context_all(exp)
        generado = render_template(str(tpl.get("Contenido","")), ctx)

        st.text_area("Vista previa", value=generado, height=320)

        # numeración solo si firmada
        numero = _next_contrato_numero(anio, sigla) if estado == "Firmado" else None
        if estado == "Firmado":
            st.info(f"Numeración asignada: {numero}-{anio}-{sigla}")

        # generar archivo base
        if st.button("💾 Guardar contrato en repositorio", disabled=is_readonly()):
            dfc = load_df("contratos")
            new_id = next_id(dfc)
            caso_row = casos[casos["Expediente"] == exp].iloc[0]
            cliente = str(caso_row.get("Cliente",""))
            abogado = str(caso_row.get("Abogado",""))

            archivo = ""
            if estado == "Firmado":
                archivo = f"{nombre_contrato} N° {numero}-{anio}-{sigla}.txt"
            else:
                archivo = f"{nombre_contrato} BORRADOR {anio}-{sigla}.txt"

            # guardar archivo txt
            out_path = os.path.join(GENERADOS_DIR, archivo)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(generado)

            dfc = add_row(dfc, {
                "ID": new_id,
                "Numero": "" if numero is None else str(numero),
                "Año": str(anio),
                "Sigla": str(sigla),
                "NombreContrato": nombre_contrato,
                "Caso": exp,
                "Cliente": cliente,
                "Abogado": abogado,
                "Estado": estado,
                "Archivo": archivo,
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, "contratos")
            save_df("contratos", dfc)
            audit_log("ADD","contratos",new_id,archivo)
            st.success(f"✅ Contrato guardado: {archivo}")
            st.download_button("⬇️ Descargar contrato (TXT)", generado.encode("utf-8"), archivo)

if menu == "Contratos":
    st.subheader("📚 Repositorio de Contratos")
    dfc = load_df("contratos")
    if dfc.empty:
        st.info("No hay contratos guardados.")
    else:
        st.dataframe(dfc.sort_values("ID", ascending=False), use_container_width=True)
        st.download_button("⬇️ Descargar contratos (CSV)", dfc.to_csv(index=False).encode("utf-8"), "contratos.csv")
# ==========================================================
# BLOQUE 5 – USUARIOS + ROLES + AUDITORÍA + REPORTES + BÚSQUEDA (FINAL)
# ==========================================================

# ----------------------------------------------------------
# 0) FIX DEFINITIVO (sobrescribe cualquier bug previo de helpers)
# ----------------------------------------------------------
def _ensure_schema_cols(df: pd.DataFrame, key: str) -> pd.DataFrame:
    cols = SCHEMAS[key]
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    return df.reindex(columns=cols)

def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    try:
        df = pd.read_csv(FILES[key])
    except Exception:
        df = pd.DataFrame(columns=SCHEMAS[key])
    df = drop_unnamed(df)
    df = _ensure_schema_cols(df, key)
    return df

def save_df(key: str, df: pd.DataFrame):
    backup_file(FILES[key])
    df = drop_unnamed(df)
    df = _ensure_schema_cols(df, key)
    df.to_csv(FILES[key], index=False)

def add_row(df: pd.DataFrame, row_dict: dict, schema_key: str) -> pd.DataFrame:
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df2 = _ensure_schema_cols(df2, schema_key)
    return df2

# recargar dataframes base para evitar inconsistencias
try:
    clientes = load_df("clientes")
    abogados = load_df("abogados")
    casos = load_df("casos")
    usuarios = load_df("usuarios")
    auditoria_mod = load_df("auditoria_mod")
    consultas = load_df("consultas")
except Exception:
    pass

# ----------------------------------------------------------
# 1) Permisos por rol
# ----------------------------------------------------------
def is_readonly():
    return st.session_state.get("rol") == "asistente"

def is_admin():
    return st.session_state.get("rol") == "admin"

def is_abogado():
    return st.session_state.get("rol") == "abogado"

def can_edit():
    return st.session_state.get("rol") in ["admin", "abogado"]

# ----------------------------------------------------------
# 2) Búsqueda global mejorada (punto 19)
# ----------------------------------------------------------
try:
    with st.sidebar.expander("🔎 Búsqueda avanzada", expanded=False):
        q = st.text_input("Buscar (expediente/cliente/DNI/RUC/abogado/materia)")
        if q:
            ql = q.lower().strip()
            results = []

            # casos
            if 'casos' in globals() and not casos.empty:
                for _, r in casos.iterrows():
                    if any(ql in str(r.get(k, "")).lower() for k in ["Expediente", "Cliente", "Abogado", "Materia", "Juzgado", "Contraparte"]):
                        results.append({
                            "Tipo": "Caso",
                            "Clave": r.get("Expediente",""),
                            "Detalle": f"{r.get('Cliente','')} | {r.get('Abogado','')} | {r.get('Materia','')}"
                        })

            # clientes
            if 'clientes' in globals() and not clientes.empty:
                for _, r in clientes.iterrows():
                    if any(ql in str(r.get(k, "")).lower() for k in ["Nombre","DNI","RUC","RazonSocial","RepresentanteLegal"]):
                        results.append({
                            "Tipo": "Cliente",
                            "Clave": r.get("Nombre",""),
                            "Detalle": f"DNI:{r.get('DNI','')} RUC:{r.get('RUC','')}"
                        })

            # abogados
            if 'abogados' in globals() and not abogados.empty:
                for _, r in abogados.iterrows():
                    if any(ql in str(r.get(k, "")).lower() for k in ["Nombre","DNI","Colegiatura","ColegioProfesional","DistritoJudicial"]):
                        results.append({
                            "Tipo": "Abogado",
                            "Clave": r.get("Nombre",""),
                            "Detalle": f"Colegiatura:{r.get('Colegiatura','')}"
                        })

            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("Sin resultados.")
except Exception:
    pass

# ----------------------------------------------------------
# 3) Usuarios (punto 14,18) – Admin gestiona; asistente solo lectura
# ----------------------------------------------------------
if menu == "Usuarios":
    require_admin()
    st.subheader("👥 Usuarios (MARCA 006)")

    users = load_df("usuarios")
    st.dataframe(users[["Usuario","Rol","AbogadoID","Activo","Creado"]], use_container_width=True)

    # Mapear abogados para vincular
    abogado_map = {str(r["ID"]): str(r["Nombre"]) for _, r in abogados.iterrows()} if not abogados.empty else {}

    accion = st.radio("Acción", ["Nuevo","Cambiar contraseña","Activar/Desactivar","Eliminar"], horizontal=True)

    if accion == "Nuevo":
        if abogados.empty:
            st.warning("Primero registra abogados para vincular usuarios.")
        else:
            with st.form("new_user_form_m6"):
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
                        audit_log("ADD","usuarios",u,f"rol={rol}")
                        st.success("✅ Usuario creado")
                        st.rerun()

    if accion == "Cambiar contraseña":
        sel_u = st.selectbox("Usuario", users["Usuario"].tolist())
        new_p = st.text_input("Nueva contraseña", type="password")
        if st.button("Guardar contraseña"):
            idx = users.index[users["Usuario"].astype(str) == str(sel_u)][0]
            users.loc[idx, "PasswordHash"] = sha256(new_p)
            save_df("usuarios", users)
            audit_log("UPDATE","usuarios",sel_u,"password change")
            st.success("✅ Contraseña actualizada")

    if accion == "Activar/Desactivar":
        sel_u = st.selectbox("Usuario", users["Usuario"].tolist(), key="act_user")
        fila = users[users["Usuario"].astype(str) == str(sel_u)].iloc[0]
        activo = str(fila.get("Activo","1")).strip() == "1"
        nuevo = st.checkbox("Activo", value=activo)
        if st.button("Guardar estado"):
            idx = users.index[users["Usuario"].astype(str) == str(sel_u)][0]
            users.loc[idx, "Activo"] = "1" if nuevo else "0"
            save_df("usuarios", users)
            audit_log("UPDATE","usuarios",sel_u,f"activo={nuevo}")
            st.success("✅ Estado actualizado")

    if accion == "Eliminar":
        sel_u = st.selectbox("Usuario a eliminar", users["Usuario"].tolist(), key="del_user")
        if st.button("Eliminar usuario"):
            if sel_u == "admin":
                st.error("No se puede eliminar admin.")
            else:
                users = users[users["Usuario"].astype(str) != str(sel_u)].copy()
                save_df("usuarios", users)
                audit_log("DELETE","usuarios",sel_u,"")
                st.success("✅ Usuario eliminado")
                st.rerun()

    st.download_button("⬇️ Descargar usuarios (CSV)", users.to_csv(index=False).encode("utf-8"), "usuarios.csv")

# ----------------------------------------------------------
# 4) Auditoría (punto 14,18) – vista filtrable
# ----------------------------------------------------------
if menu == "Auditoría":
    require_admin()
    st.subheader("🧾 Auditoría de modificaciones (MARCA 006)")

    df = load_df("auditoria_mod")
    if df.empty:
        st.info("Aún no hay auditoría registrada.")
    else:
        col1, col2, col3 = st.columns(3)
        f_user = col1.selectbox("Usuario", ["(todos)"] + sorted(df["Usuario"].astype(str).unique().tolist()))
        f_acc = col2.selectbox("Acción", ["(todas)"] + sorted(df["Accion"].astype(str).unique().tolist()))
        f_ent = col3.selectbox("Entidad", ["(todas)"] + sorted(df["Entidad"].astype(str).unique().tolist()))

        tmp = df.copy()
        if f_user != "(todos)":
            tmp = tmp[tmp["Usuario"].astype(str) == f_user]
        if f_acc != "(todas)":
            tmp = tmp[tmp["Accion"].astype(str) == f_acc]
        if f_ent != "(todas)":
            tmp = tmp[tmp["Entidad"].astype(str) == f_ent]

        tmp = tmp.sort_values("ID", ascending=False)
        st.dataframe(tmp, use_container_width=True)
        st.download_button("⬇️ Descargar auditoría (CSV)", tmp.to_csv(index=False).encode("utf-8"), "auditoria_mod.csv")

# ----------------------------------------------------------
# 5) Reportes extra (ingresos consultas + por abogado)
# ----------------------------------------------------------
if menu == "Reportes":
    st.subheader("📈 Reportes (MARCA 006)")

    tab1, tab2, tab3 = st.tabs(["Ingresos por consulta", "Reporte por abogado", "Auditoría rápida"])
    with tab1:
        dfc = load_df("consultas")
        if dfc.empty:
            st.info("No hay consultas registradas.")
        else:
            dfc["CostoConsulta"] = safe_float_series(dfc["CostoConsulta"])
            rep = dfc.groupby("Abogado", as_index=False)["CostoConsulta"].sum().rename(columns={"CostoConsulta":"IngresosConsultas"})
            rep = rep.sort_values("IngresosConsultas", ascending=False)
            st.dataframe(rep, use_container_width=True)
            st.download_button("⬇️ Descargar ingresos (CSV)", rep.to_csv(index=False).encode("utf-8"), "ingresos_consultas.csv")

    with tab2:
        # Mezclar casos con resumen financiero
        try:
            df_res = resumen_financiero_df()
            if df_res.empty:
                st.info("Sin datos financieros.")
            else:
                dfm = df_res.merge(casos[["Expediente","Abogado"]], on="Expediente", how="left")
                rep_ab = dfm.groupby("Abogado", as_index=False).agg({
                    "Honorario Pactado":"sum",
                    "Honorario Pagado":"sum",
                    "Honorario Pendiente":"sum",
                    "Saldo Litis":"sum"
                })
                rep_ab["SaldoTotal"] = rep_ab["Honorario Pendiente"] + rep_ab["Saldo Litis"]
                rep_ab.sort_values("SaldoTotal", ascending=False, inplace=True)
                st.dataframe(rep_ab, use_container_width=True)
                st.download_button("⬇️ Descargar reporte abogado (CSV)", rep_ab.to_csv(index=False).encode("utf-8"), "reporte_por_abogado.csv")
        except Exception:
            st.warning("No se pudo generar reporte por abogado (falta resumen financiero).")

    with tab3:
        df = load_df("auditoria_mod")
        if df.empty:
            st.info("Sin auditoría aún.")
        else:
            st.dataframe(df.sort_values("ID", ascending=False).head(200), use_container_width=True)

# ----------------------------------------------------------
# 6) Nota final UX: aviso de modo lectura
# ----------------------------------------------------------
try:
    if is_readonly():
        st.sidebar.warning("🔒 Modo lectura: tu rol (asistente) no puede modificar datos.")
except Exception:
    pass
