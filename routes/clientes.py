from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

from firebase import db
from utils.auth import login_required

clientes_bp = Blueprint(
    "clientes",
    __name__
)

@clientes_bp.route("/clientes", methods=["GET", "POST"])
@login_required
def clientes():
    if request.method == "POST":
        db.collection("clientes").add(
            {
                "nome": request.form["nome"],
                "telefone": request.form["telefone"],
                "data_nascimento": request.form.get("data_nascimento", ""),
                "status": "ativo",
                "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        return redirect(url_for("clientes.clientes"))
    clis = [
        {"id": c.id, **c.to_dict()}
        for c in db.collection("clientes").order_by("nome").stream()
    ]
    return render_template("clientes.html", clientes=clis)


@clientes_bp.route("/editar_cliente/<id>", methods=["POST"])
@login_required
def editar_cliente(id):
    db.collection("clientes").document(id).update(
        {
            "nome": request.form["nome"],
            "telefone": request.form["telefone"],
            "data_nascimento": request.form.get("data_nascimento", ""),
        }
    )
    return redirect(url_for("clientes.clientes"))


@clientes_bp.route("/toggle_cliente/<id>")
@login_required
def toggle_cliente(id):
    ref = db.collection("clientes").document(id)
    c = ref.get().to_dict()
    ref.update({"status": "inativo" if c.get("status") == "ativo" else "ativo"})
    return redirect(url_for("clientes.clientes"))