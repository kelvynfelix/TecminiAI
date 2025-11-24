import google.generativeai as genai
import json
import datetime
from dotenv import load_dotenv
import os
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
    "bosta","merda","caralho","fdp","foda","porra","pqp","vtnc","vsf",
    "otario","otária","troxa","trouxa","burro","burra","cu","arrombado"
]

def tem_palavrao(msg):
    msg = msg.lower()
    achou = False
    for p in PALAVROES:
        if p in msg:
            achou = True

    return achou


# ======================================================
# SISTEMA DE CONSULTA AO JSON (INTELIGENTE)
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
    if "nome da escola" in msg_lower or "qual é a escola" in msg_lower:
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

    return None  # Nada encontrado

# ======================================================
# GEMINI (fallback automático)
# ======================================================
def responder_com_gemini(msg):
    model = genai.GenerativeModel(MODEL)
    resposta = model.generate_content(
        f"""
        Você é um assistente que responde APENAS sobre a escola Etec Cônego José Bento.
        Você pode responder perguntas de educação, bom dia, e tals e pode despedir quando a pessoa quiser terminar o chat.
        Se a pergunta não tiver relação com a escola, responda:
        'Não posso responder isso, pois só respondo perguntas relacionadas à escola.'

        Aqui estão os dados da escola que você pode usar:
        {json.dumps(dados, ensure_ascii=False, indent=2)}

        Pergunta do usuário: "{msg}"

        A data de hoje é: {datetime.datetime.now().strftime('%d/%m/%Y')}
        """
    )
    # Certifique-se de pegar o texto correto dependendo da versão do genai
    return getattr(resposta, "text", getattr(resposta, "output_text", "Erro ao gerar resposta"))

# ======================================================
# FUNÇÃO PRINCIPAL
# ======================================================
def responder(msg):
    msg = msg.strip()
    if not msg:
        return "Digite alguma coisa!"

    if tem_palavrao(msg):
        return "Por favor, mantenha o respeito. Não posso responder com palavrões."

    # Buscar no JSON primeiro
    info = buscar_info_escola(msg)
    if info:
        return info

    # Se não achar → usa o Gemini
    return responder_com_gemini(msg)
