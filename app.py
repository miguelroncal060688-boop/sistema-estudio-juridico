import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta

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
    "cuotas": "cuotas.csv",  # NUEVO: cronograma
}

# =========================
# ESQUEMAS
# =========================
SCHEMAS = {
    "clientes": ["ID","Nombre","DNI","Celular","Correo","Direccion","Observaciones"],
    "abogados": ["ID","Nombre","DNI","Celular","Correo","Colegiatura","Domicilio Procesal","Casilla Electronica","Casilla Judicial"],
    "casos": ["ID","Cliente","Abogado","Expediente","Año","Materia","Pretension","Observaciones"],
    "honorarios": ["Caso","Monto Pactado"],

    # pagos con fecha + observación
    "pagos_honorarios": ["Caso","FechaPago","Monto","Observacion"],
    "cuota_litis": ["Caso","Monto Base","Porcentaje"],
    "pagos_litis": ["Caso","FechaPago","Monto","Observacion"],

    # NUEVO: cronograma de cuotas (sirve para honorarios o litis)
    # Tipo: "Honorarios" o "CuotaLitis"
    "cuotas": ["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","Notas"]
}

# =========================
# UTILIDADES CSV
# =========================
def ensure_csv(key: str):
    path = FILES[key]
    cols = SCHEMAS[key]

    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    df = pd.read_csv(path)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        for c in missing:
            df[c] = ""
        df = df[cols]
        df.to_csv(path, index=False)

def load_df(key: str) -> pd.DataFrame:
    ensure_csv(key)
    return pd.read_csv(FILES[key])

def save_df(key: str, df: pd.DataFrame):
    df = df[SCHEMAS[key]]
    df.to_csv(FILES[key], index=False)

def next_id(df: pd.DataFrame, col="ID") -> int:
    if df.empty:
        return 1
    try:
        return int(pd.to_numeric(df[col], errors="coerce").max()) + 1
    except Exception:
        return len(df) + 1

# Inicializar / migrar CSV
for k in FILES:
    ensure_csv(k)

# =========================
# LOGIN (simple)
# =========================
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"admin": {"password": "estudio123", "rol": "admin"}}

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
    "Cronograma de Cuotas",     # NUEVO
    "Resumen Financiero"
])

# =========================
# HELPERS FECHAS
# =========================
def to_date_safe(x):
    """Convierte a date o devuelve None."""
    if pd.isna(x) or str(x).strip() == "":
        return None
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

# =========================
# FINANZAS: RESUMEN + CUOTAS
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

        pactado = honorarios[honorarios["Caso"] == expediente]["Monto Pactado"].sum()
        pagado_h = pagos_honorarios[pagos_honorarios["Caso"] == expediente]["Monto"].sum()

        base = cuota_litis[cuota_litis["Caso"] == expediente]["Monto Base"].sum()
        porc_series = cuota_litis[cuota_litis["Caso"] == expediente]["Porcentaje"]
        porcentaje = float(porc_series.iloc[-1]) if len(porc_series) else 0.0

        calculada = float(base) * float(porcentaje) / 100.0
        pagado_l = pagos_litis[pagos_litis["Caso"] == expediente]["Monto"].sum()

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

