# main.py - Interface Gráfica, Chat, Voz e Microfone (Kivy)
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock

# Importa o motor inteligente de cálculo (do arquivo cerebro.py)
from cerebro import processar_comando_cerebro

# Tenta importar a biblioteca de voz (ignora se não estiver no PC)
try:
    import pyttsx3
    engine_voz = pyttsx3.init()
    # Ajusta a velocidade da fala (opcional)
    engine_voz.setProperty('rate', 150)
except Exception:
    engine_voz = None

class SuperCerebroApp(App):
    def build(self):
        # -- CONFIGURAÇÃO VISUAL DA INTERFACE --
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Fundo da tela (Cor escura moderna)
        self.cor_fundo = (0.05, 0.05, 0.1, 1)
        
        # Cabeçalho / Título
        header = Label(
            text="🤖 [b]SUPER-CÉREBRO V44.3[/b] - Central Ativa",
            markup=True,
            size_hint_y=None,
            height=50,
            font_size=18,
            color=(0.1, 0.9, 1.0, 1) # Tom neon
        )
        root.add_widget(header)

        # Área de Rolagem (Histórico do chat)
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        root.add_widget(self.scroll)

        # Painel inferior (Microfone + Caixa de Texto + Enviar)
        input_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        
        # Botão do Microfone (para falar com o robô)
        btn_mic = Button(
            text="🎙️ Falar",
            size_hint_x=None,
            width=80,
            background_color=(0.9, 0.4, 0.1, 1), # Laranja destaque
            color=(1, 1, 1, 1)
        )
        btn_mic.bind(on_press=self.ouvir_microfone)
        input_layout.add_widget(btn_mic)

        # Caixa de texto principal
        self.text_input = TextInput(
            hint_text="Digite seu comando ou pergunta...",
            multiline=False,
            font_size=16,
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )
        # Permite enviar pressionando Enter no teclado virtual
        self.text_input.bind(on_text_validate=self.enviar_mensagem)
        input_layout.add_widget(self.text_input)

        # Botão de Enviar (texto)
        btn_enviar = Button(
            text="Enviar",
            size_hint_x=None,
            width=90,
            background_color=(0.1, 0.6, 0.9, 1), # Azul destaque
            color=(1, 1, 1, 1)
        )
        btn_enviar.bind(on_press=self.enviar_mensagem)
        input_layout.add_widget(btn_enviar)

        root.add_widget(input_layout)

        # Mensagem inicial de boas-vindas
        msg_inicial = "Olá, Adailton! Central de bolso online e pronta. O microfone está ativado. O que vamos calcular hoje?"
        Clock.schedule_once(lambda dt: self.adicionar_message_robo(msg_inicial), 0.6)
        self.falar_texto(msg_inicial)

        return root

    def ouvir_microfone(self, instance):
        """Ação ao clicar no microfone (chama a API de voz nativa do Android)"""
        self.adicionar_message_sistema("🎙️ Ouvindo o microfone... (Aguardando comando de voz)")
        
        # NOTA IMPORTANTE: No Android compilado pelo Buildozer, este gatilho
        # chamará a API de reconhecimento de fala do sistema operacional.
        # Por enquanto, simulamos o resultado da escuta para testes:
        
        texto_simulado_fala = "fazer análise da lote fácil" # Exemplo de fala
        Clock.schedule_once(lambda dt: self.processar_fluxo(texto_simulado_fala), 1.0)

    def enviar_mensagem(self, instance):
        """Ação ao clicar em Enviar (lê o texto da caixa)"""
        texto_usuario = self.text_input.text.strip()
        if not texto_usuario:
            return
        self.text_input.text = ""
        self.processar_fluxo(texto_usuario)

    def processar_fluxo(self, texto):
        """Fluxo comum: mostra o que disseste e chama o cérebro"""
        # 1. Mostra a tua mensagem na tela
        self.adicionar_message_usuario(texto)
        
        # 2. Chama o motor principal (cerebro.py) e obtém a resposta
        resposta_cerebro = processar_comando_cerebro(texto)
        
        # 3. Mostra a resposta do robô na tela e fala o texto
        Clock.schedule_once(lambda dt: self.adicionar_message_robo(resposta_cerebro), 0.4)
        self.falar_texto(resposta_cerebro)

    def falar_texto(self, texto):
        """Faz o aplicativo falar a resposta em voz alta (TTS)"""
        if engine_voz:
            try:
                # Para a fala anterior se estiver a falar
                if engine_voz.isBusy():
                    engine_voz.stop()
                engine_voz.say(texto)
                engine_voz.runAndWait()
            except Exception:
                pass

    # -- Funções auxiliares de estilo --
    def adicionar_message_usuario(self, mensagem):
        lbl = MessageLabelUsuario(text=f"[b]Você:[/b] {mensagem}")
        self.chat_layout.add_widget(lbl)
        self.scroll.scroll_y = 0

    def adicionar_message_robo(self, mensagem):
        lbl = MessageLabelRobo(text=f"[b]Super-Cérebro:[/b] {mensagem}")
        self.chat_layout.add_widget(lbl)
        self.scroll.scroll_y = 0
        
    def adicionar_message_sistema(self, mensagem):
        lbl = MessageLabelSistema(text=f"[b]Sistema:[/b] {mensagem}")
        self.chat_layout.add_widget(lbl)
        self.scroll.scroll_y = 0

class MessageLabelUsuario(Label):
    markup = True
    size_hint_y = None
    font_size = 15
    color = (0.9, 0.9, 0.9, 1) # Quase branco
    halign = 'left'
    valign = 'middle'
    padding = (10, 10)
    def on_size(self, *args):
        self.text_size = (self.width - 20, None)
        self.texture_update()
        self.height = self.texture_size[1] + 20

class MessageLabelRobo(Label):
    markup = True
    size_hint_y = None
    font_size = 15
    color = (0.2, 1, 0.6, 1) # Verde neon
    halign = 'left'
    valign = 'middle'
    padding = (10, 10)
    def on_size(self, *args):
        self.text_size = (self.width - 20, None)
        self.texture_update()
        self.height = self.texture_size[1] + 20

class MessageLabelSistema(Label):
    markup = True
    size_hint_y = None
    font_size = 14
    color = (1, 0.6, 0, 1) # Laranja/Amarelo de aviso
    halign = 'center'
    valign = 'middle'
    padding = (10, 10)
    def on_size(self, *args):
        self.text_size = (self.width - 20, None)
        self.texture_update()
        self.height = self.texture_size[1] + 20

if __name__ == '__main__':
    # Define a cor de fundo da janela da aplicação
    from kivy.core.window import Window
    Window.clearcolor = (0.05, 0.05, 0.1, 1)
    SuperCerebroApp().run()
