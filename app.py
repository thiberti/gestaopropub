import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_session import Session

# 1. Configuração Firebase
cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. Configuração do App e Sessão
app = Flask(__name__)
app.secret_key = "gestaoerp-demo-2026"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# ==========================================
# VERSÃO DO SISTEMA E NOTAS DE ATUALIZAÇÃO
# ==========================================
VERSAO_ATUAL = "1.2.2"

NOTAS_VERSAO = {
    "1.2.2": {
        "data": "05/07/2026",
        "titulo": "Atualização de funcionalidades",
        "novidades": [
            "📊 Novo Filtro Pesquisar por SKU adicionado a aba Estoque",
        ],
        "correcoes": [
            "✅ Correção de bug na função de verificar se já existe produto com mesmo nome ou SKU",
        ]
    },
    "1.2.1": {
        "data": "27/06/2026",
        "titulo": "Novo módulo Home",
        "novidades": [
            "🏠 Página inicial completamente reformulada com visual moderno",
            "🎂 Agenda de aniversariantes dos próximos 30 dias",
            "📝 Anotações em post-it com carrossel e múltiplas cores",
            "🏆 Ranking dos 3 produtos mais vendidos com medalhas",
            "🎉 Pop-up automático para aniversários nos próximos 3 dias",
            "📱 Botão WhatsApp direto no alerta de aniversário",
            "🏪 Cards de acesso rápido às plataformas de revenda",
        ],
        "correcoes": [
            "✅ Filtro de marca no estoque agora carrega corretamente",
            "✅ Ordenação de colunas corrigida em todas as tabelas",
            "✅ Modais de cadastro agora abrem centralizados",
        ]
    },
    "1.0.0": {
        "data": "01/01/2026",
        "titulo": "Lançamento inicial",
        "novidades": [
            "🚀 Sistema lançado com módulos de Clientes, Estoque, Vendas e Financeiro",
        ],
        "correcoes": []
    },
}


# 3. Filtro para Data Brasileira (DD/MM/AAAA)
@app.template_filter("formato_br")
def formato_br(value):
    if not value or value == "":
        return ""
    try:
        data_obj = datetime.strptime(value, "%Y-%m-%d")
        return data_obj.strftime("%d/%m/%Y")
    except:
        return value


