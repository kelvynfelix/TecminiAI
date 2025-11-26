import google.generativeai as genai
import json
from dotenv import load_dotenv
import os

from usuarios import carregar_memoria, salvar_memoria

#               CONFIGURAR GEMINI
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

# ======================================================
# CARREGAR JSON DA ESCOLA
# ======================================================
with open("dados_escola.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

# ======================================================
# PALAVRÕES PARA BLOQUEAR
# ======================================================
PALAVROES = [
    "bosta", "merda", "caralho", "fdp", "foda", "porra", "pqp", "vtnc", "vsf",
    "otario", "otária", "troxa", "trouxa", "burro", "burra", "cu", "arrombado"
]


def tem_palavrao(msg):
    msg = msg.lower()
    achou = False
    for p in PALAVROES:
        if p in msg:
            achou = True
    return achou


# ======================================================
# CONSULTAS AO JSON
# ======================================================
def buscar_info_escola(msg):
    msg_lower = msg.lower()

    # Diretoria
    diretoria = dados.get("diretoria", {})
    if "diretor" in msg_lower:
        return f"O diretor é {diretoria.get('diretor', 'não informado')}."
    if "vice" in msg_lower or "vice-diretor" in msg_lower:
        return f"O vice-diretor é {diretoria.get('vice_diretor', 'não informado')}."
    if "coordenador" in msg_lower:
        return f"O coordenador é {diretoria.get('coordenador', 'não informado')}."

    # Nome da escola
    if "nome da escola" in msg_lower:
        return f"O nome da escola é {dados.get('nome', 'não informado')}."

    # Endereço
    if "endereço" in msg_lower:
        return f"O endereço da escola é: {dados.get('endereco', 'não informado')}."

    # Telefone
    if "telefone" in msg_lower:
        return f"O telefone da escola é {dados.get('telefone', 'não informado')}."

    # Professores
    professores = dados.get("professores", {})
    for materia, prof in professores.items():
        if materia.lower() in msg_lower:
            return f"O(a) professor(a) de {materia} é {prof}."

    # Horários
    horarios = dados.get("horarios", {})
    if "horário" in msg_lower or "horarios" in msg_lower:
        return (
            f"Horários da escola:\n"
            f"• Manhã: {horarios.get('manhã', 'não informado')}\n"
            f"• Tarde: {horarios.get('tarde', 'não informado')}"
        )

    return None


# ======================================================
# GEMINI COM MEMÓRIA DO USUÁRIO
# ======================================================
def responder_com_gemini(msg, usuario):
    model = genai.GenerativeModel(MODEL)

    memoria = carregar_memoria(usuario)

    contexto = "\n".join(f"{k}: {v}" for k, v in memoria.items())

    info_escola_texto = json.dumps(dados, ensure_ascii=False, indent=2)

    prompt = f"""
    Você é um assistente da escola Etec Cônego José Bento.

    A seguir estão TODAS as informações oficiais da escola (NÃO invente nada que não esteja aqui):
    {info_escola_texto}

    INFORMAÇÕES SOBRE O USUÁRIO:
    {contexto}

    PERGUNTA DO USUÁRIO:
    "{msg}"

    REGRAS:
    - Se o usuário disser informações pessoais, memorize.
    - Não invente dados. Só responda com base no JSON.
    - Se o usuário pedir algo que não está no JSON, apenas diga que não há essa informação cadastrada.
    - Seja educado e natural.
    """

    resposta = model.generate_content(prompt).text

    # ------------ ATUALIZA A MEMÓRIA ------------
    gatilhos = ["eu gosto", "meu nome é", "moro", "estudo", "minha idade"]
    lower = msg.lower()

    for g in gatilhos:
        if g in lower:
            memoria["ultima_info"] = msg
            salvar_memoria(usuario, memoria)
            break

    return resposta


def eh_assunto_da_escola(msg):
    msg = msg.lower().strip()

    # -----------------------------
    # 1) Sempre permitido
    # -----------------------------
    sempre_ok = [
        "oi", "olá", "ola", "eae", "salve", "hey",
        "bom dia", "boa tarde", "boa noite",
        "tudo bem", "como você está", "como vai",
        "beleza", "suave", "tranquilo",

        "que dia é hoje", "que horas são",
        "hora", "horas", "dia", "data",
        "clima", "tempo", "temperatura", "agora"
    ]
    for p in sempre_ok:
        if p in msg:
            return True

    # -----------------------------
    # 2) Palavras claramente da escola
    # -----------------------------
    palavras_escola = [
        "etec", "escola", "cônego", "conego", "jose bento", "josé bento",
        "diretor", "diretora", "vice", "coordenador",
        "professor", "professora",
        "sala", "salas", "biblioteca", "lab", "laboratório", "quadra",
        "curso", "cursos", "materia", "matéria", "disciplina",
        "horário", "horarios", "turma", "aluno", "aluna", "estudante",
        "secretaria", "rematrícula", "matrícula",
        "prova", "atividade", "trabalho", "evento", "palestra"
    ]
    if any(p in msg for p in palavras_escola):
        return True

    # -----------------------------
    # 3) Lista de assuntos proibidos
    # -----------------------------
    proibidos = [
        # tecnologia
        "python", "programar", "programação", "javascript", "html",
        "como faço um código", "faça um código", "faça um programa",

        # jogos
        "roblox", "minecraft", "fortnite", "jogo", "games",

        # carros
        "carro", "carro melhor", "carros",

        # medicina
        "doença", "remédio", "diagnóstico", "saúde",

        # coisas ilegais
        "hackear", "hack", "invadir", "crackear",

        # entretenimento
        "filme", "série", "musica", "cantor", "cantora",

        # filosofia / ciência não escolar
        "física quântica", "universo", "cosmos",

        # esportes
        "futebol", "basquete",

        # compras
        "comprar", "preço", "valor"
    ]
    if any(p in msg for p in proibidos):
        return False

    # -----------------------------
    # 4) Perguntas muito amplas → bloqueia
    # -----------------------------
    perguntas_muito_abertas = [
        "me explique", "explique", "o que é", "defina",
        "como funciona", "me ajude com"
    ]
    if any(msg.startswith(p) for p in perguntas_muito_abertas):
        return False

    # -----------------------------
    # 5) Perguntas curtas → assume que é escolar
    # -----------------------------
    if len(msg.split()) <= 2:
        return True

    # -----------------------------
    # 6) Perguntas com "qual", "quando", "quem"
    # se não forem proibidas → ok
    # -----------------------------
    if msg.startswith(("quem", "quando", "qual", "como", "onde")):
        return True

    # Se chegou aqui → não é claramente escolar
    return False


# ======================================================
# FUNÇÃO PRINCIPAL (APENAS ADICIONADO PARAM USUARIO)
# ======================================================
def responder(msg, usuario):
    msg = msg.strip()
    if not msg:
        return "Digite alguma coisa!"

    if tem_palavrao(msg):
        return "Por favor, mantenha o respeito. Não posso responder com palavrões."

    # 1️⃣ JSON da escola
    info = buscar_info_escola(msg)
    if info:
        return info

    # 2️⃣ Filtro leve: só bloqueia quando NÃO for escola e NÃO for cumprimentos
    if not eh_assunto_da_escola(msg):
        return "Só posso responder perguntas relacionadas à Etec, à escola ou assuntos educacionais."

    # 3️⃣ Enviar para o Gemini (personalizado por usuário)
    return responder_com_gemini(msg, usuario)
