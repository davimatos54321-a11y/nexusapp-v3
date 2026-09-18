import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle

class NexusQuantumApp(App):
    def build(self):
        self.title = "NexusQuantum - Advanced Scientific Assistant"
        
        # Layout principal com espaçamento profissional
        root_layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        
        # Fundo Quântico (Deep Tech Blue)
        with root_layout.canvas.before:
            Color(0.02, 0.05, 0.12, 1)
            self.bg_rect = Rectangle(size=root_layout.size, pos=root_layout.pos)
        root_layout.bind(size=self._update_bg, pos=self._update_bg)
        
        # Cabeçalho Tecnológico Avançado
        header = Label(
            text="[b][color=00F0FF]NEXUS QUANTUM AI[/color][/b]\n[size=11][color=8A99AD]KERNEL: v2.7 | STATUS: ONLINE ⚡[/color][/size]",
            markup=True,
            size_hint_y=None,
            height=60,
            halign='center',
            valign='middle'
        )
        header.bind(size=header.setter('text_size'))
        root_layout.add_widget(header)
        
        # Área de Histórico / Terminal Quântico Rolável
        self.output_label = Label(
            text="[color=00F0FF]>> [System]:[/color] Núcleo quântico inicializado com sucesso.\n[color=8A99AD]Selecione um atalho abaixo ou digite o seu comando.[/color]",
            markup=True,
            size_hint_y=None,
            halign='left',
            valign='top',
            color=(0.9, 0.95, 1, 1)
        )
        self.output_label.bind(
            width=lambda *x: setattr(self.output_label, 'text_size', (self.output_label.width - 20, None)),
            texture_size=lambda *x: setattr(self.output_label, 'height', max(x[0][1] + 20, 200))
        )
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.output_label)
        root_layout.add_widget(scroll)
        
        # Painel de Botões de Acesso Rápido (Estilo Neon / Organizado)
        control_panel = BoxLayout(orientation='vertical', size_hint_y=None, height=90, spacing=6)
        
        row1 = GridLayout(cols=3, spacing=6, size_hint_y=None, height=42)
        
        btn_clear = Button(text='[color=FF5555]🗑 Limpar[/color]', markup=True, background_color=(0.12, 0.18, 0.3, 1))
        btn_clear.bind(on_press=self.limpar_ecra)
        
        btn_aposta = Button(text='[color=00FF99]⚽ Apostas EV[/color]', markup=True, background_color=(0.08, 0.25, 0.2, 1))
        btn_aposta.bind(on_press=lambda x: self.inserir_atalho("aposta odds=1.95 prob=0.55"))
        
        btn_calc = Button(text='[color=00F0FF]🔢 Cálculo[/color]', markup=True, background_color=(0.08, 0.2, 0.35, 1))
        btn_calc.bind(on_press=lambda x: self.inserir_atalho("50 + 50 * 2"))
        
        row1.add_widget(btn_clear)
        row1.add_widget(btn_aposta)
        row1.add_widget(btn_calc)
        
        row2 = GridLayout(cols=2, spacing=6, size_hint_y=None, height=42)
        
        btn_estatistica = Button(text='[color=70A5FF]📊 Média Aritmética[/color]', markup=True, background_color=(0.1, 0.2, 0.4, 1))
        btn_estatistica.bind(on_press=lambda x: self.inserir_atalho("media(10, 20, 30, 40)"))
        
        btn_ajuda = Button(text='[color=FFD700]💡 Ajuda[/color]', markup=True, background_color=(0.25, 0.2, 0.08, 1))
        btn_ajuda.bind(on_press=lambda x: self.inserir_atalho("ajuda"))
        
        row2.add_widget(btn_estatistica)
        row2.add_widget(btn_ajuda)
        
        control_panel.add_widget(row1)
        control_panel.add_widget(row2)
        root_layout.add_widget(control_panel)
        
        # Caixa de Texto de Entrada
        self.input_field = TextInput(
            text='',
            hint_text='Digite um cálculo ou aposta...',
            size_hint_y=None,
            height=48,
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
            height=52,
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
        self.output_label.text = "[color=00F0FF]>> [System]:[/color] Terminal limpo. Pronto."
        self.input_field.text = ""

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
                f"• Probabilidade: {prob * 100}%\n"
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
                    "1. Contas diretas (ex: 50 + 50)\n"
                    "2. Apostas (ex: aposta odds=1.90 prob=0.55)\n"
                    "3. Média (ex: media(10, 20, 30))"
                )
            elif comando.lower().startswith("aposta"):
                saida = self.calcular_aposta(comando)
            elif comando.lower().startswith("media"):
                # Cálculo de média nativo em Python puro
                nums_str = comando[comando.find("(")+1:comando.find(")")]
                nums = [float(n.strip()) for n in nums_str.split(",")]
                res = sum(nums) / len(nums)
                saida = f"[color=00F0FF]>> Input:[/color] {comando}\n[color=00FF99]Média Calculada:[/color] {res}"
            else:
                res = eval(comando, {"__builtins__": None}, {})
                saida = f"[color=00F0FF]>> Input:[/color] {comando}\n[color=00FF99]Resultado:[/color] {res}"
                
            self.output_label.text = saida + "\n\n" + "-"*30 + "\n\n" + self.output_label.text
            self.input_field.text = ""
            
        except Exception as e:
            saida = f"[color=FF5555]>> [Erro]:[/color] Expressão inválida ({str(e)}). Use formato numérico correto."
            self.output_label.text = saida + "\n\n" + "-"*30 + "\n\n" + self.output_label.text

if __name__ == '__main__':
    NexusQuantumApp().run()
