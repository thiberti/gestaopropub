from flask import Blueprint, render_template, request, redirect, url_for, flash  # 🔹 Adicionado flash
from datetime import datetime, timedelta
import json

from firebase import db
from utils.auth import login_required
from utils.empresa import colecao_empresa  # 🔹 NOVO

from services.vendas_service import (
    gerar_proximo_pedido,
    criar_venda,
)

vendas_bp = Blueprint(
    "vendas",
    __name__
)

@vendas_bp.route("/vendas", methods=["GET", "POST"])
@login_required
def vendas():
    if request.method == "POST":
        try:
            criar_venda(request.form)
            flash("✅ Venda criada com sucesso!", "success")
        except Exception as e:
            flash(f"❌ Erro ao criar venda: {str(e)}", "danger")
        return redirect(url_for("vendas.vendas"))

    hoje = datetime.now().strftime("%Y-%m-%d")
    vendas_list = []
    # 🔹 MODIFICADO: usa subcoleção da empresa
    for v in (
        colecao_empresa("vendas")
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

    # 🔹 MODIFICADO: produtos e clientes isolados por empresa
    prods = [
        {"id": p.id, **p.to_dict()}
        for p in colecao_empresa("produtos").where("status", "==", "ativo").stream()
    ]
    clis_raw = [
        {"id": c.id, "nome": c.to_dict()["nome"]}
        for c in colecao_empresa("clientes").where("status", "==", "ativo").stream()
    ]
    clis = sorted(clis_raw, key=lambda x: x["nome"])
    return render_template(
        "vendas.html", vendas=vendas_list, produtos=prods, clientes=clis
    )


@vendas_bp.route("/editar_venda/<id>", methods=["POST"])
@login_required
def editar_venda(id):
    try:
        colecao_empresa("vendas").document(id).update(
            {
                "cliente": request.form.get("cliente"),
                "data_emissao": request.form.get("data_emissao"),
                "vencimento": request.form.get("data_vencimento"),
                "parcelas": int(request.form.get("parcelas", 1) or 1),
                "total_geral": float(request.form.get("total_geral_input", 0) or 0),
                "itens": json.loads(request.form.get("itens_venda")),
            }
        )
        flash("✅ Venda atualizada com sucesso!", "success")
    except Exception as e:
        flash(f"❌ Erro ao atualizar venda: {str(e)}", "danger")
    return redirect(url_for("vendas.vendas"))


@vendas_bp.route("/pagar_venda/<id>")
@login_required
def pagar_venda(id):
    from datetime import timedelta
    # 🔹 MODIFICADO: usa subcoleção da empresa
    ref = colecao_empresa("vendas").document(id)
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
            # 🔹 MODIFICADO: lançamentos financeiros isolados por empresa
            colecao_empresa("financeiro").add(
                {
                    "descricao": f"Pedido #{v['numero_pedido']} - {v['cliente']}" + (f" ({i+1}/{parcelas})" if parcelas > 1 else ""),
                    "valor": valor_parcela,
                    "tipo": "entrada",
                    "data_vencimento": venc.strftime("%Y-%m-%d"),
                    "status": "pago",
                    "id_venda": id,
                }
            )
        flash("✅ Venda marcada como paga e lançamentos financeiros criados!", "success")
    else:
        flash("⚠️ Esta venda já está paga.", "warning")
    return redirect(url_for("vendas.vendas"))


@vendas_bp.route("/cancelar_venda/<id>")
@login_required
def cancelar_venda(id):
    try:
        # 🔹 MODIFICADO: usa subcoleção da empresa
        colecao_empresa("vendas").document(id).update({"status": "cancelado"})
        # 🔹 MODIFICADO: atualiza lançamentos financeiros vinculados
        for d in colecao_empresa("financeiro").where("id_venda", "==", id).stream():
            colecao_empresa("financeiro").document(d.id).update({"status": "cancelado"})
        flash("✅ Venda cancelada com sucesso!", "success")
    except Exception as e:
        flash(f"❌ Erro ao cancelar venda: {str(e)}", "danger")
    return redirect(url_for("vendas.vendas"))