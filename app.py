import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sistema Jurídico PRO", layout="wide")

# ================= CSV USUARIOS =================
USUARIOS_CSV = "usuarios.csv"

def cargar_usuarios():
    if os.path.exists(USUARIOS_CSV):
        return pd.read_csv(USUARIOS_CSV)
    else:
        # Usuario admin por defecto
        df = pd.DataFrame([{"Usuario":"admin","Contraseña":"estudio123","Rol":"admin"}])
        df.to_csv(USUARIOS_CSV,index=False)
        return df

usuarios = cargar_usuarios()

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.usuario = None
    st.session_state.rol = None

if not st.session_state.login:
    st.title("Acceso al Sistema Jurídico")
    usuario = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        user = usuarios[(usuarios["Usuario"]==usuario) & (usuarios["Contraseña"]==pwd)]
        if not user.empty:
            st.session_state.login = True
            st.session_state.usuario = usuario
            st.session_state.rol = user.iloc[0]["Rol"]
            st.success(f"Bienvenido {usuario} ({st.session_state.rol})")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ================= FUNCIONES =================
def cargar_csv(nombre):
    if os.path.exists(nombre):
        return pd.read_csv(nombre)
    return pd.DataFrame()

def guardar_csv(df, nombre):
    df.to_csv(nombre, index=False)

clientes = cargar_csv("clientes.csv")
casos = cargar_csv("casos.csv")
pagos = cargar_csv("pagos.csv")

menu = st.sidebar.selectbox("Menú", ["Dashboard","Clientes","Casos","Pagos","Contrato","Usuarios"])

# ================= CLIENTES =================
if menu == "Clientes":
    st.title("Gestión de Clientes")

    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
    with col2:
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")

    if st.button("Guardar Cliente"):
        if dni in clientes["DNI"].values:
            st.warning("Cliente ya registrado")
        else:
            nuevo = pd.DataFrame([{
                "Nombre": nombre,
                "DNI": dni,
                "Celular": celular,
                "Correo": correo,
                "Dirección": direccion
            }])
            clientes = pd.concat([clientes, nuevo], ignore_index=True)
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente guardado")
            st.rerun()

    if not clientes.empty:
        st.subheader("Clientes registrados")
        for i in clientes.index:
            c = clientes.loc[i]
            st.write(f"{c['Nombre']} | DNI: {c['DNI']} | Celular: {c['Celular']}")
            col_edit, col_del = st.columns([1,1])
            if col_edit.button("Editar",key=f"editar_c{i}"):
                st.session_state.edit_cliente = i
            if col_del.button("Eliminar",key=f"elim_c{i}"):
                clientes.drop(i,inplace=True)
                clientes.reset_index(drop=True,inplace=True)
                guardar_csv(clientes,"clientes.csv")
                st.success("Cliente eliminado")
                st.rerun()

    # Editar cliente
    if "edit_cliente" in st.session_state:
        i = st.session_state.edit_cliente
        c = clientes.loc[i]
        st.subheader(f"Editar Cliente: {c['Nombre']}")
        nombre_e = st.text_input("Nombre completo",c['Nombre'])
        dni_e = st.text_input("DNI",c['DNI'])
        celular_e = st.text_input("Celular",c['Celular'])
        correo_e = st.text_input("Correo",c['Correo'])
        direccion_e = st.text_input("Dirección",c['Dirección'])
        if st.button("Guardar Cambios"):
            clientes.loc[i] = [nombre_e,dni_e,celular_e,correo_e,direccion_e]
            guardar_csv(clientes,"clientes.csv")
            st.success("Cliente actualizado")
            del st.session_state.edit_cliente
            st.rerun()

