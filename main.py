import re
import threading
from time import sleep
import flet as ft
import API
from usuarios import validar_login, criar_usuario, usuario_existe

# ---------------------------------------------------
# Função segura para UI
# ---------------------------------------------------
def get_scheduler(page: ft.Page):
    if hasattr(page, "call_from_thread"):
        return page.call_from_thread
    elif hasattr(page, "run_on_main_thread"):
        return page.run_on_main_thread
    elif hasattr(page, "invoke_later"):
        return page.invoke_later
    else:
        return lambda fn: fn()


# ---------------------------------------------------
# CHAT (ChatApp substituído pelo novo com suporte a formatação)
# ---------------------------------------------------
class ChatApp(ft.Column):
    def __init__(self, page, drawer=None):
        super().__init__()
        self.page = page
        self.drawer = drawer
        self.expand = True
        self.spacing = 10
        self._schedule = get_scheduler(page)

        self.chat_area = ft.ListView(expand=True, auto_scroll=True, spacing=10)

        self.new_message = ft.TextField(
            hint_text="Digite aqui...",
            expand=True,
            autofocus=True,
            on_submit=self.send_message,
        )

        self.send_button = ft.FloatingActionButton(
            icon=ft.Icons.SEND,
            bgcolor="#B20000",  # fundo padrão
            foreground_color="white",  # cor do ícone
            on_click=self.send_message,
        )

        input_bar = ft.Container(
            content=ft.Row(
                controls=[self.new_message, self.send_button],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            padding=10,
            border_radius=ft.border_radius.all(12),
        )

        self.controls = [self.chat_area, input_bar]

    # limpar histórico
    def limpar_historico(self):
        self.chat_area.controls.clear()
        self.page.update()

    # envio de mensagem (usuário)
    def send_message(self, e):
        texto = (self.new_message.value or "").strip()
        if not texto:
            return

        self.new_message.disabled = True
        self.send_button.disabled = True
        self.page.update()

        # bolha do usuário usando format_text para permitir rich text caso necessário
        user_bubble = ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.Container(
                    content=self.format_text(texto),
                    bgcolor=ft.Colors.with_opacity(0.5,"#B20000" ),
                    padding=10,
                    border_radius=ft.border_radius.all(12),
                    margin=ft.margin.only(left=80),
                    width=min(520, max(120, len(texto) * 8)),
                )
            ],
        )

        self.chat_area.controls.append(user_bubble)
        self.new_message.value = ""
        self.page.update()

        threading.Thread(target=self.bot_reply, args=(texto,), daemon=True).start()

    # função auxiliar que converte texto com **negrito** e [label](url) e retorna um Row
    def format_text(self, text):
        """
        Converte **negrito** e [link](https://...) em widgets Flet.
        Retorna um ft.Row com ft.Text / ft.TextButton.
        """
        parts = []
        i = 0

        # primeiro processa links
        link_pat = re.compile(r"\[(.*?)]\((.*?)\)")
        for match in link_pat.finditer(text):
            start, end = match.span()
            label = match.group(1)
            url = match.group(2)

            if start > i:
                remaining = text[i:start]
                # processa negrito no trecho anterior
                parts.extend(self._split_bold_to_texts(remaining))

            parts.append(
                ft.TextButton(
                    content=ft.Text(label, size=16, color=ft.Colors.BLUE_400),
                    style=ft.ButtonStyle(padding=0, bgcolor="transparent", overlay_color="transparent"),
                    on_click=lambda e, link=url: self.page.launch_url(link),
                )
            )
            i = end

        # resto do texto (apos últimos links)
        tail = text[i:]
        parts.extend(self._split_bold_to_texts(tail))

        return ft.Row(controls=parts, spacing=0, wrap=True)

    # noinspection PyMethodMayBeStatic
    def _split_bold_to_texts(self, text):
        """Divide o texto em partes normais e **negrito** e retorna lista de ft.Text"""
        out = []
        bold_pat = re.compile(r"\*\*(.*?)\*\*")
        j = 0
        for m in bold_pat.finditer(text):
            s, e = m.span()
            if s > j:
                out.append(ft.Text(text[j:s], size=16))
            out.append(ft.Text(m.group(1), size=16, weight=ft.FontWeight.BOLD))
            j = e
        if j < len(text):
            out.append(ft.Text(text[j:], size=16))
        return out

    # parse_message cria colunas de linhas, suportando listas com * e texto simples
    def parse_message(self, text):
        lines = text.split("\n")
        widgets = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("* "):
                item = stripped[2:]
                widgets.append(
                    ft.Row(
                        controls=[ft.Text("•", size=16), self.format_text(item)],
                        spacing=6,
                    )
                )
            else:
                widgets.append(self.format_text(stripped))
        return widgets

    # bolha do bot (usa parse_message)
    def create_bot_bubble(self, raw_text):
        content = self.parse_message(raw_text)
        return ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Column(controls=content, spacing=5, tight=True),
                    bgcolor=ft.Colors.with_opacity(0.3, "WHITE"),
                    padding=12,
                    border_radius=ft.border_radius.all(12),
                    margin=ft.margin.only(right=80),
                    width=520,
                )
            ],
        )

    # simulador de reply do bot (chamada API)
    def bot_reply(self, user_text):
        global usuario_logado  # <-- obrigatório para acessar o usuário logado

        typing = ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Text(
                        "TecminiAI está digitando...",
                        size=15,
                        italic=True,
                        color=ft.Colors.GREY_500
                    ),
                    padding=10,
                )
            ],
        )

        # adicionar "digitando..."
        self._schedule(lambda: self.show_typing(typing))

        try:
            resposta = API.responder(user_text, usuario_logado)
        except Exception as e:
            resposta = f"Erro ao gerar resposta: {e}"

        # mostrar resposta
        self._schedule(lambda: self.show_bot_reply(typing, resposta))

    def show_typing(self, typing_row):
        self.chat_area.controls.append(typing_row)
        self.page.update()

    def show_bot_reply(self, typing_row, resposta):
        if typing_row in self.chat_area.controls:
            self.chat_area.controls.remove(typing_row)

        self.chat_area.controls.append(self.create_bot_bubble(resposta))

        self.new_message.disabled = False
        self.send_button.disabled = False

        try:
            self.new_message.focus()
        except:
            pass

        self.page.update()


