from backend.core.app_factory import create_app

if __name__ == "__main__":
    app = create_app("development")
    app.run(debug=True, host="127.0.0.1", port=5000)
