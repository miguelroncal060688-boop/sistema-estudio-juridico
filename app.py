import re

APP_CORE = "app_core.py"

def patch_source(src: str) -> str:
    # ------------------------------------------------------------
    # A) Garantizar que exista import json (por si luego lo usas)
    # ------------------------------------------------------------
    if "import json" not in src:
        src = src.replace("import shutil", "import shutil\nimport json")

    # ------------------------------------------------------------
    # B) Panel de control: CONTROL_PASSWORD desde Secrets
    # Reemplaza cualquier línea CONTROL_PASSWORD = "..."
    # ------------------------------------------------------------
    src = re.sub(
        r'^\s*CONTROL_PASSWORD\s*=\s*["\'].*?["\']\s*(#.*)?$',
        'CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")  # clave panel de control (fallback local)',
        src,
        flags=re.MULTILINE
    )

    # ------------------------------------------------------------
    # C) Definir ADMIN_BOOTSTRAP_PASSWORD y PASSWORD_PEPPER desde Secrets
    # (si no existen ya en el core)
    # ------------------------------------------------------------
    if "ADMIN_BOOTSTRAP_PASSWORD" not in src:
        src = src.replace(
            'CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")  # clave panel de control (fallback local)',
            'CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")  # clave panel de control (fallback local)\n'
            'ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")  # admin inicial (fallback local)\n'
            'PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")  # pepper opcional'
        )
    else:
        # si ya existe admin bootstrap pero no pepper
        if "PASSWORD_PEPPER" not in src:
            src = src.replace(
                'ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")',
                'ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")\n'
                'PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")  # pepper opcional'
            )

    # ------------------------------------------------------------
    # D) Parche sha256: usar pepper
    # Reemplaza la función sha256 completa si existe
    # ------------------------------------------------------------
    sha_new = (
        'def sha256(text: str) -> str:\n'
        '    base = (PASSWORD_PEPPER or "") + str(text)\n'
        '    return hashlib.sha256(base.encode("utf-8")).hexdigest()\n'
    )

    # reemplazo de bloque de función sha256 (top-level)
    src = re.sub(
        r'(?ms)^def\s+sha256\s*\(.*?\)\s*->\s*str\s*:\s*\n(.*?)(?=^\S)',
        sha_new + "\n",
        src
    )
    # por si estaba sin anotación -> str:
    src = re.sub(
        r'(?ms)^def\s+sha256\s*\(.*?\)\s*:\s*\n(.*?)(?=^\S)',
        sha_new + "\n",
        src
    )

    # ------------------------------------------------------------
    # E) Quitar autorrelleno DESDE CÓDIGO (no del navegador)
    # ------------------------------------------------------------
    src = src.replace('value="admin"', 'value=""')
    src = src.replace("value='admin'", "value=''")
    src = src.replace('value="estudio123"', 'value=""')
    src = src.replace("value='estudio123'", "value=''")

    # ------------------------------------------------------------
    # F) Admin bootstrap: sha256("estudio123") -> sha256(ADMIN_BOOTSTRAP_PASSWORD)
    # (sirve para creación inicial y reset_total)
    # ------------------------------------------------------------
    src = src.replace('sha256("estudio123")', 'sha256(ADMIN_BOOTSTRAP_PASSWORD)')
    src = src.replace("sha256('estudio123')", "sha256(ADMIN_BOOTSTRAP_PASSWORD)")

    # ------------------------------------------------------------
    # G) Mensaje que revela credenciales (solo texto)
    # ------------------------------------------------------------
    src = src.replace(
        'st.success("✅ Reset total aplicado. admin/estudio123")',
        'st.success("✅ Reset total aplicado. Usuario: admin. Contraseña: la configurada en Secrets.")'
    )

    # ------------------------------------------------------------
    # H) Reemplazar COMPLETA la función login_ui por versión anti-estado/autofill
    # (esto NO rompe indentación del resto)
    # ------------------------------------------------------------
    login_new = r'''
def login_ui():
    brand_header()
    st.subheader("Ingreso al Sistema")

    # Limpia SOLO la primera vez que se muestra el login en esta sesión
    if "login_cleared" not in st.session_state:
        st.session_state["login_cleared"] = True
        st.session_state["login_user"] = ""
        st.session_state["login_pass"] = ""

    u = st.text_input(
        "Acceso",
        value="",
        key="login_user",
        placeholder="Escribe tu usuario",
        autocomplete="off"
    )
    p = st.text_input(
        "Clave de acceso",
        value="",
        key="login_pass",
        type="password",
        placeholder="Escribe tu contraseña",
        autocomplete="off"
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

        # permitir que se limpie de nuevo cuando vuelvas al login (logout)
        st.session_state.pop("login_cleared", None)
        st.session_state["login_pass"] = ""
        st.rerun()
'''.lstrip("\n")

    src = re.sub(
        r'(?ms)^def\s+login_ui\s*\(\)\s*:\s*\n(.*?)(?=^\S)',
        login_new + "\n",
        src
    )

    return src


def main():
    with open(APP_CORE, "r", encoding="utf-8") as f:
        original = f.read()

    # si el core venía pegado con escapes HTML, los arreglamos por si acaso
    original = (original.replace("&gt;", ">")
                        .replace("&lt;", "<")
                        .replace("&amp;", "&")
                        .replace("-&gt;", "->"))

    patched = patch_source(original)

    code = compile(patched, APP_CORE, "exec")
    globals_dict = {"__name__": "__main__", "__file__": APP_CORE}
    exec(code, globals_dict)

main()
