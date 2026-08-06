from flask import session

def empresa_id():
    """Retorna o ID da empresa do usuário logado."""
    return session.get("empresa_id")

def empresa_ref():
    """Retorna a referência da empresa no Firestore."""
    from firebase import db
    return db.collection("empresas").document(empresa_id())

def colecao_empresa(nome_colecao):
    """
    Retorna uma referência para uma subcoleção dentro da empresa.
    Exemplo: colecao_empresa("clientes") -> empresas/empresa_demo/clientes
    """
    from firebase import db
    return db.collection("empresas").document(empresa_id()).collection(nome_colecao)