from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import json

from firebase import db
from utils.auth import login_required

from services.vendas_service import gerar_proximo_pedido

vendas_bp = Blueprint(
    "vendas",
    __name__
)

@vendas_bp.route("/vendas", methods=["GET", "POST"])
@login_required
def vendas():
    if request.method == "POST":
        itens = json.loads(request.form.get("itens_venda"))
        dados = {
            "numero_pedido": gerar_proximo_pedido(),
            "cliente": request.form.get("cliente"),
            "data_emissao": request.form.get("data_emissao"),
            "vencimento": request.form.get("data_vencimento"),
            "status": "aberto",
            "total_geral": float(request.form.get("total_geral_input", 0) or 0),
            "itens": itens,
            "parcelas": int(request.form.get("parcelas", 1) or 1),
            "intervalo_parcelas": int(request.form.get("intervalo_parcelas", 30) or 30),
            "forma_pagamento": request.form.get("forma_pagamento"),
            "observacao": request.form.get("observacao"),
            "desconto_total_percent": float(request.form.get("desconto_total", 0) or 0),
        }
        db.collection("vendas").add(dados)
        for item in itens:
            ref_p = db.collection("produtos").document(item["id"])
            doc_p = ref_p.get()
            if doc_p.exists:
                ref_p.update(
                    {
                        "quantidade": doc_p.to_dict().get("quantidade", 0)
                        - int(item["quantidade"])
                    }
                )
        return redirect(url_for("vendas.vendas"))

    hoje = datetime.now().strftime("%Y-%m-%d")
    vendas_list = []
    for v in (
        db.collection("vendas")
        .order_by("numero_pedido", direction="DESCENDING")
        .stream()
    ):
        d = v.to_dict()
        d["id"] = v.id
        if (
            d.get("status") == "aberto"
            and d.get("vencimento")
            and d.get("vencimento") < hoje
        ):
            d["status"] = "vencido"
        vendas_list.append(d)

    prods = [
        {"id": p.id, **p.to_dict()}
        for p in db.collection("produtos").where("status", "==", "ativo").stream()
    ]
    clis_raw = [
        {"id": c.id, "nome": c.to_dict()["nome"]}
        for c in db.collection("clientes").where("status", "==", "ativo").stream()
    ]
    clis = sorted(clis_raw, key=lambda x: x["nome"])
    return render_template(
        "vendas.html", vendas=vendas_list, produtos=prods, clientes=clis
    )

@vendas_bp.route("/editar_venda/<id>", methods=["POST"])
@login_required
def editar_venda(id):
    db.collection("vendas").document(id).update(
        {
            "cliente": request.form.get("cliente"),
            "data_emissao": request.form.get("data_emissao"),
            "vencimento": request.form.get("data_vencimento"),
            "parcelas": int(request.form.get("parcelas", 1) or 1),
            "total_geral": float(request.form.get("total_geral_input", 0) or 0),
            "itens": json.loads(request.form.get("itens_venda")),
        }
    )
    return redirect(url_for("vendas.vendas"))

@vendas_bp.route("/pagar_venda/<id>")
@login_required
def pagar_venda(id):
    from datetime import timedelta
    ref = db.collection("vendas").document(id)
    v = ref.get().to_dict()
    if v and v.get("status") != "pago":
        hoje = datetime.now().strftime("%Y-%m-%d")
        ref.update({"status": "pago", "data_pagamento": hoje})
        parcelas = int(v.get("parcelas", 1) or 1)
        total = v["total_geral"]
        valor_parcela = round(total / parcelas, 2)
        venc_base_str = v.get("vencimento") or hoje
        venc_base = datetime.strptime(venc_base_str, "%Y-%m-%d")
        intervalo = int(v.get("intervalo_parcelas", 30) or 30)
        for i in range(parcelas):
            venc = venc_base + timedelta(days=intervalo * i)
            db.collection("financeiro").add(
                {
                    "descricao": f"Pedido #{v['numero_pedido']} - {v['cliente']}" + (f" ({i+1}/{parcelas})" if parcelas > 1 else ""),
                    "valor": valor_parcela,
                    "tipo": "entrada",
                    "data_vencimento": venc.strftime("%Y-%m-%d"),
                    "status": "pago",
                    "id_venda": id,
                }
            )
    return redirect(url_for("vendas.vendas"))

@vendas_bp.route("/cancelar_venda/<id>")
@login_required
def cancelar_venda(id):
    db.collection("vendas").document(id).update({"status": "cancelado"})
    for d in db.collection("financeiro").where("id_venda", "==", id).stream():
        db.collection("financeiro").document(d.id).update({"status": "cancelado"})
    return redirect(url_for("vendas.vendas"))