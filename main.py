import sys
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# Tenta importar bibliotecas científicas integradas
try:
    import numpy as np
    NUMPY_DISPONIVEL = True
except ImportError:
    NUMPY_DISPONIVEL = False

class NexusScientificApp(App):
    def build(self):
        self.title = "NexusQuantum - Assistente Científico"
        
        # Layout principal vertical
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Cabeçalho / Título
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
        
        # Área de exibição de resultados (Rolável)
        self.output_label = Label(
            text="Sistema pronto.\nDigite uma expressão matemática ou comando analítico abaixo.",
            markup=True,
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.output_label)
        layout.add_widget(scroll)
        
        # Caixa de texto para entrada do usuário
        self.input_field = TextInput(
            text='',
            hint_text='Ex: np.mean([10, 20, 30, 40]) ou 2 + 2',
            size_hint_y=None,
            height=50,
            multiline=False
        )
        layout.add_widget(self.input_field)
        
        # Botão de Execução
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
            # Ambiente seguro de execução para testes matemáticos
            # Se o usuário digitar código python válido ou expressões com numpy (np)
            resultado_local = {}
            if NUMPY_DISPONIVEL:
                resultado_local['np'] = np
                
            # Executa a string de forma dinâmica
            if "=" not in comando and "print" not in comando:
                # Tenta avaliar como expressão direta se possível
                try:
                    res = eval(comando, {"__builtins__": None, "np": np if NUMPY_DISPONIVEL else None})
                    saida = f">> {comando}\nResultado: {res}"
                except Exception:
                    exec(f"res = {comando}", {"__builtins__": None, "np": np if NUMPY_DISPONIVEL else None}, resultado_local)
                    saida = f">> {comando}\nResultado: {resultado_local.get('res', 'Executado com sucesso.')}"
            else:
                exec(comando, {"__builtins__": None, "np": np if NUMPY_DISPONIVEL else None}, resultado_local)
                saida = f">> {comando}\nBloco executado com sucesso."
                
            self.output_label.text = saida + "\n\n" + self.output_label.text
            
        except Exception as e:
            erro_detalhado = traceback.format_exc()
            self.output_label.text = f">> Erro ao processar:\n{str(e)}\n\n" + self.output_label.text

if __name__ == '__main__':
    NexusScientificApp().run()
