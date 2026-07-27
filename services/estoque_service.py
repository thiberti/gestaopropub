from firebase import db


def listar_produtos():
    return [{"id": p.id, **p.to_dict()} for p in db.collection("produtos").stream()]


def listar_marcas():
    return [
        {"id": m.id, **m.to_dict()}
        for m in db.collection("marcas").order_by("nome").stream()
    ]


def adicionar_produto(form):
    db.collection("produtos").add(
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
    db.collection("produtos").document(id).update(
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
    ref = db.collection("produtos").document(id)
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