# 4. Protetor de Páginas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# ==========================================
# ROTAS DE ACESSO
# ==========================================


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_digitado = request.form.get("username").strip()
        senha_digitada = request.form.get("password")
        user_doc = db.collection("usuarios").document(usuario_digitado).get()
        if user_doc.exists:
            if check_password_hash(user_doc.to_dict()["password"], senha_digitada):
                session["user_id"] = usuario_digitado
                return redirect(url_for("dashboard"))
        flash("Usuário ou senha incorretos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==========================================
# DASHBOARD E MÓDULOS BÁSICOS
# ==========================================


@app.route("/")
@app.route("/dashboard")
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


@app.route("/estoque", methods=["GET", "POST"])
@login_required
def estoque():
    if request.method == "POST":
        db.collection("produtos").add(
            {
                "nome": request.form["nome"],
                "marca": request.form["marca"],
                "linha": request.form.get("linha", ""),
                "sku": request.form["sku"],
                "preco": float(request.form["preco"]),
                "quantidade": int(request.form["quantidade"]),
                "status": "ativo",
            }
        )
        return redirect(url_for("estoque"))
    prods = [{"id": p.id, **p.to_dict()} for p in db.collection("produtos").stream()]
    marcas = [{"id": m.id, **m.to_dict()} for m in db.collection("marcas").order_by("nome").stream()]
    return render_template("estoque.html", produtos=prods, marcas=marcas)


@app.route("/editar_produto/<id>", methods=["POST"])
@login_required
def editar_produto(id):
    db.collection("produtos").document(id).update(
        {
            "nome": request.form["nome"],
            "marca": request.form["marca"],
            "linha": request.form.get("linha", ""),
            "sku": request.form["sku"],
            "preco": float(request.form["preco"]),
            "quantidade": int(request.form["quantidade"]),
        }
    )
    return redirect(url_for("estoque"))


@app.route("/toggle_estoque/<id>")
@login_required
def toggle_estoque(id):
    ref = db.collection("produtos").document(id)
    p = ref.get().to_dict()
    ref.update({"status": "inativo" if p.get("status") == "ativo" else "ativo"})
    return redirect(url_for("estoque"))


@app.route("/clientes", methods=["GET", "POST"])
@login_required
def clientes():
    if request.method == "POST":
        db.collection("clientes").add(
            {
                "nome": request.form["nome"],
                "telefone": request.form["telefone"],
                "data_nascimento": request.form.get("data_nascimento", ""),
                "status": "ativo",
                "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        return redirect(url_for("clientes"))
    clis = [
        {"id": c.id, **c.to_dict()}
        for c in db.collection("clientes").order_by("nome").stream()
    ]
    return render_template("clientes.html", clientes=clis)


@app.route("/editar_cliente/<id>", methods=["POST"])
@login_required
def editar_cliente(id):
    db.collection("clientes").document(id).update(
        {
            "nome": request.form["nome"],
            "telefone": request.form["telefone"],
            "data_nascimento": request.form.get("data_nascimento", ""),
        }
    )
    return redirect(url_for("clientes"))


@app.route("/toggle_cliente/<id>")
@login_required
def toggle_cliente(id):
    ref = db.collection("clientes").document(id)
    c = ref.get().to_dict()
    ref.update({"status": "inativo" if c.get("status") == "ativo" else "ativo"})
    return redirect(url_for("clientes"))


# ==========================================
# VENDAS E FINANCEIRO
# ==========================================


def gerar_proximo_pedido():
    ref_meta = db.collection("config").document("vendas")
    meta = ref_meta.get()
    novo_n = (meta.to_dict().get("ultimo", 0) + 1) if meta.exists else 1
    ref_meta.set({"ultimo": novo_n})
    return novo_n


@app.route("/vendas", methods=["GET", "POST"])
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
        return redirect(url_for("vendas"))

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


@app.route("/editar_venda/<id>", methods=["POST"])
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
    return redirect(url_for("vendas"))


@app.route("/pagar_venda/<id>")
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
    return redirect(url_for("vendas"))


@app.route("/cancelar_venda/<id>")
@login_required
def cancelar_venda(id):
    db.collection("vendas").document(id).update({"status": "cancelado"})
    for d in db.collection("financeiro").where("id_venda", "==", id).stream():
        db.collection("financeiro").document(d.id).update({"status": "cancelado"})
    return redirect(url_for("vendas"))


@app.route("/financeiro", methods=["GET", "POST"])
@login_required
def financeiro():
    if request.method == "POST":
        db.collection("financeiro").add(
            {
                "descricao": request.form["descricao"],
                "valor": float(request.form["valor"]),
                "tipo": request.form["tipo"],
                "data_vencimento": request.form["data_vencimento"],
                "status": "pendente",
                "id_venda": None,
            }
        )
        return redirect(url_for("financeiro"))

    hoje = datetime.now().strftime("%Y-%m-%d")
    lans = []
    for l in db.collection("financeiro").stream():
        d = l.to_dict()
        d["id"] = l.id
        if (
            d.get("status") == "pendente"
            and d.get("data_vencimento")
            and d.get("data_vencimento") < hoje
        ):
            d["status"] = "vencido"
        lans.append(d)

    te = sum(
        [l["valor"] for l in lans if l["tipo"] == "entrada" and l["status"] == "pago"]
    )
    ts = sum(
        [l["valor"] for l in lans if l["tipo"] == "saida" and l["status"] == "pago"]
    )
    return render_template(
        "financeiro.html",
        lancamentos=lans,
        total_entradas=te,
        total_saidas=ts,
        saldo=te - ts,
    )


@app.route("/pagar_financeiro/<id>")
@login_required
def pagar_financeiro(id):
    db.collection("financeiro").document(id).update({"status": "pago"})
    return redirect(url_for("financeiro"))


@app.route("/editar_financeiro/<id>", methods=["POST"])
@login_required
def editar_financeiro(id):
    db.collection("financeiro").document(id).update(
        {
            "descricao": request.form["descricao"],
            "valor": float(request.form["valor"]),
            "tipo": request.form["tipo"],
            "data_vencimento": request.form["data_vencimento"],
        }
    )
    return redirect(url_for("financeiro"))


@app.route("/cancelar_financeiro/<id>")
@login_required
def cancelar_financeiro(id):
    db.collection("financeiro").document(id).update({"status": "cancelado"})
    return redirect(url_for("financeiro"))


# ==========================================
# PARÂMETROS DO SISTEMA
# ==========================================

@app.route("/parametros")
@login_required
def parametros():
    marcas_raw = db.collection("marcas").order_by("nome").stream()
    marcas = [{"id": m.id, **m.to_dict()} for m in marcas_raw]
    config_doc = db.collection("config").document("sistema").get()
    config = config_doc.to_dict() if config_doc.exists else {}
    msg_aniversario = config.get("msg_aniversario", "Olá {nome}! 🎂 Feliz aniversário! Que seu dia seja especial! 🎉")
    return render_template("parametros.html", usuario_id=session["user_id"], marcas=marcas, msg_aniversario=msg_aniversario)


@app.route("/parametros/mensagens", methods=["POST"])
@login_required
def parametros_mensagens():
    msg = request.form.get("msg_aniversario", "").strip()
    db.collection("config").document("sistema").set({"msg_aniversario": msg}, merge=True)
    flash("Mensagem de aniversário salva com sucesso!", "success")
    return redirect(url_for("parametros"))


@app.route("/parametros/conta", methods=["POST"])
@login_required
def parametros_conta():
    nova_senha = request.form.get("nova_senha", "").strip()
    confirmar = request.form.get("confirmar_senha", "").strip()
    if nova_senha:
        if nova_senha != confirmar:
            flash("As senhas não coincidem.", "danger")
        else:
            db.collection("usuarios").document(session["user_id"]).update(
                {"password": generate_password_hash(nova_senha)}
            )
            flash("Senha alterada com sucesso!", "success")
    else:
        flash("Nenhuma alteração realizada.", "info")
    return redirect(url_for("parametros"))


@app.route("/parametros/marcas", methods=["POST"])
@login_required
def parametros_marcas_add():
    nome = request.form.get("nome_marca", "").strip().upper()
    if nome:
        existentes = [m.to_dict().get("nome") for m in db.collection("marcas").stream()]
        if nome in existentes:
            flash(f'A marca "{nome}" já existe.', "warning")
        else:
            db.collection("marcas").add({"nome": nome})
            flash(f'Marca "{nome}" adicionada!', "success")
    return redirect(url_for("parametros"))


@app.route("/parametros/marcas/remover/<id>", methods=["POST"])
@login_required
def parametros_marcas_remover(id):
    db.collection("marcas").document(id).delete()
    flash("Marca removida.", "info")
    return redirect(url_for("parametros"))


# Rota API: retorna marcas em JSON para uso dinâmico nas telas
@app.route("/api/marcas")
@login_required
def api_marcas():
    from flask import jsonify
    marcas = [{"id": m.id, "nome": m.to_dict()["nome"]} for m in db.collection("marcas").order_by("nome").stream()]
    return jsonify(marcas)


# Rota API: verifica duplicidade de produto pelo nome
@app.route("/api/verificar_produto")
@login_required
def api_verificar_produto():
    from flask import jsonify
    nome = request.args.get("nome", "").strip().lower()
    sku  = request.args.get("sku", "").strip().lower()
    if not nome and not sku:
        return jsonify({"status": "ok"})
    produtos = [{"id": p.id, **p.to_dict()} for p in db.collection("produtos").stream()]
    for p in produtos:
        nome_cad = p.get("nome", "").strip().lower()
        sku_cad  = p.get("sku", "").strip().lower()
        if nome_cad == nome or (sku and sku_cad and sku_cad == sku):
            return jsonify({
                "status": "identico",
                "id": p["id"],
                "nome": p.get("nome", ""),
                "quantidade": p.get("quantidade", 0),
            })
    return jsonify({"status": "ok"})

@app.route("/estoque/somar_quantidade/<id>", methods=["POST"])
@login_required
def somar_quantidade(id):
    from flask import jsonify
    qtd = int(request.json.get("quantidade", 0))
    prod_ref = db.collection("produtos").document(id)
    prod = prod_ref.get().to_dict()
    nova_qtd = int(prod.get("quantidade", 0)) + qtd
    prod_ref.update({"quantidade": nova_qtd})
    return jsonify({"ok": True, "nova_quantidade": nova_qtd})



# ==========================================
# NOTAS DE ATUALIZAÇÃO
# ==========================================

@app.route("/marcar_versao_vista", methods=["POST"])
@login_required
def marcar_versao_vista():
    from flask import jsonify
    db.collection("usuarios").document(session["user_id"]).update(
        {"versao_vista": VERSAO_ATUAL}
    )
    return jsonify({"ok": True})


# ==========================================
# POST-ITS DA HOME
# ==========================================

@app.route("/postit/add", methods=["POST"])
@login_required
def postit_add():
    from flask import jsonify
    texto = request.json.get("texto", "").strip()
    cor = request.json.get("cor", "#fef9c3")
    if not texto:
        return jsonify({"erro": "vazio"}), 400
    # ordem = maior existente + 1
    existentes = list(db.collection("postits").stream())
    ordem = max([p.to_dict().get("ordem", 0) for p in existentes], default=0) + 1
    ref = db.collection("postits").add({"texto": texto, "cor": cor, "ordem": ordem})
    return jsonify({"id": ref[1].id, "texto": texto, "cor": cor, "ordem": ordem})


@app.route("/postit/delete/<id>", methods=["POST"])
@login_required
def postit_delete(id):
    from flask import jsonify
    db.collection("postits").document(id).delete()
    return jsonify({"ok": True})


if __name__ == "__main__":
    import os

    # O Render define a porta automaticamente, se não houver, usa 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)