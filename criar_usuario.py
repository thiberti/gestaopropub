import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash

# 1. Configuração
cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. Dados do acesso
usuario = "demo"  # <-- Digite aqui o nome de usuário desejado
senha = "demo123"  # <-- Digite aqui a senha

# 3. Salvar no Firebase
# O ID do documento será o próprio nome de usuário
db.collection("usuarios").document(usuario).set(
    {
        "username": usuario,
        "password": generate_password_hash(senha),
        "ver_financeiro": True,
        "ver_estoque": True,
    }
)

print(f"Sucesso! Usuário '{usuario}' criado/atualizado.")
