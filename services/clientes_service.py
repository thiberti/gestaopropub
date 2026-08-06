from datetime import datetime
from firebase import db
from utils.empresa import colecao_empresa  # 🔹 NOVO - importa o helper


def listar_clientes():
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    return [
        {"id": c.id, **c.to_dict()}
        for c in colecao_empresa("clientes").order_by("nome").stream()
    ]


def adicionar_cliente(form):
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    colecao_empresa("clientes").add(
        {
            "nome": form["nome"],
            "telefone": form["telefone"],
            "data_nascimento": form.get("data_nascimento", ""),
            "status": "ativo",
            "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
        }
    )


def atualizar_cliente(id, form):
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    colecao_empresa("clientes").document(id).update(
        {
            "nome": form["nome"],
            "telefone": form["telefone"],
            "data_nascimento": form.get("data_nascimento", ""),
        }
    )


def alterar_status_cliente(id):
    # 🔹 MODIFICADO: usa a subcoleção dentro da empresa
    ref = colecao_empresa("clientes").document(id)
    cliente = ref.get().to_dict()

    ref.update(
        {
            "status": (
                "inativo"
                if cliente.get("status") == "ativo"
                else "ativo"
            )
        }
    )