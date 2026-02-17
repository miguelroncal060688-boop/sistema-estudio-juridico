import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
from datetime import datetime
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LexControl v2.0", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DATOS (Auto-creación) ---
def conectar_db():
    conn = sqlite3.connect('estudio_juridico.db', check_same_thread=False)
    return conn

def init_db():
    conn = conectar_db()
    c = conn.cursor()
    # Clientes: Natural o Jurídica
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, nombre TEXT, documento TEXT, 
                  direccion TEXT, correo TEXT, celular TEXT, contacto_emergencia TEXT, 
                  tel_emergencia TEXT, representante TEXT, dni_rep TEXT)''')
    # Casos
    c.execute('''CREATE TABLE IF NOT EXISTS casos 
                 (id_exp TEXT PRIMARY KEY, cliente_id INTEGER, materia TEXT, 
                  etapa TEXT, abogado TEXT, monto_pactado REAL, cuota_litis_pct REAL, 
                  pretension REAL, saldo_monto REAL, FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
    # Pagos
    c.execute('''CREATE TABLE IF NOT EXISTS pagos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, caso_id TEXT, fecha TEXT, 
                  monto_pagado REAL, concepto TEXT, FOREIGN KEY(caso_id) REFERENCES casos(id_exp))''')
    conn.commit()
    conn.close()

init_db()

# --- GENERADOR DE CONTRATO PROFESIONAL ---
class ContratoPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'CONTRATO DE PRESTACIÓN DE SERVICIOS LEGALES', 0, 1, 'C')
        self.ln(10)

def generar_contrato_pdf(cli, casos):
    pdf = ContratoPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Datos de las partes
    parte_cliente = f"{cli['nombre'].upper()} con DNI/RUC N° {cli['documento']}"
    if cli['tipo'] == "Jurídica":
        parte_cliente += f", representada por su gerente {cli['representante']} con DNI {cli['dni_rep']}"

    texto_cuerpo = f"""Conste por el presente documento el CONTRATO DE LOCACIÓN DE SERVICIOS que celebran de una parte el Sr. MIGUEL ANTONIO RONCAL LIÑÁN, identificado con DNI N° 70205926, domiciliado en el Psje. Victoria N° 280 – Barrio San Martín, Cajamarca, a quien en adelante se denominará EL LOCADOR; y, de la otra parte, {parte_cliente}, domiciliado en {cli['direccion']}, a quien en adelante se denominará EL CLIENTE.

PRIMERO: EL LOCADOR es abogado habilitado con colegiatura N° 2710. EL CLIENTE requiere sus servicios para los siguientes procesos:
"""
    pdf.multi_cell(0, 5, texto_cuerpo)
    pdf.ln(5)

    # Detalle de Casos y Montos
    for idx, c in enumerate(casos):
        pdf.set_font("Arial", 'B', 10)
        pdf.multi_cell(0, 5, f"{idx+1}. Expediente N° {c[0]} - Materia: {c[2]}")
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, f"   Contraprestación: S/ {c[5]:,.2f} + {c[6]}% de Cuota Litis.")
    
    clausulas_finales = f"""
TERCERO: Los pagos se realizarán de común acuerdo. Los gastos operativos corren por cuenta de EL CLIENTE.
SÉPTIMO: Para cualquier controversia, las partes se someten a la Sede Central de la Corte Superior de Justicia de Cajamarca.

Se firma en señal de conformidad a los {datetime.now().day} días del mes de {datetime.now().month} del año {datetime.now().year}.
"""
    pdf.ln(10)
    pdf.multi_cell(0, 5, clausulas_finales)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
