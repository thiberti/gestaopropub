from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

from firebase import db
from utils.auth import login_required

clientes_bp = Blueprint(
    "clientes",
    __name__
)

from services.clientes_service import (
    listar_clientes,
    adicionar_cliente,
    atualizar_cliente,
    alterar_status_cliente,
)

@clientes_bp.route("/clientes", methods=["GET", "POST"])
@login_required
def clientes():

    if request.method == "POST":
        adicionar_cliente(request.form)
        return redirect(url_for("clientes.clientes"))

    clis = listar_clientes()

    return render_template(
        "clientes.html",
        clientes=clis
    )


@clientes_bp.route("/editar_cliente/<id>", methods=["POST"])
@login_required
def editar_cliente(id):

    atualizar_cliente(id, request.form)

    return redirect(url_for("clientes.clientes"))


@clientes_bp.route("/toggle_cliente/<id>")
@login_required
def toggle_cliente(id):

    alterar_status_cliente(id)

    return redirect(url_for("clientes.clientes"))