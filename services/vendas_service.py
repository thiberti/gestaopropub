import json
from datetime import datetime

from flask import render_template, request, redirect, url_for
from firebase import db
from utils.empresa import colecao_empresa, empresa_id  # 🔹 Adicionado empresa_id


def gerar_proximo_pedido():
    # 🔹 MODIFICADO: contador isolado por empresa
    ref_meta = colecao_empresa("config").document("vendas")
    meta = ref_meta.get()
    novo_n = (meta.to_dict().get("ultimo", 0) + 1) if meta.exists else 1
    ref_meta.set({"ultimo": novo_n})
    return novo_n


def criar_venda(form):
    from utils.empresa import empresa_id, colecao_empresa
    empresa = empresa_id()
    print(f"🔍 empresa_id: {empresa}")
    
    # 🔹 TESTE DIRETO - salva um documento de teste
    try:
        teste_ref = colecao_empresa("teste").add({"teste": "funcionou", "data": datetime.now().isoformat()})
        print(f"✅ Teste de escrita no Firestore funcionou! ID: {teste_ref[1].id}")
    except Exception as e:
        print(f"❌ Teste de escrita FALHOU: {e}")
        raise
    
    print(f"🔍 empresa_id: {empresa_id()}")  # Log 1
    
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
    print(f"📦 Salvando venda com dados: {dados}")  # Log 2
    
    # 🔹 Tenta salvar e captura erro (APENAS UMA VEZ!)
    try:
        colecao_empresa("vendas").add(dados)  # ← ÚNICA chamada
        print("✅ Venda salva com sucesso!")  # Log 3
    except Exception as e:
        print(f"❌ ERRO ao salvar: {e}")  # Log 4
        raise
    
    # 🔹 Dedução do estoque usando subcoleção da empresa
    for item in itens:
        ref_p = colecao_empresa("produtos").document(item["id"])
        doc_p = ref_p.get()
        if doc_p.exists:
            ref_p.update(
                {
                    "quantidade": doc_p.to_dict().get("quantidade", 0)
                    - int(item["quantidade"])
                }
            )