def allocate_payments_oldest_first(cuotas_tipo_df: pd.DataFrame, pagos_tipo_df: pd.DataFrame, caso_col="Caso"):
    """
    Distribuye pagos a cuotas del caso desde la cuota más antigua (FechaVenc ascendente).
    Retorna df con PagadoAsignado, SaldoCuota, Estado y DíasParaVencimiento.
    """
    today = date.today()
    if cuotas_tipo_df.empty:
        return cuotas_tipo_df.assign(PagadoAsignado=0.0, SaldoCuota=0.0, Estado="", DiasParaVencimiento=None)

    df = cuotas_tipo_df.copy()

    # Normalizar tipos
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0.0)
    df["FechaVenc_dt"] = df["FechaVenc"].apply(to_date_safe)

    # Ordenar por vencimiento (None al final)
    df["_sort_date"] = df["FechaVenc_dt"].apply(lambda d: d if d is not None else date(2100,1,1))
    df.sort_values([caso_col, "_sort_date", "NroCuota"], inplace=True)

    # Total pagado por caso
    pagos_tipo_df = pagos_tipo_df.copy()
    pagos_tipo_df["Monto"] = pd.to_numeric(pagos_tipo_df["Monto"], errors="coerce").fillna(0.0)
    pagado_por_caso = pagos_tipo_df.groupby(caso_col)["Monto"].sum().to_dict()

    pagado_asignado = []
    saldo_cuota = []
    estado = []
    dias_venc = []

    remaining_by_case = {k: float(v) for k, v in pagado_por_caso.items()}

    for _, row in df.iterrows():
        caso = row[caso_col]
        monto_cuota = float(row["Monto"])
        venc = row["FechaVenc_dt"]

        rem = remaining_by_case.get(caso, 0.0)
        asignado = min(rem, monto_cuota) if monto_cuota > 0 else 0.0
        remaining_by_case[caso] = rem - asignado

        saldo = monto_cuota - asignado

        if monto_cuota == 0:
            est = "Sin monto"
        elif saldo <= 0.00001:
            est = "Pagada"
        elif asignado > 0:
            est = "Parcial"
        else:
            est = "Pendiente"

        if venc is None:
            dv = None
        else:
            dv = (venc - today).days

        pagado_asignado.append(asignado)
        saldo_cuota.append(saldo)
        estado.append(est)
        dias_venc.append(dv)

    df["PagadoAsignado"] = pagado_asignado
    df["SaldoCuota"] = saldo_cuota
    df["Estado"] = estado
    df["DiasParaVencimiento"] = dias_venc

    df.drop(columns=["_sort_date"], inplace=True, errors="ignore")
    return df

def cuotas_status_all():
    """Construye status para cuotas de Honorarios y CuotaLitis."""
    if cuotas.empty:
        return pd.DataFrame()

    # cuotas honorarios
    q_h = cuotas[cuotas["Tipo"] == "Honorarios"].copy()
    # cuotas litis
    q_l = cuotas[cuotas["Tipo"] == "CuotaLitis"].copy()

    # pagos honorarios y litis
    ph = pagos_honorarios.copy()
    pl = pagos_litis.copy()

    # Asegurar columnas de fecha/obs existen
    # (ya se migran en ensure_csv)
    st_h = allocate_payments_oldest_first(q_h, ph)
    st_l = allocate_payments_oldest_first(q_l, pl)

    out = pd.concat([st_h, st_l], ignore_index=True) if not st_h.empty or not st_l.empty else pd.DataFrame()
    return out

def cuotas_pendientes(df_cuotas_status: pd.DataFrame):
    """Filtra cuotas con saldo > 0."""
    if df_cuotas_status.empty:
        return df_cuotas_status
    return df_cuotas_status[df_cuotas_status["SaldoCuota"] > 0].copy()

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("📊 Dashboard General")

    df_res = resumen_financiero_df()
    df_cuotas_status = cuotas_status_all()
    df_cuotas_pend = cuotas_pendientes(df_cuotas_status)

    # Totales (saldo total)
    total_pactado = df_res["Honorario Pactado"].sum() if not df_res.empty else 0
    total_pagado_h = df_res["Honorario Pagado"].sum() if not df_res.empty else 0
    total_pend_h = df_res["Honorario Pendiente"].sum() if not df_res.empty else 0

    total_litis = df_res["Cuota Litis Calculada"].sum() if not df_res.empty else 0
    total_pagado_l = df_res["Pagado Litis"].sum() if not df_res.empty else 0
    total_pend_l = df_res["Saldo Litis"].sum() if not df_res.empty else 0

    # Totales por cronograma
    today = date.today()
    vencidas = pd.DataFrame()
    por_vencer = pd.DataFrame()

    if not df_cuotas_pend.empty:
        # Vencidas: DiasParaVencimiento < 0
        vencidas = df_cuotas_pend[df_cuotas_pend["DiasParaVencimiento"].notna() & (df_cuotas_pend["DiasParaVencimiento"] < 0)]
        # Por vencer en 7 días: 0..7
        por_vencer = df_cuotas_pend[df_cuotas_pend["DiasParaVencimiento"].notna() & (df_cuotas_pend["DiasParaVencimiento"].between(0, 7))]

    total_vencidas = float(vencidas["SaldoCuota"].sum()) if not vencidas.empty else 0.0
    total_por_vencer = float(por_vencer["SaldoCuota"].sum()) if not por_vencer.empty else 0.0

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
    d1, d2, d3 = st.columns(3)
    d1.metric("🚨 Cuotas vencidas (S/)", f"{total_vencidas:,.2f}")
    d2.metric("⏱️ Por vencer (7 días) (S/)", f"{total_por_vencer:,.2f}")
    d3.metric("📌 Total cuotas pendientes (S/)", f"{float(df_cuotas_pend['SaldoCuota'].sum()) if not df_cuotas_pend.empty else 0.0:,.2f}")

    st.divider()

    e1, e2, e3 = st.columns(3)
    e1.metric("👥 Total Clientes", len(clientes))
    e2.metric("📁 Total Casos", len(casos))
    e3.metric("👨‍⚖️ Total Abogados", len(abogados))

    st.subheader("🚨 Reporte: Cuotas Vencidas")
    if vencidas.empty:
        st.info("No hay cuotas vencidas con saldo pendiente.")
    else:
        st.dataframe(
            vencidas[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]],
            use_container_width=True
        )

    st.subheader("⏱️ Reporte: Cuotas por Vencer (7 días)")
    if por_vencer.empty:
        st.info("No hay cuotas por vencer en los próximos 7 días.")
    else:
        st.dataframe(
            por_vencer[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]],
            use_container_width=True
        )

