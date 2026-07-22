from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_session import Session
from firebase import db
from routes.dashboard import dashboard_bp
from routes.clientes import clientes_bp
from routes.estoque import estoque_bp
from utils.auth import login_required
from routes.auth import auth_bp
from routes.parametros import parametros_bp
from routes.vendas import vendas_bp
from routes.financeiro import financeiro_bp
from utils.filters import formato_br

app = Flask(__name__)
app.secret_key = "gestaoerp-demo-2026"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(estoque_bp)
app.register_blueprint(parametros_bp)
app.register_blueprint(vendas_bp)
app.register_blueprint(financeiro_bp)
app.template_filter("formato_br")(formato_br)

if __name__ == "__main__":
    import os

    # O Render define a porta automaticamente, se não houver, usa 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)