# ---------------------------------------------------
# TELA DE LOGIN + CADASTRO + CHAT
# ---------------------------------------------------
def main(page: ft.Page):
    # abrir fullscreen e estilo base
    page.window_full_screen = True
    page.padding = 20
    page.bgcolor = "#191919"
    page.theme_mode = ft.ThemeMode.DARK

    def carregar_login():
        page.clean()

        user_field = ft.TextField(label="Usuário", width=250, max_length=20)
        pass_field = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=250, max_length=30)

        # permitir ENTER em usuário para focar senha; ENTER em senha tenta login
        user_field.on_submit = lambda e: pass_field.focus()

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        def tentar_login(e):
            global usuario_logado

            user = user_field.value.strip()
            pwd = pass_field.value.strip()

            if validar_login(user, pwd):
                usuario_logado = user
                print("Logado como:", usuario_logado)
                carregar_chat()  # ← mantém o que já existia
            else:
                error_text.value = "Usuário ou senha incorretos."
                error_text.visible = True
                page.update()

        # set pass_field.on_submit after function defined
        pass_field.on_submit = lambda e: tentar_login(e)

        login_button = ft.ElevatedButton(
            "Entrar",
            width=250,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: "#B20000",
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                },
                color={
                    ft.ControlState.DEFAULT: "#FFFFFF",
                    ft.ControlState.HOVERED: "#B20000",
                },
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=tentar_login)

        cadastrar_link = ft.TextButton(
            "Cadastre-se",
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: "#B20000",
                    ft.ControlState.HOVERED: "white",
                }
            ),
            on_click=lambda _: carregar_cadastro())

        login_box = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Login", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    user_field,
                    pass_field,
                    error_text,
                    login_button,
                    cadastrar_link,
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=350,
            height=400,
            padding=30,
            border_radius=ft.border_radius.all(20),
            bgcolor= "#191919",
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=14, color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE), offset=ft.Offset(0, 10)),
        )

        page.add(ft.Container(content=login_box, expand=True, alignment=ft.alignment.center))

    def carregar_cadastro():
        page.clean()

        nome_field = ft.TextField(label="Nome completo", width=250, max_length=32)
        user_field = ft.TextField(label="Usuário", width=250, max_length=20)
        pass_field = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=250, max_length=30)

        # MENSAGENS DE VALIDAÇÃO (embaixo de cada input)
        msg_nome = ft.Text("", color=ft.Colors.RED, visible=False, size=12)
        msg_user = ft.Text("", color=ft.Colors.RED, visible=False, size=12)
        msg_senha = ft.Text("", color=ft.Colors.RED, visible=False, size=12)

        # validators on-blur
        def validar_nome(e):
            texto = nome_field.value.strip()
            if len(texto) < 5:
                msg_nome.value = "Mínimo: 5 caracteres"
                msg_nome.visible = True
            else:
                msg_nome.visible = False
            page.update()

        # noinspection PyUnusedLocal
        def validar_usuario(e):
            texto = user_field.value.strip()
            if len(texto) < 5:
                msg_user.value = "Mínimo: 5 caracteres"
                msg_user.visible = True
            elif usuario_existe(texto):
                msg_user.value = "Usuário já existe"
                msg_user.visible = True
            else:
                msg_user.visible = False
            page.update()

        def validar_senha(e):
            texto = pass_field.value.strip()
            if len(texto) < 5:
                msg_senha.value = "Mínimo: 5 caracteres"
                msg_senha.visible = True
            else:
                msg_senha.visible = False
            page.update()

        # ativa validação ao perder foco
        nome_field.on_blur = validar_nome
        user_field.on_blur = validar_usuario
        pass_field.on_blur = validar_senha

        # fluxo ENTER
        nome_field.on_submit = lambda e: user_field.focus()
        user_field.on_submit = lambda e: pass_field.focus()

        msg = ft.Text("", visible=False)

        def registrar(e):
            nome = nome_field.value.strip()
            user = user_field.value.strip()
            senha = pass_field.value.strip()

            max_nome = 32
            max_user = 20
            max_senha = 30

            if len(nome) < 5 or len(user) < 5 or len(senha) < 5:
                msg.value = "Todos os campos devem ter pelo menos 5 caracteres!"
                msg.color = ft.Colors.RED
                msg.visible = True
                page.update()
                return

            if len(nome) > max_nome:
                msg.value = f"O nome deve ter no máximo {max_nome} caracteres."
                msg.color = ft.Colors.RED
                msg.visible = True
                page.update()
                return

            if len(user) > max_user:
                msg.value = f"O usuário deve ter no máximo {max_user} caracteres."
                msg.color = ft.Colors.RED
                msg.visible = True
                page.update()
                return

            if len(senha) > max_senha:
                msg.value = f"A senha deve ter no máximo {max_senha} caracteres."
                msg.color = ft.Colors.RED
                msg.visible = True
                page.update()
                return

            if usuario_existe(user):
                msg.value = "Este usuário já existe!"
                msg.color = ft.Colors.RED
                msg.visible = True
                page.update()
                return

            criar_usuario(nome, user, senha)

            msg.value = "Cadastro realizado com sucesso!"
            msg.color = ft.Colors.GREEN
            msg.visible = True
            page.update()

            # volta para login após 1s
            threading.Thread(target=lambda: (sleep(1), carregar_login()), daemon=True).start()

        pass_field.on_submit = lambda e: registrar(e)

        cadastro_button = ft.ElevatedButton(
            "Cadastrar",
            width=250,
            on_click=registrar,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: "#B20000",
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                },
                color={
                    ft.ControlState.DEFAULT: "#FFFFFF",
                    ft.ControlState.HOVERED: "#B20000",
                },
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )

        voltar = ft.TextButton(
            "Voltar",
            style=ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: "#B20000",
                ft.ControlState.HOVERED: "white",
            }
            ),
            on_click=lambda _: carregar_login())

        box = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Cadastro", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    nome_field,
                    msg_nome,
                    user_field,
                    msg_user,
                    pass_field,
                    msg_senha,
                    msg,
                    cadastro_button,
                    voltar,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=350,
            height=430,
            padding=30,
            border_radius=ft.border_radius.all(20),
            bgcolor= "#191919",
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=14, color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE), offset=ft.Offset(0, 10)),
        )

        page.add(ft.Container(content=box, expand=True, alignment=ft.alignment.center))

    def carregar_chat():
        page.clean()
        page.title = "TecminiAI"
        page.bgcolor = "#191919"

        def voltar():
            page.clean()
            page.appbar = None
            page.drawer = None
            carregar_login()

        drawer = ft.NavigationDrawer(
            controls=[
                ft.Container(content=ft.TextButton(
                    "Limpar histórico",
                    style=ft.ButtonStyle(
                        color={
                            ft.ControlState.DEFAULT: "white",
                            ft.ControlState.HOVERED: "grey",
                        }
                    ),
                    on_click=lambda _: app.limpar_historico()),
                    padding=ft.padding.only(top=20)),
                ft.Container(content=ft.TextButton(
                    "Sair",
                    style=ft.ButtonStyle(
                        color={
                            ft.ControlState.DEFAULT: "#B20000",
                            ft.ControlState.HOVERED: "white",
                        }
                    ),
                    on_click=lambda _: voltar()),
                    padding=ft.padding.only(top=10)),
            ]
        )

        page.drawer = drawer

        menu_button = ft.IconButton(icon=ft.Icons.MENU, on_click=lambda _: abrir_menu())

        def abrir_menu():
            page.drawer.open = True
            page.update()

        global app
        app = ChatApp(page, drawer)

        page.appbar = ft.AppBar(leading=menu_button, title=ft.Text("TecminiAI", color=ft.Colors.WHITE), bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))

        page.add(app)
        page.update()

    carregar_login()


if __name__ == "__main__":
    ft.app(target=main)
