import sys
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle

# Importações protegidas para evitar crash no arranque do Android
try:
    import numpy as np
    NUMPY_DISPONIVEL = True
except Exception:
    NUMPY_DISPONIVEL = False

# Importação de voz segura
STT_DISPONIVEL = False
try:
    from plyer import stt
    STT_DISPONIVEL = True
except Exception:
    pass

class NexusQuantumApp(App):
    def build(self):
        self.title = "NexusQuantum - Advanced Scientific Assistant"
        
        # Layout principal com margens limpas
        root_layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        # Fundo quântico profissional (Deep Tech Blue)
        with root_layout.canvas.before:
            Color(0.02, 0.05, 0.10, 1)
            self.bg_rect = Rectangle(size=root_layout.size, pos=root_layout.pos)
        root_layout.bind(size=self._update_bg, pos=self._update_bg)
        
        # Cabeçalho Tecnológico Avançado
        engine_status = "ONLINE ⚡" if NUMPY_DISPONIVEL else "LOCAL ⚠️"
        header_text = (
            f"[b][color=00F0FF]NEXUS QUANTUM AI[/color][/b]\n"
            f"[size=11][color=8A99AD]KERNEL: v2.6 | ENGINE: {engine_status}[/color][/size]"
        )
        header = Label(
            text=header_text,
            markup=True,
            size_hint_y=None,
            height=65,
            halign='center',
            valign='middle'
        )
        header.bind(size=header.setter('text_size'))
        root_layout.add_widget(header)
        
        # Área de Histórico / Terminal Quântico Rolável
        self.output_label = Label(
            text="[color=00F0FF]>> [System]:[/color] Núcleo quântico inicializado com sucesso.\n[color=8A99AD]Selecione um módulo abaixo ou insira um comando.[/color]",
            markup=True,
            size_hint_y=None,
            halign='left',
            valign='top',
            color=(0.9, 0.95, 1, 1)
        )
        self.output_label.bind(
            width=lambda *x: setattr(self.output_label, 'text_size', (self.output_label.width - 25, None)),
            texture_size=lambda *x: setattr(self.output_label, 'height', max(x[0][1] + 25, 220))
        )
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.output_label)
        root_layout.add_widget(scroll)
        
        # Painel de Botões de Acesso Rápido
        control_panel = BoxLayout(orientation='vertical', size_hint_y=None, height=95, spacing=8)
        
        # Linha 1 de Atalhos
        row1 = GridLayout(cols=3, spacing=8, size_hint_y=None, height=43)
        
        btn_clear = Button(text='[color=FF5555]🗑 Limpar[/color]', markup=True, background_color=(0.12, 0.18, 0.3, 1))
        btn_clear.bind(on_press=self.limpar_ecra)
        
        btn_aposta = Button(text='[color=00FF99]⚽ Apostas EV[/color]', markup=True, background_color=(0.08, 0.25, 0.2, 1))
        btn_aposta.bind(on_press=lambda x: self.inserir_atalho("aposta odds=1.95 prob=0.55"))
        
        btn_voz = Button(text='[color=00F0FF]🎙 Falar Voz[/color]', markup=True, background_color=(0.08, 0.2, 0.35, 1))
        btn_voz.bind(on_press=self.ouvir_voz)
        
        row1.add_widget(btn_clear)
        row1.add_widget(btn_aposta)
        row1.add_widget(btn_voz)
        
        # Linha 2 de Atalhos
        row2 = GridLayout(cols=2, spacing=8, size_hint_y=None, height=43)
        
        btn_numpy = Button(text='[color=70A5FF]📊 NumPy Estatística[/color]', markup=True, background_color=(0.1, 0.2, 0.4, 1))
        btn_numpy.bind(on_press=lambda x: self.inserir_atalho("np.mean([15, 25, 35, 45])"))
        
        btn_ajuda = Button(text='[color=FFD700]💡 Info / Ajuda[/color]', markup=True, background_color=(0.25, 0.2, 0.08, 1))
        btn_ajuda.bind(on_press=lambda x: self.inserir_atalho("ajuda"))
        
        row2.add_widget(btn_numpy)
        row2.add_widget(btn_ajuda)
        
        control_panel.add_widget(row1)
        control_panel.add_widget(row2)
        root_layout.add_widget(control_panel)
        
        # Caixa de Texto de Entrada
        self.input_field = TextInput(
            text='',
            hint_text='Digite um comando, cálculo ou aposta...',
            size_hint_y=None,
            height=50,
            multiline=False,
            background_color=(0.05, 0.11, 0.2, 1),
            foreground_color=(0.9, 0.95, 1, 1),
            hint_text_color=(0.4, 0.55, 0.7, 1)
        )
        root_layout.add_widget(self.input_field)
        
        # Botão de Execução Principal
        btn_executar = Button(
            text='[b]PROCESSAR COMANDO QUÂNTICO[/b]',
            markup=True,
            size_hint_y=None,
            height=55,
            background_color=(0.0, 0.6, 0.9, 1)
        )
        btn_executar.bind(on_press=self.executar_comando)
        root_layout.add_widget(btn_executar)
        
        return root_layout

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def inserir_atalho(self, texto):
        self.input_field.text = texto

    def limpar_ecra(self, instance):
        self.output_label.text = "[color=00F0FF]>> [System]:[/color] Terminal limpo. Pronto para nova operação."
        self.input_field.text = ""

    def ouvir_voz(self, instance):
        if STT_DISPONIVEL:
            try:
                stt.speak = False
                stt.start(listener=self.resultado_voz)
                self.output_label.text = "[color=FFD700]>> [Voice]:[/color] Escutando microfone... Fale agora.\n\n" + self.output_label.text
            except Exception as e:
                self.output_label.text = f"[color=FF5555]>> [Error]:[/color] Falha no microfone: {str(e)}\n\n" + self.output_label.text
        else:
            self.output_label.text = "[color=FF5555]>> [System]:[/color] Módulo de reconhecimento de voz indisponível neste modo.\n\n" + self.output_label.text

    def resultado_voz(self, resultat):
        if resultat:
            self.input_field.text = str(resultat)
            self.output_label.text = f"[color=00FF99]>> [Voice Input]:[/color] {resultat}\n\n" + self.output_label.text

    def calcular_aposta(self, texto):
        try:
            partes = texto.lower().replace("aposta", "").strip().split()
            odds = 1.95
            prob = 0.50
            for p in partes:
                if "odds=" in p:
                    odds = float(p.split("=")[1])
                elif "prob=" in p:
                    prob = float(p.split("=")[1])
            
            ev = (odds * prob) - 1
            lucro_pct = ev * 100
            status = "[color=00FF99]APOSTA COM VALOR (EV POSITIVO 🚀)[/color]" if ev > 0 else "[color=FF5555]EV NEGATIVO (EVITAR ⚠️)[/color]"
            
            return (
                f"[color=00F0FF]>> [Quantum Betting Analysis]:[/color]\n"
                f"• Odds: {odds}\n"
                f"• Probabilidade Real: {prob * 100}%\n"
                f"• Retorno Esperado (EV): {lucro_pct:.2f}%\n"
                f"• Conclusão: {status}"
            )
        except Exception:
            return "[color=FF5555]>> [Error]: Sintaxe inválida. Use: aposta odds=1.90 prob=0.55[/color]"

    def executar_comando(self, instance):
        comando = self.input_field.text.strip()
        if not comando:
            return
        
        saida = ""
        try:
            if comando.lower() == "ajuda":
                saida = (
                    "[color=00F0FF]>> [Nexus Help]:[/color]\n"
                    "1. Cálculo matemático direto (ex: 50 + 50)\n"
                    "2. Análise de apostas (ex: aposta odds=1.90 prob=0.55)\n"
                    "3. Use o botão 'Falar Voz' se suportado."
                )
            elif comando.lower().startswith("aposta"):
                saida = self.calcular_aposta(comando)
            else:
                contexto = {"np": np if NUMPY_DISPONIVEL else None}
                try:
                    res = eval(comando, {"__builtins__": None}, contexto)
                    saida = f"[color=00F0FF]>> Input:[/color] {comando}\n[color=00FF99]Result:[/color] {res}"
                except Exception:
                    resultado_local = {}
                    exec(comando, {"__builtins__": None}, {**contexto, **resultado_local})
                    saida = f"[color=00F0FF]>> Input:[/color] {comando}\n[color=00FF99]Status:[/color] Executado com sucesso."
                
            self.output_label.text = saida + "\n\n" + "="*35 + "\n\n" + self.output_label.text
            self.input_field.text = ""
            
        except SyntaxError:
            saida = f"[color=FFD700]>> [Quantum AI Assistant]:[/color] Comando '{comando}' registado. Para operações numéricas use '50 + 50' ou 'aposta odds=1.90 prob=0.5'."
            self.output_label.text = saida + "\n\n" + "="*35 + "\n\n" + self.output_label.text
        except Exception as e:
            saida = f"[color=FF5555]>> [Kernel Error]:[/color] {str(e)}"
            self.output_label.text = saida + "\n\n" + "="*35 + "\n\n" + self.output_label.text

if __name__ == '__main__':
    NexusQuantumApp().run()
