from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash

from firebase import db
from utils.auth import login_required
from config import VERSAO_ATUAL
from utils.empresa import colecao_empresa

parametros_bp = Blueprint(
    "parametros",
    __name__
)

@parametros_bp.route("/parametros")
@login_required
def parametros():
    marcas_raw = colecao_empresa("marcas").order_by("nome").stream()
    marcas = [{"id": m.id, **m.to_dict()} for m in marcas_raw]
    config_doc = db.collection("config").document("sistema").get()
    config = config_doc.to_dict() if config_doc.exists else {}
    msg_aniversario = config.get("msg_aniversario", "Olá {nome}! 🎂 Feliz aniversário! Que seu dia seja especial! 🎉")
    return render_template("parametros.html", usuario_id=session["user_id"], marcas=marcas, msg_aniversario=msg_aniversario)


@parametros_bp.route("/parametros/mensagens", methods=["POST"])
@login_required
def parametros_mensagens():
    msg = request.form.get("msg_aniversario", "").strip()
    db.collection("config").document("sistema").set({"msg_aniversario": msg}, merge=True)
    flash("Mensagem de aniversário salva com sucesso!", "success")
    return redirect(url_for("parametros.parametros"))


@parametros_bp.route("/parametros/conta", methods=["POST"])
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
    return redirect(url_for("parametros.parametros"))


@parametros_bp.route("/parametros/marcas", methods=["POST"])
@login_required
def parametros_marcas_add():
    nome = request.form.get("nome_marca", "").strip().upper()
    if nome:
        existentes = [m.to_dict().get("nome") for m in colecao_empresa("marcas").stream()]
        if nome in existentes:
            flash(f'A marca "{nome}" já existe.', "warning")
        else:
            colecao_empresa("marcas").add({"nome": nome})
            flash(f'Marca "{nome}" adicionada!', "success")
    return redirect(url_for("parametros.parametros"))


@parametros_bp.route("/parametros/marcas/remover/<id>", methods=["POST"])
@login_required
def parametros_marcas_remover(id):
    colecao_empresa("marcas").document(id).delete()
    flash("Marca removida.", "info")
    return redirect(url_for("parametros.parametros"))

# Rota API: retorna marcas em JSON para uso dinâmico nas telas
@parametros_bp.route("/api/marcas")
@login_required
def api_marcas():
    marcas = [{"id": m.id, "nome": m.to_dict()["nome"]} for m in colecao_empresa("marcas").order_by("nome").stream()]
    return jsonify(marcas)



# ==========================================
# NOTAS DE ATUALIZAÇÃO
# ==========================================

@parametros_bp.route("/marcar_versao_vista", methods=["POST"])
@login_required
def marcar_versao_vista():
    db.collection("usuarios").document(session["user_id"]).update(
        {"versao_vista": VERSAO_ATUAL}
    )
    return jsonify({"ok": True})


# ==========================================
# POST-ITS DA HOME
# ==========================================

@parametros_bp.route("/postit/add", methods=["POST"])
@login_required
def postit_add():
    texto = request.json.get("texto", "").strip()
    cor = request.json.get("cor", "#fef9c3")
    if not texto:
        return jsonify({"erro": "vazio"}), 400
    # ordem = maior existente + 1
    existentes = list(colecao_empresa("postits").stream())
    ordem = max([p.to_dict().get("ordem", 0) for p in existentes], default=0) + 1
    ref = colecao_empresa("postits").add({"texto": texto, "cor": cor, "ordem": ordem})
    return jsonify({"id": ref[1].id, "texto": texto, "cor": cor, "ordem": ordem})


@parametros_bp.route("/postit/delete/<id>", methods=["POST"])
@login_required
def postit_delete(id):
    colecao_empresa("postits").document(id).delete()
    return jsonify({"ok": True})