from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from utils.empresa import colecao_empresa  # 🔹 NOVO

from firebase import db
from utils.auth import login_required

financeiro_bp = Blueprint(
    "financeiro",
    __name__
)

@financeiro_bp.route("/financeiro", methods=["GET", "POST"])
@login_required
def financeiro():
    if request.method == "POST":
        colecao_empresa("financeiro").add({
            {
                "descricao": request.form["descricao"],
                "valor": float(request.form["valor"]),
                "tipo": request.form["tipo"],
                "data_vencimento": request.form["data_vencimento"],
                "status": "pendente",
                "id_venda": None,
            }
        )
        return redirect(url_for("financeiro.financeiro"))

    hoje = datetime.now().strftime("%Y-%m-%d")
    lans = []
    for l in colecao_empresa("financeiro").stream():
        d = l.to_dict()
        d["id"] = l.id
        if (
            d.get("status") == "pendente"
            and d.get("data_vencimento")
            and d.get("data_vencimento") < hoje
        ):
            d["status"] = "vencido"
        lans.append(d)

    te = sum(
        [l["valor"] for l in lans if l["tipo"] == "entrada" and l["status"] == "pago"]
    )
    ts = sum(
        [l["valor"] for l in lans if l["tipo"] == "saida" and l["status"] == "pago"]
    )
    return render_template(
        "financeiro.html",
        lancamentos=lans,
        total_entradas=te,
        total_saidas=ts,
        saldo=te - ts,
    )

@financeiro_bp.route("/pagar_financeiro/<id>")
@login_required
def pagar_financeiro(id):
    colecao_empresa("financeiro").document(id).update({"status": "pago"})
    return redirect(url_for("financeiro.financeiro"))


@financeiro_bp.route("/editar_financeiro/<id>", methods=["POST"])
@login_required
def editar_financeiro(id):
    colecao_empresa("financeiro").document(id).update(
        {
            "descricao": request.form["descricao"],
            "valor": float(request.form["valor"]),
            "tipo": request.form["tipo"],
            "data_vencimento": request.form["data_vencimento"],
        }
    )
    return redirect(url_for("financeiro.financeiro"))


@financeiro_bp.route("/cancelar_financeiro/<id>")
@login_required
def cancelar_financeiro(id):
    colecao_empresa("financeiro").document(id).update({"status": "cancelado"})
    return redirect(url_for("financeiro.financeiro"))