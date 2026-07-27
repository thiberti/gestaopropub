import json
from datetime import datetime

from flask import render_template, request, redirect, url_for
from firebase import db

def gerar_proximo_pedido():
    ref_meta = db.collection("config").document("vendas")
    meta = ref_meta.get()
    novo_n = (meta.to_dict().get("ultimo", 0) + 1) if meta.exists else 1
    ref_meta.set({"ultimo": novo_n})
    return novo_n

def criar_venda(form):
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
