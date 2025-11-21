import flet as ft
import threading
import API  # sua API com perguntar_escola()


# -------------------------
# Função segura para chamadas de UI
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
    def __init__(self, page, drawer):
        super().__init__()
        self.page = page
        self.drawer = drawer
        self.expand = True
        self.spacing = 10

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

        # Botão enviar
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
    # Limpar histórico
    # -------------------------
    def limpar_historico(self):
        self.chat_area.controls.clear()
        self.page.update()

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

    def create_user_bubble(self, text):
        return ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.Container(
                    content=ft.Text(text, size=16, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.BLUE_800,
                    padding=10,
                    border_radius=ft.border_radius.all(12),
                    margin=ft.margin.only(left=80),
                    width=min(520, max(120, len(text) * 8)),
                )
            ],
        )

    def create_bot_bubble(self, text):
        return ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Text(text, size=16, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREY_800,
                    padding=10,
                    border_radius=ft.border_radius.all(12),
                    margin=ft.margin.only(right=80),
                    width=min(520, max(120, len(text) * 8)),
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

        self._schedule(lambda: self.show_typing(typing))

        try:
            resposta = API.responder_com_gemini(user_text)
        except Exception as e:
            resposta = f"Erro ao gerar resposta: {e}"

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
    page.window_full_screen = True
    page.title = "TecminiAI - Login"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.bgcolor = ft.Colors.BLACK

    # Campos de login
    user_field = ft.TextField(
        label="Usuário",
        width=250,
        on_submit=lambda e: pass_field.focus(),  # ENTER → vai para senha
    )

    pass_field = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        width=250,
         # ENTER → tenta login
    )

    error_text = ft.Text(
        "",
        color=ft.Colors.RED,
        size=14,
        visible=False,
    )

    def tentar_login(e):
        if user_field.value == "admin" and pass_field.value == "admin":
            carregar_chat()
        else:
            error_text.value = "Usuário ou senha incorretos."
            error_text.visible = True
            page.update()

    pass_field = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        width=250,
        on_submit=tentar_login,  # ENTER → tenta login
    )


    login_button = ft.ElevatedButton(
        "Entrar",
        width=250,
        bgcolor=ft.Colors.BLUE_700,
        color=ft.Colors.WHITE,
        on_click=tentar_login,
    )

    # QUADRADO FLUTUANTE
    login_box = ft.Container(
        content=ft.Column(
            [
                ft.Text("Login", size=22, weight=ft.FontWeight.BOLD),
                user_field,
                pass_field,
                error_text,
                login_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        width=350,
        height=350,
        padding=30,
        bgcolor=ft.Colors.with_opacity(1, ft.Colors.BLACK),
        border_radius=20,
        alignment=ft.alignment.center,

        # >>> AQUI: SOMBRA BRANCA <<<
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=14,
            color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
            offset=ft.Offset(0, 10),
        ),
    )

    # Layout centralizado
    wrapper = ft.Container(
        content=login_box,
        expand=True,
        alignment=ft.alignment.center,
    )

    page.add(wrapper)

    # ----------------------------
    # FUNÇÃO PARA CARREGAR O CHAT
    # ----------------------------
    def carregar_chat():
        page.clean()
        page.title = "TecminiAI"
        page.bgcolor = ft.Colors.BLACK

        def voltar_para_login():
            page.clean()
            page.appbar = None
            page.drawer = None
            page.update()
            main(page)

        drawer = ft.NavigationDrawer(
            controls=[
                ft.Container(
                    content=ft.TextButton(
                        "Limpar histórico",
                        on_click=lambda _: app.limpar_historico(),
                    ),
                    padding=ft.padding.only(top=20)
                ),

                ft.Container(
                    content=ft.TextButton(
                        "Sair",
                        on_click=lambda _: voltar_para_login(),
                    ),
                    padding=ft.padding.only(top=10)
                )
            ],
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
            title=ft.Text("TecminiAI"),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
        )

        page.add(app)
        page.update()



def open_drawer(page):
    page.drawer.open = True
    page.update()


def handle_drawer_select(e, app):
    if e.control.selected_index == 0:
        app.limpar_historico()

    # fechar drawer
    e.control.open = False
    e.control.page.update()


if __name__ == "__main__":
    ft.app(target=main)
