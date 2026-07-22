from flask import Blueprint, render_template, request, redirect, url_for

from firebase import db
from utils.auth import login_required

estoque_bp = Blueprint(
    "estoque",
    __name__
)

@estoque_bp.route("/estoque", methods=["GET", "POST"])
@login_required
def estoque():
    if request.method == "POST":
        db.collection("produtos").add(
            {
                "nome": request.form["nome"],
                "marca": request.form["marca"],
                "linha": request.form.get("linha", ""),
                "sku": request.form["sku"],
                "preco": float(request.form["preco"]),
                "quantidade": int(request.form["quantidade"]),
                "status": "ativo",
            }
        )
        return redirect(url_for("estoque.estoque"))
    prods = [{"id": p.id, **p.to_dict()} for p in db.collection("produtos").stream()]
    marcas = [{"id": m.id, **m.to_dict()} for m in db.collection("marcas").order_by("nome").stream()]
    return render_template("estoque.html", produtos=prods, marcas=marcas)


@estoque_bp.route("/editar_produto/<id>", methods=["POST"])
@login_required
def editar_produto(id):
    db.collection("produtos").document(id).update(
        {
            "nome": request.form["nome"],
            "marca": request.form["marca"],
            "linha": request.form.get("linha", ""),
            "sku": request.form["sku"],
            "preco": float(request.form["preco"]),
            "quantidade": int(request.form["quantidade"]),
        }
    )
    return redirect(url_for("estoque.estoque"))


@estoque_bp.route("/toggle_estoque/<id>")
@login_required
def toggle_estoque(id):
    ref = db.collection("produtos").document(id)
    p = ref.get().to_dict()
    ref.update({"status": "inativo" if p.get("status") == "ativo" else "ativo"})
    return redirect(url_for("estoque.estoque"))