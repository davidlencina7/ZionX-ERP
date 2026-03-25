import requests

BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = BASE_URL + "/auth/login"
DASHBOARD_URL = BASE_URL + "/"

session = requests.Session()

# Credenciales de test
payload = {
    "username": "ilencina",
    "password": "ilencina123"
}

try:
    # 1. Obtener el token CSRF si existe (opcional, depende de la implementación)
    login_page = session.get(LOGIN_URL)
    if "csrf_token" in login_page.text:
        import re
        match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if match:
            payload["csrf_token"] = match.group(1)

    # 2. Hacer login
    response = session.post(LOGIN_URL, data=payload, allow_redirects=True)
    print(f"Login status code: {response.status_code}")
    if "logout" in response.text.lower() or "dashboard" in response.text.lower():
        print("Login exitoso. Accediendo al dashboard...")
        dashboard = session.get(DASHBOARD_URL)
        print(f"Dashboard status code: {dashboard.status_code}")
        print("\n--- Contenido dashboard ---\n")
        print(dashboard.text[:2000])
    else:
        print("No se pudo iniciar sesión. Revisa las credenciales o el formulario de login.")
        print(response.text[:1000])
except Exception as e:
    print(f"Error al conectar con el dashboard: {e}")