# ================= CASOS =================
if menu == "Casos":
    st.title("Gestión de Casos")

    cliente = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
    expediente = st.text_input("Número de expediente")
    año = st.text_input("Año")
    materia = st.text_input("Materia")
    monto = st.number_input("Monto pactado",0.0)
    cuota_litis = st.number_input("Porcentaje Cuota Litis (%)",0.0)
    monot_base = st.number_input("Monto Base",0.0)

    if st.button("Guardar Caso"):
        identificador = f"{expediente}-{año}-{cliente}"
        if identificador in casos.get("ID_CASO",[]).values:
            st.warning("Caso ya registrado")
        else:
            nuevo = pd.DataFrame([{
                "ID_CASO": identificador,
                "Cliente":cliente,
                "Expediente":expediente,
                "Año":año,
                "Materia":materia,
                "Monto":monto,
                "Cuota_Litis":cuota_litis,
                "Monot_Base":monot_base
            }])
            casos = pd.concat([casos,nuevo],ignore_index=True)
            guardar_csv(casos,"casos.csv")
            st.success("Caso guardado")
            st.rerun()

    if not casos.empty:
        st.subheader("Casos registrados")
        for i in casos.index:
            c = casos.loc[i]
            st.write(f"{c['Cliente']} | {c['ID_CASO']} | S/ {c['Monto']}")
            col_edit, col_del = st.columns([1,1])
            if col_edit.button("Editar",key=f"editar_cas{i}"):
                st.session_state.edit_caso = i
            if col_del.button("Eliminar",key=f"elim_cas{i}"):
                casos.drop(i,inplace=True)
                casos.reset_index(drop=True,inplace=True)
                guardar_csv(casos,"casos.csv")
                st.success("Caso eliminado")
                st.rerun()

    # Editar caso
    if "edit_caso" in st.session_state:
        i = st.session_state.edit_caso
        c = casos.loc[i]
        st.subheader(f"Editar Caso: {c['ID_CASO']}")
        expediente_e = st.text_input("Número de expediente",c['Expediente'])
        año_e = st.text_input("Año",c['Año'])
        cliente_e = st.selectbox("Cliente", clientes["Nombre"], index=clientes[clientes["Nombre"]==c['Cliente']].index[0])
        materia_e = st.text_input("Materia",c['Materia'])
        monto_e = st.number_input("Monto pactado",c['Monto'])
        cuota_litis_e = st.number_input("Cuota Litis (%)",c['Cuota_Litis'])
        monot_base_e = st.number_input("Monto Base",c['Monot_Base'])
        if st.button("Guardar Cambios Caso"):
            casos.loc[i] = [f"{expediente_e}-{año_e}-{cliente_e}",cliente_e,expediente_e,año_e,materia_e,monto_e,cuota_litis_e,monot_base_e]
            guardar_csv(casos,"casos.csv")
            st.success("Caso actualizado")
            del st.session_state.edit_caso
            st.rerun()

# ================= PAGOS =================
if menu == "Pagos":
    st.title("Registro de Pagos")

    caso_sel = st.selectbox("Caso", casos["ID_CASO"] if not casos.empty else [])
    cliente_sel = st.selectbox("Cliente", clientes["Nombre"] if not clientes.empty else [])
    fecha = st.date_input("Fecha")
    monto_pago = st.number_input("Monto pagado",0.0)

    if st.button("Registrar Pago"):
        nuevo = pd.DataFrame([{
            "ID_CASO":caso_sel,
            "Cliente":cliente_sel,
            "Fecha":fecha,
            "Monto":monto_pago
        }])
        pagos = pd.concat([pagos,nuevo],ignore_index=True)
        guardar_csv(pagos,"pagos.csv")
        st.success("Pago registrado")
        st.rerun()

    if not pagos.empty:
        st.subheader("Pagos registrados")
        for i in pagos.index:
            p = pagos.loc[i]
            st.write(f"{p['Cliente']} | {p['ID_CASO']} | S/ {p['Monto']} | {p['Fecha']}")
            col_del, = st.columns([1])
            if col_del.button("Eliminar",key=f"elim_pago{i}"):
                pagos.drop(i,inplace=True)
                pagos.reset_index(drop=True,inplace=True)
                guardar_csv(pagos,"pagos.csv")
                st.success("Pago eliminado")
                st.rerun()

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("Dashboard Financiero")

    total_clientes = len(clientes)
    total_casos = len(casos)
    total_ingresos = pagos["Monto"].sum() if not pagos.empty else 0

    # Saldo pendiente por caso
    df_saldo = casos.copy()
    df_saldo["Pagado"] = df_saldo["ID_CASO"].apply(lambda x: pagos[pagos["ID_CASO"]==x]["Monto"].sum() if not pagos.empty else 0)
    df_saldo["Saldo"] = df_saldo["Monto"] - df_saldo["Pagado"]

    total_pendiente = df_saldo["Saldo"].sum() if not df_saldo.empty else 0

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Clientes", total_clientes)
    col2.metric("Casos", total_casos)
    col3.metric("Ingresos", f"S/ {total_ingresos}")
    col4.metric("Pendiente", f"S/ {total_pendiente}")

    st.subheader("Saldos por Caso")
    st.dataframe(df_saldo[["ID_CASO","Cliente","Monto","Pagado","Saldo"]])

