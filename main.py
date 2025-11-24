import re
import threading

import flet as ft

import API  # sua API com perguntar_escola()


# -------------------------
# Função segura para chamadas de UI (compatível com várias versões)
# -------------------------
def get_scheduler(page: ft.Page):
    if hasattr(page, "call_from_thread"):
        return page.call_from_thread
    elif hasattr(page, "run_on_main_thread"):
        return page.run_on_main_thread
    elif hasattr(page, "invoke_later"):
        return page.invoke_later
    else:
        return lambda fn: fn()


# -------------------------
# Chat App
# -------------------------
class ChatApp(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.expand = True
        self.spacing = 10

        # scheduler compatível
        self._schedule = get_scheduler(page)

        # Área do chat
        self.chat_area = ft.ListView(
            expand=True,
            auto_scroll=True,
            spacing=10,
        )

        # Campo de texto
        self.new_message = ft.TextField(
            hint_text="Digite aqui...",
            expand=True,
            autofocus=True,
            on_submit=self.send_message,
        )

        # Botão enviar — CORRIGIDO
        self.send_button = ft.FloatingActionButton(
            icon=ft.Icons.SEND,
            bgcolor=ft.Colors.BLUE_800,
            on_click=self.send_message,
        )

        # Barra inferior
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

    # -------------------------
    # Envio de mensagem
    # -------------------------
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

    # -------------------------
    # Bot Reply (thread)
    # -------------------------
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


# -------------------------
# APP
# -------------------------
def main(page: ft.Page):
    page.title = "TecminiAI"
    page.theme_mode = ft.ThemeMode.DARK

    # AGORA DO JEITO CERTO para Flet 0.24.1+
    page.window.width = 600
    page.window.height = 650

    page.padding = 20

    app = ChatApp(page)
    page.add(app)


if __name__ == "__main__":
    ft.app(target=main)
