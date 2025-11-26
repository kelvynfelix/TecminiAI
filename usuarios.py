import json
import os



ARQUIVO_USUARIOS = "usuarios.json"
usuario_logado = None

# ==========================
# CARREGAR E SALVAR USUÁRIOS
# ==========================

def carregar_usuarios():
    """Carrega o arquivo JSON completo dos usuários."""
    if not os.path.exists(ARQUIVO_USUARIOS):
        return {"users": []}

    with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Se o arquivo quebrar, recria
            return {"users": []}


def salvar_usuarios(dados):
    """Salva o JSON completo."""
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


# ==========================
# FUNÇÕES DE LOGIN
# ==========================

def usuario_existe(username):
    dados = carregar_usuarios()
    return any(u["username"] == username for u in dados["users"])


def validar_login(username, senha):
    dados = carregar_usuarios()
    for u in dados["users"]:
        if u["username"] == username and u["password"] == senha:
            return True
    return False


def criar_usuario(nome, username, senha):
    dados = carregar_usuarios()

    if usuario_existe(username):
        return False  # usuário já existe

    dados["users"].append({
        "nome": nome,
        "username": username,
        "password": senha,
        "memory": {}  # memória individual do usuário
    })

    salvar_usuarios(dados)
    return True


# ==========================
# MEMÓRIA INDIVIDUAL DO USUÁRIO
# ==========================

def carregar_memoria(username):
    """Retorna a memória do usuário como dict."""
    dados = carregar_usuarios()

    for u in dados["users"]:
        if u["username"] == username:
            # Garante que exista memory
            if "memory" not in u:
                u["memory"] = {}
                salvar_usuarios(dados)
            return u["memory"]

    return {}  # usuário não encontrado


def salvar_memoria(username, memoria):
    """Atualiza o campo memory do usuário."""
    dados = carregar_usuarios()

    for u in dados["users"]:
        if u["username"] == username:
            u["memory"] = memoria
            break

    salvar_usuarios(dados)
