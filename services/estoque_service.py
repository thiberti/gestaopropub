from firebase import db
from utils.empresa import colecao_empresa  # 🔹 NOVO


def listar_produtos():
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    return [{"id": p.id, **p.to_dict()} for p in colecao_empresa("produtos").stream()]


def listar_marcas():
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    return [
        {"id": m.id, **m.to_dict()}
        for m in colecao_empresa("marcas").order_by("nome").stream()
    ]


def adicionar_produto(form):
    # 🔹 NOVO: verifica se já existe produto com mesmo SKU
    sku_existente = (
        colecao_empresa("produtos")
        .where("sku", "==", form["sku"])
        .stream()
    )
    
    # 🔹 NOVO: verifica se já existe produto com mesmo nome
    nome_existente = (
        colecao_empresa("produtos")
        .where("nome", "==", form["nome"])
        .stream()
    )
    
    # 🔹 NOVO: se encontrar algum, retorna erro
    if any(sku_existente):
        raise ValueError(f"Já existe um produto com o SKU '{form['sku']}'")
    
    if any(nome_existente):
        raise ValueError(f"Já existe um produto com o nome '{form['nome']}'")
    
    # 🔹 Se passou nas verificações, adiciona
    colecao_empresa("produtos").add(
        {
            "nome": form["nome"],
            "marca": form["marca"],
            "linha": form.get("linha", ""),
            "sku": form["sku"],
            "preco": float(form["preco"]),
            "quantidade": int(form["quantidade"]),
            "status": "ativo",
        }
    )


def atualizar_produto(id, form):
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    colecao_empresa("produtos").document(id).update(
        {
            "nome": form["nome"],
            "marca": form["marca"],
            "linha": form.get("linha", ""),
            "sku": form["sku"],
            "preco": float(form["preco"]),
            "quantidade": int(form["quantidade"]),
        }
    )


def alterar_status_produto(id):
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    ref = colecao_empresa("produtos").document(id)
    produto = ref.get().to_dict()

    ref.update(
        {
            "status": (
                "inativo"
                if produto.get("status") == "ativo"
                else "ativo"
            )
        }
    )