import json
import os

ARQUIVO_USUARIOS = "usuarios.json"

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return []

    with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("users", [])

def salvar_usuarios(lista):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump({"users": lista}, f, indent=4, ensure_ascii=False)

def usuario_existe(username):
    users = carregar_usuarios()
    return any(u["username"] == username for u in users)

def validar_login(username, senha):
    users = carregar_usuarios()
    for u in users:
        if u["username"] == username and u["password"] == senha:
            return True
    return False

def criar_usuario(nome, username, senha):
    users = carregar_usuarios()

    if usuario_existe(username):
        return False  # já existe

    users.append({
        "nome": nome,
        "username": username,
        "password": senha
    })

    salvar_usuarios(users)
    return True