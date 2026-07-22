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