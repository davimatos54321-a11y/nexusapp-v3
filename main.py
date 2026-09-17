import os
from kivy.app import App
from kivy.uix.label import Label

# Pega a chave de forma segura (seja no celular ou no GitHub)
api_key = os.environ.get('IBM_API_KEY', 'sua_chave_padrao_se_necessario')

class NexusApp(App):
    def build(self):
        return Label(text='Nexus App Funcionando com Sucesso!')

if __name__ == '__main__':
    NexusApp().run()
