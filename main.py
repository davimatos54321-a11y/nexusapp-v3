# main.py - Interface Gráfica Estável e Sem Sobreposição (Kivy)
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window

from cerebro import processar_comando_cerebro

try:
    import pyttsx3
    engine_voz = pyttsx3.init()
    engine_voz.setProperty('rate', 150)
except Exception:
    engine_voz = None

class SuperCerebroApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Cabeçalho / Título
        header = Label(
            text="[b]NEXUS[/b]",
            markup=True,
            size_hint_y=None,
            height=70,
            font_size=40,
            color=(0.1, 0.9, 1.0, 1)
        )
        root.add_widget(header)

        # Área de Rolagem do Chat com Fundo Organizado
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=20)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        root.add_widget(self.scroll)

        # Painel inferior (Microfone + Caixa de Texto + Enviar)
        input_layout = BoxLayout(size_hint_y=None, height=90, spacing=10)
        
        btn_mic = Button(
            text="🎙️ Falar",
            size_hint_x=None,
            width=120,
            background_color=(0.9, 0.4, 0.1, 1),
            color=(1, 1, 1, 1),
            font_size=24
        )
        btn_mic.bind(on_press=self.ouvir_microfone)
        input_layout.add_widget(btn_mic)

        self.text_input = TextInput(
            hint_text="Comando...",
            multiline=False,
            font_size=28,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )
        self.text_input.bind(on_text_validate=self.enviar_mensagem)
        input_layout.add_widget(self.text_input)

        btn_enviar = Button(
            text="Enviar",
            size_hint_x=None,
            width=120,
            background_color=(0.1, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=24
        )
        btn_enviar.bind(on_press=self.enviar_mensagem)
        input_layout.add_widget(btn_enviar)

        root.add_widget(input_layout)

        msg_inicial = "Nexus online e estabilizado!"
        Clock.schedule_once(lambda dt: self.adicionar_message_robo(msg_inicial), 0.6)
        self.falar_texto(msg_inicial)

        return root

    def ouvir_microfone(self, instance):
        self.adicionar_message_sistema("🎙️ Ouvindo...")
        texto_simulado_fala = "fazer análise da lote fácil"
        Clock.schedule_once(lambda dt: self.processar_fluxo(texto_simulado_fala), 1.0)

    def enviar_mensagem(self, instance):
        texto_usuario = self.text_input.text.strip()
        if not texto_usuario:
            return
        self.text_input.text = ""
        self.processar_fluxo(texto_usuario)

    def processar_fluxo(self, texto):
        self.adicionar_message_usuario(texto)
        resposta_cerebro = processar_comando_cerebro(texto)
        Clock.schedule_once(lambda dt: self.adicionar_message_robo(resposta_cerebro), 0.4)
        self.falar_texto(resposta_cerebro)

    def falar_texto(self, texto):
        if engine_voz:
            try:
                if engine_voz.isBusy():
                    engine_voz.stop()
                engine_voz.say(texto)
                engine_voz.runAndWait()
            except Exception:
                pass

    def adicionar_message_usuario(self, mensagem):
        lbl = MessageLabelUsuario(text=f"Você: {mensagem}")
        self.chat_layout.add_widget(lbl)
        self.scroll.scroll_y = 0

    def adicionar_message_robo(self, mensagem):
        lbl = MessageLabelRobo(text=f"Nexus:\n{mensagem}")
        self.chat_layout.add_widget(lbl)
        self.scroll.scroll_y = 0
        
    def adicionar_message_sistema(self, mensagem):
        lbl = MessageLabelSistema(text=f"Sistema: {mensagem}")
        self.chat_layout.add_widget(lbl)
        self.scroll.scroll_y = 0

class MessageLabelUsuario(Label):
    markup = True
    size_hint_y = None
    font_size = 32
    color = (0.9, 0.9, 0.9, 1)
    halign = 'left'
    valign = 'middle'
    padding = (15, 15)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(width=self.update_text_size)

    def update_text_size(self, *args):
        self.text_size = (self.width - 30, None)
        self.texture_update()
        self.height = self.texture_size[1] + 40

class MessageLabelRobo(Label):
    markup = True
    size_hint_y = None
    font_size = 34  # Letras grandes e legíveis para os números
    color = (0.2, 1, 0.6, 1)
    halign = 'left'
    valign = 'middle'
    padding = (15, 15)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(width=self.update_text_size)

    def update_text_size(self, *args):
        self.text_size = (self.width - 30, None)
        self.texture_update()
        self.height = self.texture_size[1] + 40

class MessageLabelSistema(Label):
    markup = True
    size_hint_y = None
    font_size = 28
    color = (1, 0.6, 0, 1)
    halign = 'center'
    valign = 'middle'
    padding = (15, 15)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(width=self.update_text_size)

    def update_text_size(self, *args):
        self.text_size = (self.width - 30, None)
        self.texture_update()
        self.height = self.texture_size[1] + 40

if __name__ == '__main__':
    Window.clearcolor = (0.05, 0.05, 0.1, 1)
    SuperCerebroApp().run()
