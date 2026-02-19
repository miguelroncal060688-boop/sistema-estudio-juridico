import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="⚖️ Estudio de Abogados Roncal Liñán y Asociados", layout="wide")

# ------------------------
# INICIALIZACIÓN LIMPIA
# ------------------------

if "usuarios" not in st.session_state:
    st.session_state.usuarios = pd.DataFrame(columns=[
        "usuario","password","rol","abogado_id"
    ])
    st.session_state.usuarios.loc[0] = ["admin","admin123","admin",None]

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame(columns=[
        "id","nombre","dni","telefono","correo","direccion"
    ])

if "abogados" not in st.session_state:
    st.session_state.abogados = pd.DataFrame(columns=[
        "id","nombre","dni","celular","correo",
        "colegiatura","domicilio_procesal",
        "casilla_electronica","casilla_judicial"
    ])

if "casos" not in st.session_state:
    st.session_state.casos = pd.DataFrame(columns=[
        "id","expediente","anio","cliente_id","abogado_id","materia","estado"
    ])

if "honorarios" not in st.session_state:
    st.session_state.honorarios = pd.DataFrame(columns=[
        "id","caso_id","monto_total"
    ])

if "cronograma" not in st.session_state:
    st.session_state.cronograma = pd.DataFrame(columns=[
        "id","honorario_id","fecha","monto","pagado"
    ])

if "cuota_litis" not in st.session_state:
    st.session_state.cuota_litis = pd.DataFrame(columns=[
        "id","caso_id","porcentaje","monto_estimado"
    ])

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.usuario_actual = None
    st.session_state.rol = None
    st.session_state.abogado_id = None

# ------------------------
# LOGIN
# ------------------------

