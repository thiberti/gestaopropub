from flask import Blueprint, render_template, request, redirect, url_for
from utils.auth import login_required

from services.estoque_service import (
    listar_produtos,
    listar_marcas,
    adicionar_produto,
    atualizar_produto,
    alterar_status_produto,
)

estoque_bp = Blueprint("estoque", __name__)


@estoque_bp.route("/estoque", methods=["GET", "POST"])
@login_required
def estoque():
    if request.method == "POST":
        adicionar_produto(request.form)
        return redirect(url_for("estoque.estoque"))

    return render_template(
        "estoque.html",
        produtos=listar_produtos(),
        marcas=listar_marcas(),
    )


@estoque_bp.route("/editar_produto/<id>", methods=["POST"])
@login_required
def editar_produto(id):
    atualizar_produto(id, request.form)
    return redirect(url_for("estoque.estoque"))


@estoque_bp.route("/toggle_estoque/<id>")
@login_required
def toggle_estoque(id):
    alterar_status_produto(id)
    return redirect(url_for("estoque.estoque"))