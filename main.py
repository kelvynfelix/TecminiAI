<<<<<<< Updated upstream
import re
import threading
=======
<<<<<<< HEAD
from time import sleep

import flet as ft
import threading
import API
from usuarios import (
    validar_login, criar_usuario, usuario_existe
)


# ---------------------------------------------------
# Função segura para UI
# ---------------------------------------------------
=======
import re
import threading
>>>>>>> Stashed changes

import flet as ft

import API  # sua API com perguntar_escola()


# -------------------------
# Função segura para chamadas de UI (compatível com várias versões)
# -------------------------
>>>>>>> b33ee085821391d701de966a792de0da74d901b9
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
# CHAT
# ---------------------------------------------------
class ChatApp(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.expand = True
        self.spacing = 10
<<<<<<< HEAD
=======

        # scheduler compatível
<<<<<<< Updated upstream
=======
>>>>>>> b33ee085821391d701de966a792de0da74d901b9
>>>>>>> Stashed changes
        self._schedule = get_scheduler(page)

        self.chat_area = ft.ListView(expand=True, auto_scroll=True, spacing=10)

        self.new_message = ft.TextField(
            hint_text="Digite aqui...",
            expand=True,
            autofocus=True,
            on_submit=self.send_message,
        )

<<<<<<< Updated upstream
        # Botão enviar — CORRIGIDO
=======
<<<<<<< HEAD



=======
        # Botão enviar — CORRIGIDO
>>>>>>> b33ee085821391d701de966a792de0da74d901b9
>>>>>>> Stashed changes
        self.send_button = ft.FloatingActionButton(
            icon=ft.Icons.SEND,
            bgcolor=ft.Colors.BLUE_800,
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

<<<<<<< Updated upstream
=======
<<<<<<< HEAD
    def limpar_historico(self):
        self.chat_area.controls.clear()
        self.page.update()

=======
>>>>>>> Stashed changes
    # -------------------------
    # Envio de mensagem
    # -------------------------
>>>>>>> b33ee085821391d701de966a792de0da74d901b9
    def send_message(self, e):
        texto = (self.new_message.value or "").strip()
        if not texto:
            return

        self.new_message.disabled = True
        self.send_button.disabled = True
        self.page.update()

        self.chat_area.controls.append(self.create_user_bubble(texto))
        self.new_message.value = ""
        self.page.update()

        threading.Thread(target=self.bot_reply, args=(texto,), daemon=True).start()

    # Bolha do usuário
    def create_user_bubble(self, text):
        return ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.Container(
                    content=self.format_text(text),
                    bgcolor=ft.Colors.BLUE_800,
                    padding=10,
                    border_radius=ft.border_radius.all(12),
                    margin=ft.margin.only(left=80),
                    width=min(520, max(120, len(text) * 8)),
                )
            ],
        )

    def format_text(self, text):
        """
        Converte **negrito** e [link](https://...) em widgets Flet.
        """
        patterns = [
            (r"\*\*(.*?)\*\*", "bold"),  # negrito
            (r"\[(.*?)\]\((.*?)\)", "link")  # links
        ]

        parts = []
        i = 0

        # Detecta links primeiro
        for match in re.finditer(patterns[1][0], text):
            start, end = match.span()
            label = match.group(1)
            url = match.group(2)

            if start > i:
                parts.append(ft.Text(text[i:start], size=16))

            parts.append(
                ft.TextButton(
                    content=ft.Text(label, size=16, color=ft.Colors.BLUE),
                    style=ft.ButtonStyle(
                        padding=0,
                        bgcolor="transparent",
                        overlay_color="transparent",
                    ),
                    on_click=lambda _, link=url: self.page.launch_url(link),
                )
            )

            i = end

        text = text[i:]
        i = 0

        # Detecta negrito no trecho restante
        for match in re.finditer(patterns[0][0], text):
            start, end = match.span()
            bold_text = match.group(1)

            if start > i:
                parts.append(ft.Text(text[i:start], size=16))

            parts.append(ft.Text(bold_text, size=16, weight=ft.FontWeight.BOLD))
            i = end

        if i < len(text):
            parts.append(ft.Text(text[i:], size=16))

        return ft.Row(controls=parts, wrap=True, spacing=0)

    def _make_link_callback(self, url):
        return lambda e: self.page.launch_url(url)


    # -----------------------------
    # PARSER DE TEXTO COM:
    # - **negrito**
    # - * lista automática
    # - [texto](link)
    # -----------------------------
    def parse_message(self, text):
        lines = text.split("\n")
        widgets = []

        for line in lines:
            stripped = line.strip()

            # Bullet list
            if stripped.startswith("* "):
                item = stripped[2:]
                widgets.append(
                    ft.Row(
                        controls=[
                            ft.Text("•", size=16),
                            self._rich_text(item)
                        ],
                        spacing=6
                    )
                )
            else:
                widgets.append(self._rich_text(stripped))

        return widgets

    # -----------------------------
    # TEXTO RICO (negrito + links)
    # -----------------------------
    def _rich_text(self, text):
        import re

        bold_pat = re.compile(r"\*\*(.*?)\*\*")
        link_pat = re.compile(r"\[(.*?)\]\((.*?)\)")

        parts = []
        i = 0

        # Primeiro processa links
        for match in link_pat.finditer(text):
            start, end = match.span()
            label = match.group(1)
            url = match.group(2)

            if start > i:
                parts.append(ft.Text(text[i:start], size=16))

            parts.append(
                ft.TextButton(
                    content=ft.Text(label, size=16, color=ft.Colors.BLUE_400),
                    style=ft.ButtonStyle(
                        padding=0,
                        bgcolor="transparent",
                        overlay_color="transparent",
                    ),
                    on_click=lambda e, link=url: self.page.launch_url(link),
                )
            )

            i = end

        # Texto restante sem links
        text = text[i:]
        i = 0

        # Agora aplica negrito
        for match in bold_pat.finditer(text):
            start, end = match.span()
            bold_txt = match.group(1)

            if start > i:
                parts.append(ft.Text(text[i:start], size=16))

            parts.append(
                ft.Text(bold_txt, size=16, weight=ft.FontWeight.BOLD)
            )

            i = end

        if i < len(text):
            parts.append(ft.Text(text[i:], size=16))

        return ft.Row(controls=parts, spacing=0, wrap=True)

    # Bolha do bot
    def create_bot_bubble(self, raw_text):
        content = self.parse_message(raw_text)

        return ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=content,
                        spacing=5,
                        tight=True
                    ),
                    bgcolor=ft.Colors.GREY_800,
                    padding=12,
                    border_radius=ft.border_radius.all(12),
                    margin=ft.margin.only(right=80),
                    width=520,
                )
            ],
        )

    def bot_reply(self, user_text):
        typing = ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Text(
                        "TecminiAI está digitando...",
                        size=15,
                        italic=True,
                        color=ft.Colors.GREY_500,
                    ),
                    padding=10,
                )
            ],
        )

        # Adiciona "digitando..."
        self._schedule(lambda: self.show_typing(typing))

        # Chamada API
        try:
            resposta = API.responder_com_gemini(user_text)
        except Exception as e:
            resposta = f"Erro ao gerar resposta: {e}"

        # Mostra resposta
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
# TELA DE LOGIN + CADASTRO
# ---------------------------------------------------
def main(page: ft.Page):
<<<<<<< Updated upstream
    page.title = "TecminiAI"
    page.theme_mode = ft.ThemeMode.DARK

    # AGORA DO JEITO CERTO para Flet 0.24.1+
    page.window.width = 600
    page.window.height = 650

    page.padding = 20