def main():
    st.sidebar.title("🔐 LexControl Login")
    user = st.sidebar.text_input("Usuario")
    pas = st.sidebar.text_input("Contraseña", type="password")

    if user == "admin" and pas == "abogado2026": # CAMBIA ESTO PARA SEGURIDAD
        conn = conectar_db()
        st.title("⚖️ Sistema de Gestión Jurídica")

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "👤 Clientes y Casos", "💰 Pagos y Cobros", "📄 Contratos y Reportes"])

        with tab1:
            st.subheader("Estado Financiero del Estudio")
            df_c = pd.read_sql("SELECT * FROM casos", conn)
            df_p = pd.read_sql("SELECT * FROM pagos", conn)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Expedientes", len(df_c))
            c2.metric("Total Pactado", f"S/ {df_c['monto_pactado'].sum():,.2f}")
            c3.metric("Total Cobrado", f"S/ {df_p['monto_pagado'].sum():,.2f}")
            c4.metric("Pendiente", f"S/ {df_c['saldo_monto'].sum():,.2f}", delta_color="inverse")
            
            st.write("### Listado Maestro de Casos")
            st.dataframe(df_c, use_container_width=True)

        with tab2:
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("### Registrar Cliente")
                t_cli = st.selectbox("Tipo Cliente", ["Natural", "Jurídica"])
                nom = st.text_input("Nombre Completo / Razón Social")
                doc = st.text_input("DNI o RUC")
                dir_c = st.text_input("Dirección Fiscal")
                cel = st.text_input("Celular de Contacto")
                rep = st.text_input("Representante Legal (Solo Jurídica)")
                d_rep = st.text_input("DNI Representante")
                if st.button("💾 Guardar Cliente"):
                    conn.execute("INSERT INTO clientes (tipo, nombre, documento, direccion, celular, representante, dni_rep) VALUES (?,?,?,?,?,?,?)", 
                                 (t_cli, nom, doc, dir_c, cel, rep, d_rep))
                    conn.commit()
                    st.success("Cliente creado correctamente")

            with col_b:
                st.write("### Abrir Nuevo Expediente")
                clis = pd.read_sql("SELECT id, nombre FROM clientes", conn)
                if not clis.empty:
                    c_id = st.selectbox("Seleccionar Cliente", clis['id'].tolist(), format_func=lambda x: clis[clis['id']==x]['nombre'].values[0])
                    exp = st.text_input("N° Expediente-Año (Ej: 1540-2024)")
                    mat = st.text_input("Materia (Ej: Laboral / Alimentos)")
                    abog = st.text_input("Abogado Asignado")
                    mnt = st.number_input("Monto Pactado S/", min_value=0.0)
                    lit = st.number_input("Cuota Litis %", 0, 100)
                    if st.button("📂 Registrar Caso"):
                        conn.execute("INSERT INTO casos (id_exp, cliente_id, materia, abogado, monto_pactado, cuota_litis_pct, saldo_monto) VALUES (?,?,?,?,?,?,?)",
                                     (exp, c_id, mat, abog, mnt, lit, mnt))
                        conn.commit()
                        st.success("Expediente aperturado")

        with tab3:
            st.write("### Control de Pagos por Expediente")
            casos_list = pd.read_sql("SELECT id_exp, saldo_monto FROM casos WHERE saldo_monto > 0", conn)
            if not casos_list.empty:
                c_sel = st.selectbox("Seleccionar Expediente Deudor", casos_list['id_exp'].tolist())
                m_pago = st.number_input("Monto Recibido S/", min_value=1.0)
                f_pago = st.date_input("Fecha de Pago")
                concepto = st.text_input("Concepto (Ej: Adelanto / Cuota 1)")
                if st.button("💵 Registrar Cobro"):
                    conn.execute("INSERT INTO pagos (caso_id, fecha, monto_pagado, concepto) VALUES (?,?,?,?)", (c_sel, str(f_pago), m_pago, concepto))
                    conn.execute("UPDATE casos SET saldo_monto = saldo_monto - ? WHERE id_exp = ?", (m_pago, c_sel))
                    conn.commit()
                    st.rerun()
            else:
                st.info("No hay saldos pendientes.")

        with tab4:
            st.write("### Generación de Documentos")
            clis_doc = pd.read_sql("SELECT * FROM clientes", conn)
            if not clis_doc.empty:
                c_doc = st.selectbox("Seleccionar Cliente para Documentos", clis_doc['id'].tolist(), format_func=lambda x: clis_doc[clis_doc['id']==x]['nombre'].values[0])
                
                # Datos del cliente seleccionado
                cli_data = clis_doc[clis_doc['id'] == c_doc].iloc[0]
                casos_data = pd.read_sql(f"SELECT * FROM casos WHERE cliente_id = {c_doc}", conn).values.tolist()
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📄 Crear Contrato PDF"):
                        pdf_out = generar_contrato_pdf(cli_data, casos_data)
                        st.download_button("⬇️ Descargar Contrato", pdf_out, f"Contrato_{cli_data['nombre']}.pdf")
                
                with col2:
                    if st.button("📊 Exportar Excel"):
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            pd.read_sql("SELECT * FROM clientes", conn).to_excel(writer, sheet_name='Clientes')
                            pd.read_sql("SELECT * FROM casos", conn).to_excel(writer, sheet_name='Casos')
                            pd.read_sql("SELECT * FROM pagos", conn).to_excel(writer, sheet_name='Pagos')
                        st.download_button("⬇️ Descargar Reporte Completo", output.getvalue(), "Reporte_Estudio.xlsx")

    else:
        st.warning("⚠️ Por favor, ingrese sus credenciales en la barra lateral.")

if __name__ == '__main__':
    main()