# ================= CONTRATO =================
if menu == "Contrato":
    st.title("Generar Contrato")

    caso_sel = st.selectbox("Caso", casos["ID_CASO"] if not casos.empty else [])
    contraparte = st.text_input("Contraparte")

    if caso_sel and contraparte:
        c = casos[casos["ID_CASO"]==caso_sel].iloc[0]
        contrato_text = f"""
CONTRATO DE PRESTACIÓN DE SERVICIOS

Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en el Psje. Victoria N° 280 – Barrio San Martín, a quien en adelante se denominará EL LOCADOR; y, de la otra parte, {contraparte}, a quien en adelante se denominará EL CLIENTE.

PRIMERO: ANTECEDENTES
EL LOCADOR es abogado habilitado con colegiatura N° 2710.
EL CLIENTE requiere contratar los servicios de EL LOCADOR conforme al objeto del contrato.

SEGUNDO: OBJETO DEL CONTRATO
Por el presente contrato EL LOCADOR se obliga a patrocinar a EL CLIENTE en los procesos judiciales y administrativos relacionados con el expediente {c['Expediente']} del año {c['Año']}.

TERCERO: CONTRAPRESTACIÓN
Monto pactado: S/ {c['Monto']}
Cuota Litis: {c['Cuota_Litis']}%
Monto Base: S/ {c['Monot_Base']}

CUARTO: VIGENCIA
Duración por tiempo indeterminado hasta rescisión por mutuo acuerdo.

QUINTO: PROPIEDAD INTELECTUAL
Toda documentación elaborada por EL LOCADOR es cedida a EL CLIENTE.

SEXTO: CLÁUSULA RESOLUTORIA
El contrato podrá resolverse de mutuo acuerdo o por incumplimiento de obligaciones.

SÉPTIMO: COMPETENCIA
Renuncia a la competencia jurisdiccional y se establece en la Corte Superior de Justicia de Cajamarca.

OCTAVO: CONFORMIDAD
Firmado a los {datetime.today().day} días del mes de {datetime.today().strftime('%B')} del año {datetime.today().year}.
        """
        st.text_area("Contrato Generado",contrato_text,height=500)

# ================= USUARIOS =================
if menu == "Usuarios" and st.session_state.rol=="admin":
    st.title("Gestión de Usuarios")

    nuevo_user = st.text_input("Usuario nuevo")
    nueva_clave = st.text_input("Contraseña", type="password")
    rol_user = st.selectbox("Rol",["admin","usuario"])
    if st.button("Agregar Usuario"):
        if nuevo_user in usuarios["Usuario"].values:
            st.warning("Usuario ya existe")
        else:
            usuarios = pd.concat([usuarios,pd.DataFrame([{"Usuario":nuevo_user,"Contraseña":nueva_clave,"Rol":rol_user}])],ignore_index=True)
            guardar_csv(usuarios,USUARIOS_CSV)
            st.success("Usuario creado")
            st.rerun()
