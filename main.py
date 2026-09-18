import sys
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Tenta importar o NumPy de forma robusta no Android
try:
    import numpy as np
    NUMPY_DISPONIVEL = True
except ImportError:
    NUMPY_DISPONIVEL = False

class NexusScientificApp(App):
    def build(self):
        self.title = "NexusQuantum - Assistente Científico"
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Cabeçalho indicando o estado real do NumPy
        status_numpy = "NumPy Ativo" if NUMPY_DISPONIVEL else "NumPy Indisponível"
        header = Label(
            text=f"[b]NexusQuantum Mobile[/b]\nEngine: {status_numpy}",
            markup=True,
            size_hint_y=None,
            height=60,
            halign='center',
            valign='middle'
        )
        header.bind(size=header.setter('text_size'))
        layout.add_widget(header)
        
        # Área de exibição de resultados rolável
        self.output_label = Label(
            text="Sistema pronto.\nDigite uma expressão matemática (ex: 50 + 50) ou comando analítico.",
            markup=True,
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.output_label)
        layout.add_widget(scroll)
        
        # Caixa de texto para comandos
        self.input_field = TextInput(
            text='',
            hint_text='Ex: 50 + 50 ou np.mean([10, 20, 30])',
            size_hint_y=None,
            height=50,
            multiline=False
        )
        layout.add_widget(self.input_field)
        
        # Botão de processamento
        btn_executar = Button(
            text='Processar Cálculo',
            size_hint_y=None,
            height=60,
            background_color=(0.1, 0.5, 0.8, 1)
        )
        btn_executar.bind(on_press=self.executar_comando)
        layout.add_widget(btn_executar)
        
        return layout

    def executar_comando(self, instance):
        comando = self.input_field.text.strip()
        if not comando:
            return
        
        try:
            # Contexto seguro com suporte ao NumPy se disponível
            contexto = {"np": np if NUMPY_DISPONIVEL else None}
            
            # Tenta avaliar como expressão matemática direta
            try:
                res = eval(comando, {"__builtins__": None}, contexto)
                saida = f">> {comando}\nResultado: {res}"
            except Exception:
                # Se for um bloco de comandos multi-linha ou atribuições
                resultado_local = {}
                exec(comando, {"__builtins__": None}, {**contexto, **resultado_local})
                saida = f">> {comando}\nComando executado com sucesso."
                
            self.output_label.text = saida + "\n\n" + self.output_label.text
            
        except SyntaxError:
            # Tratamento inteligente e limpo caso digite texto livre / linguagem natural
            saida = f">> {comando}\n[Assistente]: Compreendido. Para cálculos matemáticos, utilize expressões diretas como '50 + 50'."
            self.output_label.text = saida + "\n\n" + self.output_label.text
        except Exception as e:
            saida = f">> {comando}\nErro: {str(e)}"
            self.output_label.text = saida + "\n\n" + self.output_label.text

if __name__ == '__main__':
    NexusScientificApp().run()