=======
<<<<<<< HEAD
    # abrir fullscreen e estilo base (cores do primeiro código)
    page.window_full_screen = True
    page.padding = 20
    page.bgcolor = ft.Colors.BLACK
    page.theme_mode = ft.ThemeMode.DARK

    def carregar_login():
        page.clean()

        user_field = ft.TextField(label="Usuário", width=250, max_length=32)
        pass_field = ft.TextField(
            label="Senha", password=True, can_reveal_password=True, width=250, max_length=30
        )

        # permitir ENTER em usuário para focar senha
        user_field.on_submit = lambda e: pass_field.focus()
        pass_field.on_submit = lambda e: tentar_login(None)

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        def tentar_login(e):
            if validar_login(user_field.value.strip(), pass_field.value.strip()):
                carregar_chat()
            else:
                error_text.value = "Usuário ou senha incorretos."
                error_text.visible = True
                page.update()

        login_button = ft.ElevatedButton(
            "Entrar", width=250,color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700, on_click=tentar_login
        )

        cadastrar_link = ft.TextButton(
            "Cadastre-se",
            on_click=lambda _: carregar_cadastro(),
        )

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
            bgcolor=ft.Colors.BLACK,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=14,
                color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                offset=ft.Offset(0, 10),
            ),
        )

        page.add(ft.Container(content=login_box, expand=True, alignment=ft.alignment.center))

    def carregar_cadastro():
        page.clean()

        nome_field = ft.TextField(label="Nome completo", width=250, max_length=32)
        user_field = ft.TextField(label="Usuário", width=250, max_length=20)
        pass_field = ft.TextField(
            label="Senha", password=True, can_reveal_password=True, width=250, max_length=30
        )

        # MENSAGENS DE VALIDAÇÃO
        msg_nome = ft.Text("", color=ft.Colors.RED, visible=False, size=12)
        msg_user = ft.Text("", color=ft.Colors.RED, visible=False, size=12)
        msg_senha = ft.Text("", color=ft.Colors.RED, visible=False, size=12)

        # -------------------------
        # VALIDADORES ON-BLUR
        # -------------------------

        def validar_nome(e):
            texto = nome_field.value.strip()
            if len(texto) < 5:
                msg_nome.value = "Mínimo: 5 caracteres"
                msg_nome.visible = True
            else:
                msg_nome.visible = False
            page.update()

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

        # permitir ENTER seguindo fluxo
        nome_field.on_submit = lambda e: user_field.focus()
        user_field.on_submit = lambda e: pass_field.focus()
        pass_field.on_submit = lambda e: registrar(None)

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

            threading.Thread(target=lambda: (sleep(1), carregar_login()), daemon=True).start()

        cadastro_button = ft.ElevatedButton(
            "Cadastrar", color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700, width=250, on_click=registrar
        )

        voltar = ft.TextButton("Voltar", on_click=lambda _: carregar_login())

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
                    voltar
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=350,
            height=430,
            padding=30,
            border_radius=ft.border_radius.all(20),
            bgcolor=ft.Colors.BLACK,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=14,
                color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                offset=ft.Offset(0, 10),
            ),
        )

        page.add(ft.Container(content=box, expand=True, alignment=ft.alignment.center))

    def carregar_chat():
        page.clean()
        page.title = "TecminiAI"
        page.bgcolor = ft.Colors.BLACK

        def voltar():
            page.clean()
            page.appbar = None
            page.drawer = None
            carregar_login()

        drawer = ft.NavigationDrawer(
            controls=[
                ft.Container(
                    content=ft.TextButton("Limpar histórico", on_click=lambda _: app.limpar_historico()),
                    padding=ft.padding.only(top=20)
                ),
                ft.Container(
                    content=ft.TextButton("Sair", on_click=lambda _: voltar()),
                    padding=ft.padding.only(top=10)
                )
            ]
        )

        page.drawer = drawer

        menu_button = ft.IconButton(
            icon=ft.Icons.MENU,
            on_click=lambda _: abrir_menu(),
        )

        def abrir_menu():
            page.drawer.open = True
            page.update()

        global app
        app = ChatApp(page, drawer)

        page.appbar = ft.AppBar(
            leading=menu_button,
            title=ft.Text("TecminiAI", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
        )

        page.add(app)
        page.update()

    carregar_login()


ft.app(target=main)
=======
    page.title = "TecminiAI"
    page.theme_mode = ft.ThemeMode.DARK

    # AGORA DO JEITO CERTO para Flet 0.24.1+
    page.window.width = 600
    page.window.height = 650

    page.padding = 20

>>>>>>> Stashed changes
    app = ChatApp(page)
    page.add(app)


if __name__ == "__main__":
    ft.app(target=main)
>>>>>>> b33ee085821391d701de966a792de0da74d901b9
