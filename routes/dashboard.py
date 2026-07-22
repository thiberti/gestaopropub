from flask import Blueprint, render_template, session
from datetime import datetime

from firebase import db
from utils.auth import login_required

from config import VERSAO_ATUAL, NOTAS_VERSAO

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

print("Dashboard carregado!")

@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    from datetime import timedelta

    hoje = datetime.now()
    hoje_mmdd = hoje.strftime("%m-%d")

    # Aniversariantes: próximos 30 dias
    clientes_raw = [{"id": c.id, **c.to_dict()} for c in db.collection("clientes").where("status", "==", "ativo").stream()]
    aniversariantes = []
    for c in clientes_raw:
        nasc = c.get("data_nascimento", "")
        if not nasc:
            continue
        try:
            nasc_dt = datetime.strptime(nasc, "%Y-%m-%d")
            # Aniversário deste ano
            aniv_ano = nasc_dt.replace(year=hoje.year)
            if aniv_ano < hoje.replace(hour=0, minute=0, second=0, microsecond=0):
                aniv_ano = aniv_ano.replace(year=hoje.year + 1)
            diff = (aniv_ano - hoje.replace(hour=0, minute=0, second=0, microsecond=0)).days
            if 0 <= diff <= 30:
                aniversariantes.append({
                    "nome": c["nome"],
                    "telefone": c.get("telefone", ""),
                    "data_nascimento": nasc,
                    "dias_para_aniversario": diff,
                    "data_formatada": nasc_dt.strftime("%d/%m"),
                })
        except Exception:
            continue
    aniversariantes.sort(key=lambda x: x["dias_para_aniversario"])

    # Ranking de produtos vendidos
    vendas_docs = [v.to_dict() for v in db.collection("vendas").where("status", "!=", "cancelado").stream()]
    ranking_qtd = {}
    ranking_valor = {}
    from datetime import date
    hoje_date = date.today()
    for v in vendas_docs:
        data_emissao = v.get("data_emissao", "")
        itens = v.get("itens", [])
        for item in itens:
            nome = item.get("nome", "Desconhecido")
            qtd = int(item.get("quantidade", 0))
            preco = float(item.get("preco", 0))
            desc = float(item.get("desconto", 0))
            val = qtd * preco * (1 - desc / 100)
            ranking_qtd[nome] = ranking_qtd.get(nome, 0) + qtd
            ranking_valor[nome] = ranking_valor.get(nome, 0) + val

    ranking = [
        {"nome": k, "quantidade": ranking_qtd[k], "valor": round(ranking_valor.get(k, 0), 2)}
        for k in ranking_qtd
    ]
    ranking.sort(key=lambda x: x["quantidade"], reverse=True)

    # Post-its: lidos do Firestore (coleção "postits")
    postits = [{"id": p.id, **p.to_dict()} for p in db.collection("postits").order_by("ordem").stream()]

    # Mensagem de aniversário configurada nos parâmetros
    config_doc = db.collection("config").document("sistema").get()
    config = config_doc.to_dict() if config_doc.exists else {}
    msg_aniversario = config.get("msg_aniversario", "Olá {nome}! 🎂 Feliz aniversário! Que seu dia seja especial! 🎉")

    # Notas de atualização — exibir pop-up se o usuário ainda não viu esta versão
    versao_atual = VERSAO_ATUAL
    user_doc = db.collection("usuarios").document(session["user_id"]).get()
    versao_vista = (user_doc.to_dict() or {}).get("versao_vista", "")
    mostrar_novidades = versao_vista != versao_atual
    notas = NOTAS_VERSAO.get(versao_atual, {})

    return render_template(
        "dashboard.html",
        aniversariantes=aniversariantes,
        ranking=ranking,
        postits=postits,
        msg_aniversario=msg_aniversario,
        versao_atual=versao_atual,
        mostrar_novidades=mostrar_novidades,
        notas=notas,
    )