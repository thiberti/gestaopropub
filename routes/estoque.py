from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify  # 🔹 Adicionado jsonify
from utils.auth import login_required
from utils.empresa import colecao_empresa  # 🔹 Adicionado

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
        try:
            adicionar_produto(request.form)
            flash("✅ Produto adicionado com sucesso!", "success")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for("estoque.estoque"))

    return render_template(
        "estoque.html",
        produtos=listar_produtos(),
        marcas=listar_marcas(),
    )


@estoque_bp.route("/editar_produto/<id>", methods=["POST"])
@login_required
def editar_produto(id):
    try:
        atualizar_produto(id, request.form)
        flash("✅ Produto atualizado com sucesso!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("estoque.estoque"))


@estoque_bp.route("/toggle_estoque/<id>")
@login_required
def toggle_estoque(id):
    alterar_status_produto(id)
    flash("✅ Status do produto alterado!", "success")
    return redirect(url_for("estoque.estoque"))


# 🔹 NOVO: API para verificar produto duplicado
@estoque_bp.route("/api/verificar_produto", methods=["GET"])
@login_required
def verificar_produto():
    nome = request.args.get("nome", "").strip()
    sku = request.args.get("sku", "").strip()
    
    if not nome and not sku:
        return jsonify({"status": "erro", "mensagem": "Nome ou SKU obrigatório"}), 400
    
    # Busca por nome exato OU SKU
    resultados = []
    if nome:
        query_nome = colecao_empresa("produtos").where("nome", "==", nome)
        resultados.extend(list(query_nome.stream()))
    
    if sku:
        query_sku = colecao_empresa("produtos").where("sku", "==", sku)
        resultados.extend(list(query_sku.stream()))
    
    # Remove duplicatas pelo ID
    ids_vistos = set()
    unicos = []
    for doc in resultados:
        if doc.id not in ids_vistos:
            ids_vistos.add(doc.id)
            unicos.append(doc)
    
    if unicos:
        doc = unicos[0].to_dict()
        doc["id"] = unicos[0].id
        doc["status"] = "identico"
        return jsonify(doc)
    else:
        return jsonify({"status": "disponivel", "mensagem": "Produto disponível para cadastro"})


# 🔹 NOVO: API para somar quantidade ao estoque existente
@estoque_bp.route("/estoque/somar_quantidade/<id>", methods=["POST"])
@login_required
def somar_quantidade(id):
    data = request.get_json()
    quantidade_adicional = int(data.get("quantidade", 1))
    
    ref = colecao_empresa("produtos").document(id)
    produto = ref.get().to_dict()
    
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    
    nova_quantidade = produto.get("quantidade", 0) + quantidade_adicional
    ref.update({"quantidade": nova_quantidade})
    
    flash(f"✅ Adicionado {quantidade_adicional} unidade(s) ao estoque. Novo saldo: {nova_quantidade}", "success")
    return jsonify({"sucesso": True, "nova_quantidade": nova_quantidade})