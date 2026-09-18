import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import requests

class NexusApp(App):
    def build(self):
        # Cria a tela base (Quantum Blue, etc)
        layout = BoxLayout(orientation='vertical', padding=20)
        
        # Um texto para mostrar o resultado
        self.resultado = Label(text="Aguardando conexão...", color=(1, 1, 1, 1))
        layout.add_widget(self.resultado)
        
        # O botão que VAI acionar a API apenas quando clicado
        btn = Button(text="Buscar Jogos de Hoje", size_hint=(1, 0.2))
        btn.bind(on_press=self.buscar_jogos) # Conecta o botão à função
        layout.add_widget(btn)
        
        return layout

    # A função da API fica isolada aqui!
    def buscar_jogos(self, instance):
        self.resultado.text = "Conectando à API-Football..."
        
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        queries = {"date": "2026-09-18"}
        headers = {
            "X-RapidAPI-Key": "Cdbcab0cd3msh246b01115afa4b9p1ceb17jsn86f157fb5080",
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
        }
        
        try:
            response = requests.get(url, headers=headers, params=queries)
            if response.status_code == 200:
                dados = response.json()
                partidas = dados.get("response", [])
                if len(partidas) > 0:
                    exemplo = partidas[0]
                    home = exemplo["teams"]["home"]["name"]
                    away = exemplo["teams"]["away"]["name"]
                    self.resultado.text = f"Sucesso! Jogo em destaque:\n{home} vs {away}"
                else:
                    self.resultado.text = "Sem jogos para hoje."
            else:
                self.resultado.text = "Erro de conexão com o servidor."
        except Exception as e:
            self.resultado.text = f"Erro ao conectar: {e}"

if __name__ == '__main__':
    NexusApp().run()