if not st.session_state.login:
    st.title("⚖️ Estudio de Abogados Roncal Liñán y Asociados")
    st.subheader("Ingreso al Sistema")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        df = st.session_state.usuarios
        valid = df[(df["usuario"]==user) & (df["password"]==pwd)]
        if not valid.empty:
            st.session_state.login = True
            st.session_state.usuario_actual = user
            st.session_state.rol = valid.iloc[0]["rol"]
            st.session_state.abogado_id = valid.iloc[0]["abogado_id"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# ------------------------
# TÍTULO
# ------------------------

st.title("⚖️ Estudio de Abogados Roncal Liñán y Asociados")

# ------------------------
# MENÚ
# ------------------------

menu = [
    "Dashboard",
    "Clientes",
    "Abogados",
    "Usuarios",
    "Casos",
    "Honorarios",
    "Cronograma",
    "Cuota Litis",
    "Pendientes",
    "Resumen Financiero"
]

choice = st.sidebar.selectbox("Menú", menu)

# ------------------------
# DASHBOARD
# ------------------------

if choice == "Dashboard":

    total_honorarios = st.session_state.honorarios["monto_total"].sum()

    pagado = st.session_state.cronograma[
        st.session_state.cronograma["pagado"]==True
    ]["monto"].sum()

    pendiente = st.session_state.cronograma[
        st.session_state.cronograma["pagado"]==False
    ]["monto"].sum()

    c1,c2,c3 = st.columns(3)
    c1.metric("Total Honorarios Pactados", f"S/ {total_honorarios:,.2f}")
    c2.metric("Total Cobrado", f"S/ {pagado:,.2f}")
    c3.metric("Total Pendiente", f"S/ {pendiente:,.2f}")

# ------------------------
# CLIENTES
# ------------------------

if choice == "Clientes" and st.session_state.rol=="admin":

    st.subheader("Registrar Cliente")

    with st.form("cliente"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")
        if st.form_submit_button("Guardar"):
            new_id = len(st.session_state.clientes)+1
            st.session_state.clientes.loc[len(st.session_state.clientes)] = [
                new_id,nombre,dni,telefono,correo,direccion
            ]
            st.success("Cliente registrado")

    st.dataframe(st.session_state.clientes)

# ------------------------
# ABOGADOS
# ------------------------

if choice == "Abogados" and st.session_state.rol=="admin":

    st.subheader("Registrar Abogado")

    with st.form("abogado"):
        nombre = st.text_input("Nombre")
        dni = st.text_input("DNI")
        celular = st.text_input("Celular")
        correo = st.text_input("Correo")
        colegiatura = st.text_input("Colegiatura")
        domicilio = st.text_input("Domicilio Procesal")
        casilla_e = st.text_input("Casilla Electrónica")
        casilla_j = st.text_input("Casilla Judicial")

        if st.form_submit_button("Guardar"):
            new_id = len(st.session_state.abogados)+1
            st.session_state.abogados.loc[len(st.session_state.abogados)] = [
                new_id,nombre,dni,celular,correo,
                colegiatura,domicilio,casilla_e,casilla_j
            ]
            st.success("Abogado registrado")

    st.dataframe(st.session_state.abogados)

# ------------------------
# USUARIOS
# ------------------------

if choice == "Usuarios" and st.session_state.rol=="admin":

    st.subheader("Crear Usuario Abogado")

    abogados = st.session_state.abogados

    if not abogados.empty:

        abogado_sel = st.selectbox(
            "Seleccionar Abogado",
            abogados["nombre"]
        )

        abogado_id = abogados[
            abogados["nombre"]==abogado_sel
        ]["id"].values[0]

        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña")

        if st.button("Crear Usuario"):
            st.session_state.usuarios.loc[len(st.session_state.usuarios)] = [
                usuario,password,"abogado",abogado_id
            ]
            st.success("Usuario creado")

    st.dataframe(st.session_state.usuarios)

# ------------------------
# CASOS
# ------------------------

if choice == "Casos":

    if st.session_state.rol=="admin":
        st.subheader("Registrar Caso")

        if not st.session_state.clientes.empty and not st.session_state.abogados.empty:

            cliente = st.selectbox("Cliente", st.session_state.clientes["nombre"])
            abogado = st.selectbox("Abogado", st.session_state.abogados["nombre"])

            expediente = st.text_input("Expediente")
            anio = st.number_input("Año", step=1)
            materia = st.text_input("Materia")
            estado = st.text_input("Estado")

            if st.button("Guardar Caso"):
                new_id = len(st.session_state.casos)+1
                cliente_id = st.session_state.clientes[
                    st.session_state.clientes["nombre"]==cliente
                ]["id"].values[0]

                abogado_id = st.session_state.abogados[
                    st.session_state.abogados["nombre"]==abogado
                ]["id"].values[0]

                st.session_state.casos.loc[len(st.session_state.casos)] = [
                    new_id,expediente,anio,cliente_id,abogado_id,materia,estado
                ]
                st.success("Caso registrado")

        st.dataframe(st.session_state.casos)

    else:
        casos = st.session_state.casos[
            st.session_state.casos["abogado_id"]==st.session_state.abogado_id
        ]
        st.dataframe(casos)

# ------------------------
# HONORARIOS + CRONOGRAMA
# ------------------------

if choice == "Honorarios" and st.session_state.rol=="admin":

    if not st.session_state.casos.empty:

        caso_id = st.selectbox("Caso", st.session_state.casos["id"])
        monto = st.number_input("Monto Total Honorarios", min_value=0.0)
        cuotas = st.number_input("Número de Cuotas", step=1)
        fecha_inicio = st.date_input("Fecha Inicio")

        if st.button("Generar Cronograma"):
            new_id = len(st.session_state.honorarios)+1
            st.session_state.honorarios.loc[len(st.session_state.honorarios)] = [
                new_id,caso_id,monto
            ]

            monto_cuota = monto / cuotas

            for i in range(int(cuotas)):
                st.session_state.cronograma.loc[len(st.session_state.cronograma)] = [
                    len(st.session_state.cronograma)+1,
                    new_id,
                    fecha_inicio + timedelta(days=30*i),
                    monto_cuota,
                    False
                ]

            st.success("Honorario y cronograma generado")

    st.dataframe(st.session_state.honorarios)

# ------------------------
# CRONOGRAMA
# ------------------------

if choice == "Cronograma":

    df = st.session_state.cronograma

    if not df.empty:
        for i,row in df.iterrows():
            col1,col2,col3,col4 = st.columns(4)
            col1.write(f"Fecha: {row['fecha']}")
            col2.write(f"Monto: {row['monto']}")
            col3.write(f"Pagado: {row['pagado']}")
            if not row["pagado"]:
                if col4.button("Marcar Pagado", key=i):
                    st.session_state.cronograma.at[i,"pagado"] = True
                    st.rerun()

# ------------------------
# CUOTA LITIS
# ------------------------

if choice == "Cuota Litis" and st.session_state.rol=="admin":

    if not st.session_state.casos.empty:
        caso = st.selectbox("Caso", st.session_state.casos["id"])
        porcentaje = st.number_input("Porcentaje", min_value=0.0)

        if st.button("Registrar"):
            st.session_state.cuota_litis.loc[len(st.session_state.cuota_litis)] = [
                len(st.session_state.cuota_litis)+1,
                caso,
                porcentaje,
                0
            ]
            st.success("Cuota Litis registrada")

    st.dataframe(st.session_state.cuota_litis)

# ------------------------
# PENDIENTES
# ------------------------

if choice == "Pendientes":

    pendientes = st.session_state.cronograma[
        st.session_state.cronograma["pagado"]==False
    ]

    st.dataframe(pendientes)

# ------------------------
# RESUMEN FINANCIERO
# ------------------------

if choice == "Resumen Financiero":

    st.subheader("Tabla Honorarios")
    st.dataframe(st.session_state.honorarios)

    st.subheader("Tabla Cuota Litis")
    st.dataframe(st.session_state.cuota_litis)
