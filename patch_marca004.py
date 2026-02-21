# patch_marca004.py
# Uso: python patch_marca004.py app.py
# Genera: app_PATCHED.py (archivo final listo para reemplazar)

import re
import sys

LOGIN_FUNC = r'''def login_ui():
    brand_header()
    st.subheader("Ingreso al Sistema")

    # Limpia SOLO la primera vez que se muestra el login en esta sesión
    if "login_cleared" not in st.session_state:
        st.session_state["login_cleared"] = True
        st.session_state["login_user"] = ""
        st.session_state["login_pass"] = ""

    u = st.text_input(
        "Acceso",
        key="login_user",
        placeholder="Escribe tu usuario",
        autocomplete="off"
    )
    p = st.text_input(
        "Clave de acceso",
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
'''

def replace_block(text, start_pat, end_pat, new_block):
    """Reemplaza desde la primera coincidencia start_pat hasta antes de la primera coincidencia end_pat posterior."""
    m1 = re.search(start_pat, text, flags=re.MULTILINE)
    if not m1:
        return text, False
    start = m1.start()
    m2 = re.search(end_pat, text[m1.end():], flags=re.MULTILINE)
    if not m2:
        return text, False
    end = m1.end() + m2.start()
    return text[:start] + new_block + "\n\n" + text[end:], True

def replace_top_level_function(text, func_name, new_func_src):
    """Reemplaza una función top-level completa por nombre."""
    # Encuentra 'def func_name(' al inicio de línea y reemplaza hasta el siguiente top-level 'def ' o 'if ' o fin.
    pat = rf'^(def\s+{re.escape(func_name)}\s*\(.*\):\s*\n)'
    m = re.search(pat, text, flags=re.MULTILINE)
    if not m:
        return text, False
    start = m.start()
    # desde el final del def, buscar siguiente bloque top-level
    rest = text[m.end():]
    m2 = re.search(r'^\S', rest, flags=re.MULTILINE)  # siguiente línea sin indent
    if not m2:
        end = len(text)
    else:
        end = m.end() + m2.start()
    return text[:start] + new_func_src + "\n\n" + text[end:], True

def ensure_import(text, module_line):
    if module_line in text:
        return text
    # Insertar después de los imports iniciales
    lines = text.splitlines()
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.startswith("import ") or ln.startswith("from "):
            insert_at = i + 1
        else:
            if insert_at > 0:
                break
    lines.insert(insert_at, module_line)
    return "\n".join(lines) + "\n"

def main():
    if len(sys.argv) < 2:
        print("Uso: python patch_marca004.py app.py")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # 0) Arreglar escapes HTML si vinieron pegados así
    text = (text.replace("&gt;", ">")
                .replace("&lt;", "<")
                .replace("&amp;", "&")
                .replace("-&gt;", "->"))

    # 1) Asegurar import json (por borradores / secrets)
    text = ensure_import(text, "import json")

    # 2) Reemplazar LOGIN completo (evita autofill desde estado)
    text, ok_login = replace_top_level_function(text, "login_ui", LOGIN_FUNC)

    # 3) Reemplazar CONTROL_PASSWORD hardcode por secrets + variables necesarias
    #    Busca la línea CONTROL_PASSWORD = "control123" y la sustituye por 3 líneas.
    text = re.sub(
        r'^\s*CONTROL_PASSWORD\s*=\s*["\'].*?["\']\s*(#.*)?$',
        'CONTROL_PASSWORD = st.secrets.get("CONTROL_PASSWORD", "control123")  # panel de control (fallback local)\n'
        'ADMIN_BOOTSTRAP_PASSWORD = st.secrets.get("ADMIN_BOOTSTRAP_PASSWORD", "estudio123")  # admin inicial (fallback)\n'
        'PASSWORD_PEPPER = st.secrets.get("PASSWORD_PEPPER", "")  # opcional (mejora hash)',
        text,
        flags=re.MULTILINE
    )

    # 4) Reemplazar sha256() por versión con pepper
    #    Sustituye el bloque de función sha256 existente.
    sha_pat = r'^def\s+sha256\s*\(.*?\):\s*\n(?:[ \t].*\n)+'
    sha_new = (
        'def sha256(text: str) -> str:\n'
        '    base = (PASSWORD_PEPPER or "") + str(text)\n'
        '    return hashlib.sha256(base.encode("utf-8")).hexdigest()\n'
    )
    text, ok_sha = replace_block(text, r'^def\s+sha256\s*\(.*?\):', r'^\s*(def|#|for|if|class)\b', sha_new)

    # Si el bloque anterior no encontró fin bien, intenta reemplazo simple por regex.
    if not ok_sha:
        text = re.sub(sha_pat, sha_new, text, flags=re.MULTILINE)

    # 5) Cambiar admin bootstrap (sha256("estudio123") -> sha256(ADMIN_BOOTSTRAP_PASSWORD))
    text = text.replace('sha256("estudio123")', 'sha256(ADMIN_BOOTSTRAP_PASSWORD)')

    # 6) Cambiar mensaje de reset total que revela credencial
    text = text.replace('st.success("✅ Reset total aplicado. admin/estudio123")',
                        'st.success("✅ Reset total aplicado. Usuario: admin. Contraseña: la configurada en Secrets.")')

    # 7) Asegurar comas en diccionarios típicos (por si faltan)
    #    Este fix es conservador: solo agrega coma si la línea termina exactamente ahí.
    text = re.sub(r'("PasswordHash"\s*:\s*sha256\(ADMIN_BOOTSTRAP_PASSWORD\))\s*\n', r'\1,\n', text)

    out = "app_PATCHED.py"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)

    print("✅ Generado:", out)
    print("👉 Ahora reemplaza app.py por app_PATCHED.py y haz commit.")

if __name__ == "__main__":
    main()
