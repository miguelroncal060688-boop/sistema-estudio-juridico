import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="⚖️ Estudio Jurídico Roncal Liñán y Asociados", layout="wide")

# =========================
# ARCHIVOS
# =========================
FILES = {
    "clientes": "clientes.csv",
    "abogados": "abogados.csv",
    "casos": "casos.csv",
    "honorarios": "honorarios.csv",
    "pagos_honorarios": "pagos_honorarios.csv",
    "cuota_litis": "cuota_litis.csv",
    "pagos_litis": "pagos_litis.csv",
    "cuotas": "cuotas.csv",  # Cronograma de cuotas
}

# =========================
# ESQUEMAS (COLUMNAS EXACTAS)
# =========================
SCHEMAS = {
    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones"],
    "honorarios": ["Caso","Monto Pactado"],

    # Pagos con fecha + observación
    "pagos_honorarios": ["ID","Caso","FechaPago","Monto","Observacion"],
    "cuota_litis": ["Caso","Monto Base","Porcentaje"],
    "pagos_litis": ["ID","Caso","FechaPago","Monto","Observacion"],

    # Cronograma: cuotas con vencimiento
    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"]
}

# =========================
# UTILIDADES CSV (robustas)
# =========================
def drop_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina columnas tipo Unnamed: 0 si existieran."""
    return df.loc[:, ~df.columns.str.contains(r"^Unnamed", case=False, na=False)]

def ensure_csv(key: str):
    """Crea el CSV si no existe y lo migra si le faltan columnas."""
    path = FILES[key]
    cols = SCHEMAS[key]

    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    df = pd.read_csv(path)
    df = drop_unnamed(df)

    # Agregar columnas faltantes
    missing = [c for c in cols if c not in df.columns]
    for c in missing:
        df[c] = ""

    # Quitar columnas sobrantes y ordenar según esquema
    df = df.reindex(columns=cols)
    df.to_csv(path, index=False)

def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    df = pd.read_csv(FILES[key])
    df = drop_unnamed(df)
    # Forzar columnas y orden correctos
    df = df.reindex(columns=SCHEMAS[key])
    return df

def save_df(key: str, df: pd.DataFrame):
    df = drop_unnamed(df)
    df = df.reindex(columns=SCHEMAS[key])
    df.to_csv(FILES[key], index=False)

def next_id(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    try:
        s = pd.to_numeric(df["ID"], errors="coerce")
        m = s.max()
        return int(m) + 1 if pd.notna(m) else len(df) + 1
    except Exception:
        return len(df) + 1

def add_row(df: pd.DataFrame, row_dict: dict, key: str) -> pd.DataFrame:
    """
    Añade una fila por diccionario (evita mismatched columns).
    """
    df2 = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df2 = df2.reindex(columns=SCHEMAS[key])
    return df2

def to_date_safe(x):
    if pd.isna(x) or str(x).strip() == "":
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

# Inicializar todos los CSV
for k in FILES:
    ensure_csv(k)

# =========================
# LOGIN (simple)
# =========================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {
        "admin": {"password": "estudio123", "rol": "admin"}
    }

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("⚖️ Estudio Jurídico Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")

    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in st.session_state.usuarios and st.session_state.usuarios[user]["password"] == pw:
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

st.sidebar.write(f"Usuario: {st.session_state.usuario}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

# =========================
# CARGAR DATA
# =========================
clientes = load_df("clientes")
abogados = load_df("abogados")
casos = load_df("casos")
honorarios = load_df("honorarios")
pagos_honorarios = load_df("pagos_honorarios")
cuota_litis = load_df("cuota_litis")
pagos_litis = load_df("pagos_litis")
cuotas = load_df("cuotas")

menu = st.sidebar.selectbox("Menú", [
    "Dashboard",
    "Clientes",
    "Abogados",
    "Casos",
    "Honorarios",
    "Pagos Honorarios",
    "Cuota Litis",
    "Pagos Cuota Litis",
    "Cronograma de Cuotas",
    "Resumen Financiero"
])

# =========================
# FINANZAS: RESUMEN
# =========================
def resumen_financiero_df():
    if casos.empty:
        return pd.DataFrame(columns=[
            "Expediente",
            "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
            "Monto Base","Porcentaje","Cuota Litis Calculada","Pagado Litis","Saldo Litis"
        ])

    resumen = []
    for _, c in casos.iterrows():
        expediente = c["Expediente"]

        pactado = pd.to_numeric(honorarios[honorarios["Caso"] == expediente]["Monto Pactado"], errors="coerce").fillna(0).sum()
        pagado_h = pd.to_numeric(pagos_honorarios[pagos_honorarios["Caso"] == expediente]["Monto"], errors="coerce").fillna(0).sum()

        base = pd.to_numeric(cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"], errors="coerce").fillna(0).sum()
        porc_series = pd.to_numeric(cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"], errors="coerce").fillna(0)
        porcentaje = float(porc_series.iloc[-1]) if len(porc_series) else 0.0

        calculada = float(base) * float(porcentaje) / 100.0
        pagado_l = pd.to_numeric(pagos_litis[pagos_litis["Caso"] == expediente]["Monto"], errors="coerce").fillna(0).sum()

        resumen.append([
            expediente,
            float(pactado),
            float(pagado_h),
            float(pactado) - float(pagado_h),
            float(base),
            float(porcentaje),
            float(calculada),
            float(pagado_l),
            float(calculada) - float(pagado_l)
        ])

    return pd.DataFrame(resumen, columns=[
        "Expediente",
        "Honorario Pactado","Honorario Pagado","Honorario Pendiente",
        "Monto Base","Porcentaje","Cuota Litis Calculada","Pagado Litis","Saldo Litis"
    ])

def allocate_payments_oldest_first(cuotas_tipo_df: pd.DataFrame, pagos_tipo_df: pd.DataFrame):
    """
    Aplica pagos a cuotas desde la más antigua (FechaVenc).
    """
    today = date.today()

    if cuotas_tipo_df.empty:
        return cuotas_tipo_df

    df = cuotas_tipo_df.copy()
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0)
    df["FechaVenc_dt"] = df["FechaVenc"].apply(to_date_safe)
    df["_sort_date"] = df["FechaVenc_dt"].apply(lambda d: d if d is not None else date(2100,1,1))

    df.sort_values(["Caso","_sort_date","NroCuota"], inplace=True)

    pagos_tipo_df = pagos_tipo_df.copy()
    pagos_tipo_df["Monto"] = pd.to_numeric(pagos_tipo_df["Monto"], errors="coerce").fillna(0.0)
    pagado_por_caso = pagos_tipo_df.groupby("Caso")["Monto"].sum().to_dict()
    remaining = {k: float(v) for k, v in pagado_por_caso.items()}

    pagado_asignado = []
    saldo_cuota = []
    estado = []
    dias = []

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

    out = pd.concat([st_h, st_l], ignore_index=True) if (not st_h.empty or not st_l.empty) else pd.DataFrame()
    return out

def cuotas_pendientes(df_status: pd.DataFrame):
    if df_status.empty:
        return df_status
    return df_status[pd.to_numeric(df_status["SaldoCuota"], errors="coerce").fillna(0) > 0].copy()

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard General")

    df_res = resumen_financiero_df()
    df_status = cuotas_status_all()
    df_pend = cuotas_pendientes(df_status)

    # Totales saldo total
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

    st.subheader("📅 Indicadores por Cronograma (Cuotas)")
    today = date.today()
    vencidas = pd.DataFrame()
    por_vencer = pd.DataFrame()

    if not df_pend.empty:
        vencidas = df_pend[df_pend["DiasParaVencimiento"].notna() & (df_pend["DiasParaVencimiento"] < 0)]
        por_vencer = df_pend[df_pend["DiasParaVencimiento"].notna() & (df_pend["DiasParaVencimiento"].between(0, 7))]

    total_vencidas = float(pd.to_numeric(vencidas["SaldoCuota"], errors="coerce").fillna(0).sum()) if not vencidas.empty else 0.0
    total_por_vencer = float(pd.to_numeric(por_vencer["SaldoCuota"], errors="coerce").fillna(0).sum()) if not por_vencer.empty else 0.0
    total_pend_cuotas = float(pd.to_numeric(df_pend["SaldoCuota"], errors="coerce").fillna(0).sum()) if not df_pend.empty else 0.0

    d1, d2, d3 = st.columns(3)
    d1.metric("🚨 Cuotas vencidas (S/)", f"{total_vencidas:,.2f}")
    d2.metric("⏱️ Por vencer (7 días) (S/)", f"{total_por_vencer:,.2f}")
    d3.metric("📌 Total cuotas pendientes (S/)", f"{total_pend_cuotas:,.2f}")

    st.divider()

    e1, e2, e3 = st.columns(3)
    e1.metric("👥 Total Clientes", len(clientes))
    e2.metric("📁 Total Casos", len(casos))
    e3.metric("👨‍⚖️ Total Abogados", len(abogados))

    st.subheader("🚨 Reporte: Cuotas Vencidas")
    if vencidas.empty:
        st.info("No hay cuotas vencidas con saldo pendiente.")
    else:
        st.dataframe(vencidas[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]], use_container_width=True)

    st.subheader("⏱️ Reporte: Cuotas por Vencer (7 días)")
    if por_vencer.empty:
        st.info("No hay cuotas por vencer en los próximos 7 días.")
    else:
        st.dataframe(por_vencer[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]], use_container_width=True)

# =========================
# CLIENTES (CRUD)  ✅ (CORREGIDO)
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
                nueva_fila = {
                    "ID": new_id,
                    "Nombre": nombre,
                    "DNI": dni,
                    "Celular": celular,
                    "Correo": correo,
                    "Direccion": direccion,
                    "Observaciones": obs
                }
                clientes = add_row(clientes, nueva_fila, "clientes")
                save_df("clientes", clientes)
                st.success("✅ Cliente registrado")
                st.rerun()

    elif accion == "Editar":
        if clientes.empty:
            st.info("No hay clientes para editar.")
        else:
            sel_id = st.selectbox("Selecciona Cliente (ID)", clientes["ID"].tolist())
            fila = clientes[clientes["ID"] == sel_id].iloc[0]

            with st.form("editar_cliente"):
                nombre = st.text_input("Nombre", value=str(fila["Nombre"]))
                dni = st.text_input("DNI", value=str(fila["DNI"]))
                celular = st.text_input("Celular", value=str(fila["Celular"]))
                correo = st.text_input("Correo", value=str(fila["Correo"]))
                direccion = st.text_input("Dirección", value=str(fila["Direccion"]))
                obs = st.text_area("Observaciones", value=str(fila["Observaciones"]))
                submit = st.form_submit_button("Guardar cambios")

                if submit:
                    idx = clientes.index[clientes["ID"] == sel_id][0]
                    clientes.loc[idx, :] = [sel_id, nombre, dni, celular, correo, direccion, obs]
                    clientes = clientes.reindex(columns=SCHEMAS["clientes"])
                    save_df("clientes", clientes)
                    st.success("✅ Cliente actualizado")
                    st.rerun()

    elif accion == "Eliminar":
        if clientes.empty:
            st.info("No hay clientes para eliminar.")
        else:
            sel_id = st.selectbox("Selecciona Cliente (ID) a eliminar", clientes["ID"].tolist())
            st.warning("⚠️ Esta acción elimina el cliente (no borra casos automáticamente).")
            if st.button("Eliminar Cliente"):
                clientes = clientes[clientes["ID"] != sel_id].copy()
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
                nueva_fila = {
                    "ID": new_id,
                    "Nombre": nombre,
                    "DNI": dni,
                    "Celular": celular,
                    "Correo": correo,
                    "Colegiatura": coleg,
                    "Domicilio Procesal": dom,
                    "Casilla Electronica": cas_e,
                    "Casilla Judicial": cas_j
                }
                abogados = add_row(abogados, nueva_fila, "abogados")
                save_df("abogados", abogados)
                st.success("✅ Abogado registrado")
                st.rerun()

    elif accion == "Editar":
        if abogados.empty:
            st.info("No hay abogados para editar.")
        else:
            sel_id = st.selectbox("Selecciona Abogado (ID)", abogados["ID"].tolist())
            fila = abogados[abogados["ID"] == sel_id].iloc[0]

            with st.form("editar_abogado"):
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
                    idx = abogados.index[abogados["ID"] == sel_id][0]
                    abogados.loc[idx, :] = [sel_id, nombre, dni, celular, correo, coleg, dom, cas_e, cas_j]
                    abogados = abogados.reindex(columns=SCHEMAS["abogados"])
                    save_df("abogados", abogados)
                    st.success("✅ Abogado actualizado")
                    st.rerun()

    elif accion == "Eliminar":
        if abogados.empty:
            st.info("No hay abogados para eliminar.")
        else:
            sel_id = st.selectbox("Selecciona Abogado (ID) a eliminar", abogados["ID"].tolist())
            st.warning("⚠️ Esta acción elimina el abogado (no borra casos automáticamente).")
            if st.button("Eliminar Abogado"):
                abogados = abogados[abogados["ID"] != sel_id].copy()
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
    abogados_list = abogados["Nombre"].tolist() if not abogados.empty else []

    if accion == "Nuevo":
        with st.form("nuevo_caso"):
            cliente = st.selectbox("Cliente", clientes_list)
            abogado = st.selectbox("Abogado", abogados_list)
            expediente = st.text_input("Número de Expediente")
            anio = st.text_input("Año")
            materia = st.text_input("Materia")
            pretension = st.text_input("Pretensión")
            obs = st.text_area("Observaciones")
            submit = st.form_submit_button("Guardar")

            if submit:
                new_id = next_id(casos)
                nueva_fila = {
                    "ID": new_id,
                    "Cliente": cliente,
                    "Abogado": abogado,
                    "Expediente": expediente,
                    "Año": anio,
                    "Materia": materia,
                    "Pretension": pretension,
                    "Observaciones": obs
                }
                casos = add_row(casos, nueva_fila, "casos")
                save_df("casos", casos)
                st.success("✅ Caso registrado")
                st.rerun()

    elif accion == "Editar":
        if casos.empty:
            st.info("No hay casos para editar.")
        else:
            sel_id = st.selectbox("Selecciona Caso (ID)", casos["ID"].tolist())
            fila = casos[casos["ID"] == sel_id].iloc[0]

            with st.form("editar_caso"):
                cliente = st.selectbox("Cliente", clientes_list,
                                       index=clientes_list.index(fila["Cliente"]) if fila["Cliente"] in clientes_list else 0)
                abogado = st.selectbox("Abogado", abogados_list,
                                       index=abogados_list.index(fila["Abogado"]) if fila["Abogado"] in abogados_list else 0)
                expediente = st.text_input("Número de Expediente", value=str(fila["Expediente"]))
                anio = st.text_input("Año", value=str(fila["Año"]))
                materia = st.text_input("Materia", value=str(fila["Materia"]))
                pretension = st.text_input("Pretensión", value=str(fila["Pretension"]))
                obs = st.text_area("Observaciones", value=str(fila["Observaciones"]))
                submit = st.form_submit_button("Guardar cambios")

                if submit:
                    idx = casos.index[casos["ID"] == sel_id][0]
                    casos.loc[idx, :] = [sel_id, cliente, abogado, expediente, anio, materia, pretension, obs]
                    casos = casos.reindex(columns=SCHEMAS["casos"])
                    save_df("casos", casos)
                    st.success("✅ Caso actualizado")
                    st.rerun()

    elif accion == "Eliminar":
        if casos.empty:
            st.info("No hay casos para eliminar.")
        else:
            sel_id = st.selectbox("Selecciona Caso (ID) a eliminar", casos["ID"].tolist())
            fila = casos[casos["ID"] == sel_id].iloc[0]
            st.warning(f"⚠️ Se eliminará el caso con expediente: {fila['Expediente']}")
            if st.button("Eliminar Caso"):
                casos = casos[casos["ID"] != sel_id].copy()
                save_df("casos", casos)
                st.success("🗑️ Caso eliminado")
                st.rerun()

    st.subheader("Listado")
    st.dataframe(casos, use_container_width=True)

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
            st.success("✅ Honorario guardado")
            st.rerun()

    st.dataframe(honorarios, use_container_width=True)

# =========================
# PAGOS HONORARIOS (con editar/eliminar)
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
        st.subheader("Editar / Eliminar pago")
        if pagos_honorarios.empty:
            st.info("Aún no hay pagos.")
        else:
            sel = st.selectbox("Selecciona pago por ID", pagos_honorarios["ID"].tolist())
            fila = pagos_honorarios[pagos_honorarios["ID"] == sel].iloc[0]

            with st.form("edit_pago_h"):
                caso_e = st.text_input("Caso", value=str(fila["Caso"]))
                fecha_e = st.text_input("Fecha (YYYY-MM-DD)", value=str(fila["FechaPago"]))
                monto_e = st.number_input("Monto", min_value=0.0, value=float(pd.to_numeric(fila["Monto"], errors="coerce") or 0), step=50.0)
                obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
                guardar = st.form_submit_button("Guardar cambios")

                if guardar:
                    idx = pagos_honorarios.index[pagos_honorarios["ID"] == sel][0]
                    pagos_honorarios.loc[idx, :] = [sel, caso_e, fecha_e, float(monto_e), obs_e]
                    pagos_honorarios = pagos_honorarios.reindex(columns=SCHEMAS["pagos_honorarios"])
                    save_df("pagos_honorarios", pagos_honorarios)
                    st.success("✅ Pago actualizado")
                    st.rerun()

            if st.button("Eliminar pago seleccionado"):
                pagos_honorarios = pagos_honorarios[pagos_honorarios["ID"] != sel].copy()
                save_df("pagos_honorarios", pagos_honorarios)
                st.success("🗑️ Pago eliminado")
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
            st.success("✅ Cuota Litis guardada")
            st.rerun()

    st.dataframe(cuota_litis, use_container_width=True)

# =========================
# PAGOS CUOTA LITIS (editar/eliminar)
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
            st.success("✅ Pago litis registrado")
            st.rerun()

        st.divider()
        st.subheader("Editar / Eliminar pago")
        if pagos_litis.empty:
            st.info("Aún no hay pagos litis.")
        else:
            sel = st.selectbox("Selecciona pago litis por ID", pagos_litis["ID"].tolist())
            fila = pagos_litis[pagos_litis["ID"] == sel].iloc[0]

            with st.form("edit_pago_l"):
                caso_e = st.text_input("Caso", value=str(fila["Caso"]))
                fecha_e = st.text_input("Fecha (YYYY-MM-DD)", value=str(fila["FechaPago"]))
                monto_e = st.number_input("Monto", min_value=0.0, value=float(pd.to_numeric(fila["Monto"], errors="coerce") or 0), step=50.0)
                obs_e = st.text_input("Observación", value=str(fila["Observacion"]))
                guardar = st.form_submit_button("Guardar cambios")

                if guardar:
                    idx = pagos_litis.index[pagos_litis["ID"] == sel][0]
                    pagos_litis.loc[idx, :] = [sel, caso_e, fecha_e, float(monto_e), obs_e]
                    pagos_litis = pagos_litis.reindex(columns=SCHEMAS["pagos_litis"])
                    save_df("pagos_litis", pagos_litis)
                    st.success("✅ Pago litis actualizado")
                    st.rerun()

            if st.button("Eliminar pago litis seleccionado"):
                pagos_litis = pagos_litis[pagos_litis["ID"] != sel].copy()
                save_df("pagos_litis", pagos_litis)
                st.success("🗑️ Pago litis eliminado")
                st.rerun()

    st.dataframe(pagos_litis, use_container_width=True)

# =========================
# CRONOGRAMA DE CUOTAS
# =========================
if menu == "Cronograma de Cuotas":
    st.title("📅 Cronograma de Cuotas (con vencimientos)")

    if casos.empty:
        st.info("Primero registra casos.")
    else:
        st.subheader("Agregar cuota al cronograma")
        caso = st.selectbox("Caso (Expediente)", casos["Expediente"].tolist())
        tipo = st.selectbox("Tipo", ["Honorarios", "CuotaLitis"])
        fecha_venc = st.date_input("Fecha de vencimiento", value=date.today())
        monto = st.number_input("Monto de la cuota", min_value=0.0, step=50.0)
        notas = st.text_input("Notas (opcional)")

        subset = cuotas[(cuotas["Caso"] == caso) & (cuotas["Tipo"] == tipo)].copy()
        nro = int(pd.to_numeric(subset["NroCuota"], errors="coerce").max()) + 1 if not subset.empty else 1

        if st.button("Guardar cuota"):
            new_id = next_id(cuotas)
            cuotas = add_row(cuotas, {
                "ID": new_id,
                "Caso": caso,
                "Tipo": tipo,
                "NroCuota": nro,
                "FechaVenc": str(fecha_venc),
                "Monto": float(monto),
                "Notas": notas
            }, "cuotas")
            save_df("cuotas", cuotas)
            st.success("✅ Cuota agregada al cronograma")
            st.rerun()

    st.divider()
    st.subheader("Estado de cuotas (pagos aplicados automáticamente: más antigua primero)")
    df_status = cuotas_status_all()
    if df_status.empty:
        st.info("Aún no hay cuotas registradas.")
    else:
        st.dataframe(df_status[["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento","Notas"]], use_container_width=True)

    st.divider()
    st.subheader("Eliminar cuota")
    if cuotas.empty:
        st.info("No hay cuotas para eliminar.")
    else:
        sel_id = st.selectbox("Selecciona cuota (ID) a eliminar", cuotas["ID"].tolist())
        if st.button("Eliminar cuota"):
            cuotas = cuotas[cuotas["ID"] != sel_id].copy()
            save_df("cuotas", cuotas)
            st.success("🗑️ Cuota eliminada")
            st.rerun()

# =========================
# RESUMEN FINANCIERO
# =========================
if menu == "Resumen Financiero":
    st.title("Resumen Financiero")

    df_resumen = resumen_financiero_df()
    st.subheader("Saldo total por caso")
    st.dataframe(df_resumen, use_container_width=True)

    st.subheader("Pendientes por cronograma (cuotas con saldo)")
    df_status = cuotas_status_all()
    df_pend = cuotas_pendientes(df_status)

    if df_pend.empty:
        st.info("No hay cuotas pendientes registradas.")
    else:
        st.dataframe(df_pend[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]], use_container_width=True)
``