# =========================
# CLIENTES (CRUD simple)
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
                clientes.loc[len(clientes)] = [new_id,nombre,dni,celular,correo,direccion,obs]
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
                    clientes.loc[idx] = [sel_id,nombre,dni,celular,correo,direccion,obs]
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
                abogados.loc[len(abogados)] = [new_id,nombre,dni,celular,correo,coleg,dom,cas_e,cas_j]
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
                    abogados.loc[idx] = [sel_id,nombre,dni,celular,correo,coleg,dom,cas_e,cas_j]
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
                casos.loc[len(casos)] = [new_id,cliente,abogado,expediente,anio,materia,pretension,obs]
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
                    casos.loc[idx] = [sel_id,cliente,abogado,expediente,anio,materia,pretension,obs]
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
            honorarios.loc[len(honorarios)] = [caso, float(monto)]
            save_df("honorarios", honorarios)
            st.success("✅ Honorario guardado")
            st.rerun()

    st.dataframe(honorarios, use_container_width=True)

# =========================
# PAGOS HONORARIOS
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
            pagos_honorarios.loc[len(pagos_honorarios)] = [caso, str(fecha), float(monto), obs]
            save_df("pagos_honorarios", pagos_honorarios)
            st.success("✅ Pago registrado")
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
            cuota_litis.loc[len(cuota_litis)] = [caso, float(base), float(porcentaje)]
            save_df("cuota_litis", cuota_litis)
            st.success("✅ Cuota Litis guardada")
            st.rerun()

    st.dataframe(cuota_litis, use_container_width=True)

# =========================
# PAGOS CUOTA LITIS
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
            pagos_litis.loc[len(pagos_litis)] = [caso, str(fecha), float(monto), obs]
            save_df("pagos_litis", pagos_litis)
            st.success("✅ Pago litis registrado")
            st.rerun()

    st.dataframe(pagos_litis, use_container_width=True)

# =========================
# NUEVO: CRONOGRAMA DE CUOTAS
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

        # calcular número de cuota automático por caso+tipo
        subset = cuotas[(cuotas["Caso"] == caso) & (cuotas["Tipo"] == tipo)]
        nro = int(pd.to_numeric(subset["NroCuota"], errors="coerce").max()) + 1 if not subset.empty else 1

        if st.button("Guardar cuota"):
            new_id = next_id(cuotas)
            cuotas.loc[len(cuotas)] = [new_id, caso, tipo, nro, str(fecha_venc), float(monto), notas]
            save_df("cuotas", cuotas)
            st.success("✅ Cuota agregada al cronograma")
            st.rerun()

    st.divider()
    st.subheader("Estado de cuotas (pagos asignados automáticamente al vencimiento más antiguo)")
    df_status = cuotas_status_all()
    if df_status.empty:
        st.info("Aún no hay cuotas registradas.")
    else:
        st.dataframe(
            df_status[["ID","Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento","Notas"]],
            use_container_width=True
        )

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
        st.dataframe(
            df_pend[["Caso","Tipo","NroCuota","FechaVenc","Monto","PagadoAsignado","SaldoCuota","Estado","DiasParaVencimiento"]],
            use_container_width=True
        )
