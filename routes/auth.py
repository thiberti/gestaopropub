from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

from firebase import db

auth_bp = Blueprint(
    "auth",
    __name__
)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_digitado = request.form.get("username").strip()
        senha_digitada = request.form.get("password")
        user_doc = db.collection("usuarios").document(usuario_digitado).get()
        if user_doc.exists:
            dados_usuario = user_doc.to_dict()
            if check_password_hash(dados_usuario["password"], senha_digitada):
                session["user_id"] = usuario_digitado
                session["empresa_id"] = dados_usuario.get("empresa_id", "empresa_demo")
                return redirect(url_for("dashboard.dashboard"))
        flash("Usuário ou senha incorretos.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))