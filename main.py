import threading
import time
import sqlite3
import random
import math
from dataclasses import dataclass
from typing import List, Tuple

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line

# --- 1. CONTRATOS DE DADOS E VALIDAÇÃO CIENTÍFICA ---
@dataclass(frozen=True)
class Partida:
    home_team: str
    away_team: str
    competition: str
    odd_home: float
    odd_draw: float
    odd_away: float

    def __post_init__(self):
        if self.odd_home <= 1.0 or self.odd_draw <= 1.0 or self.odd_away <= 1.0:
            raise ValueError("Violação de Contrato: As odds devem ser estritamente superiores a 1.0")

@dataclass
class BilheteSimulacao:
    partida: str
    mercado: str
    odd_selecionada: float
    probabilidade_estimada: float
    stake_sugerida: float
    retorno_potencial: float


# --- 2. PERSISTÊNCIA ATÔMICA (SQLite) ---
class NexusDatabase:
    def __init__(self, db_path="nexus_quant.db"):
        self.db_path = db_path
        self._inicializar_banco()

    def _inicializar_banco(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_bilhetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                partida TEXT,
                mercado TEXT,
                odd REAL,
                probabilidade REAL,
                stake REAL,
                retorno REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cofre_estado (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def salvar_bilhete(self, b: BilheteSimulacao):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_bilhetes (data, partida, mercado, odd, probabilidade, stake, retorno)
            VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)
        ''', (b.partida, b.mercado, b.odd_selecionada, b.probabilidade_estimada, b.stake_sugerida, b.retorno_potencial))
        conn.commit()
        conn.close()

    def obter_historico(self) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data, partida, mercado, odd, retorno FROM historico_bilhetes ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        return rows


# --- 3. RESILIÊNCIA DE REDE (BACKOFF EXPONENCIAL) ---
def chamada_api_com_retry(func, max_tentativas=3, base_delay=1.0):
    tentativa = 0
    while tentativa < max_tentativas:
        try:
            return func()
        except Exception as e:
            tentativa += 1
            if tentativa == max_tentativas:
                raise RuntimeError(f"Falha crítica na API após {max_tentativas} tentativas: {e}")
            delay = base_delay * (2 ** (tentativa - 1)) + random.uniform(0, 0.5)
            time.sleep(delay)


# --- 4. WIDGET GRÁFICO DE DISTRIBUIÇÃO ESTATÍSTICA (Canvas Kivy) ---
class MonteCarloGraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resultados = []
        self.bind(pos=self.atualizar_canvas, size=self.atualizar_canvas)

    def atualizar_dados(self, novos_resultados: List[float]):
        self.resultados = novos_resultados
        self.atualizar_canvas()

    def atualizar_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Fundo do painel gráfico
            Color(0.05, 0.06, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Moldura cibernética
            Color(0.0, 0.8, 0.6, 0.5)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

            if not self.resultados:
                return

            # Agrupamento estatístico em 10 bins
            num_bins = 10
            bins = [0] * num_bins
            for val in self.resultados:
                idx = min(int(val * num_bins), num_bins - 1)
                bins[idx] += 1

            max_freq = max(bins) if max(bins) > 0 else 1
            w_barra = self.width / num_bins
            
            for i, freq in enumerate(bins):
                h_barra = (freq / max_freq) * (self.height - 30)
                x_barra = self.x + (i * w_barra) + 2
                y_barra = self.y + 15
                
                # Barras de densidade de probabilidade
                Color(0.0, 0.7, 0.5, 0.8)
                Rectangle(pos=(x_barra, y_barra), size=(w_barra - 4, h_barra))


# --- 5. INTERFACE DE USUÁRIO (KIVY SCREEN) ---
class DashboardScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        # Cabeçalho Principal
        lbl_titulo = Label(
            text="[b]NEXUS QUANTUM ENGINE - PRO V2[/b]",
            markup=True,
            font_size=18,
            size_hint_y=None,
            height=35,
            color=(0.0, 0.8, 0.6, 1)
        )
        layout.add_widget(lbl_titulo)

        # Formulário de Parâmetros
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=100)
        form_layout.add_widget(Label(text="Banca Inicial (R$):", color=(0.8, 0.8, 0.8, 1)))
        self.input_banca = TextInput(text="1000.0", multiline=False)
        form_layout.add_widget(self.input_banca)

        form_layout.add_widget(Label(text="Risco Máximo (%):", color=(0.8, 0.8, 0.8, 1)))
        self.input_risco = TextInput(text="2.0", multiline=False)
        form_layout.add_widget(self.input_risco)
        layout.add_widget(form_layout)

        # Botão de Execução Otimizado (Altura ajustada e destaque visual proeminente)
        btn_simular = Button(
            text="[b]EXECUTAR SIMULAÇÃO DE MONTE CARLO[/b]",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=60,
            background_normal='',
            background_color=(0.0, 0.6, 0.4, 1),
            color=(1, 1, 1, 1)
        )
        btn_simular.bind(on_press=self.executar_processamento)
        layout.add_widget(btn_simular)

        # Widget de Gráfico Estatístico
        self.graph_widget = MonteCarloGraphWidget(size_hint_y=None, height=150)
        layout.add_widget(self.graph_widget)

        # Terminal de Logs e Telemetria
        self.terminal = TextInput(
            text="Sistema pronto. Clique em executar para iniciar o pipeline quantitativo.\n",
            background_color=(0.08, 0.09, 0.11, 1),
            foreground_color=(0.9, 0.9, 0.95, 1),
            cursor_color=(0.0, 0.8, 0.6, 1),
            readonly=True,
            multiline=True
        )
        layout.add_widget(self.terminal)

        self.add_widget(layout)

    def executar_processamento(self, instance):
        self.terminal.text = "Iniciando pipeline com validação estrita e retry de rede...\n"
        threading.Thread(target=self._processamento_background, daemon=True).start()

    def _processamento_background(self):
        try:
            banca = float(self.input_banca.text)
            risco = float(self.input_risco.text)

            # Simulação de busca segura com retry em API externa de partidas
            def fetch_partidas_mock():
                return [
                    Partida("Flamengo", "Palmeiras", "Brasileirão Série A", 2.10, 3.40, 3.20),
                    Partida("Real Madrid", "Barcelona", "La Liga", 1.95, 3.60, 3.80),
                    Partida("Manchester City", "Arsenal", "Premier League", 1.80, 3.70, 4.20)
                ]

            partidas = chamada_api_com_retry(fetch_partidas_mock)
            
            log_msg_1 = f"Iniciando pipeline...\n[API] {len(partidas)} partidas validadas via Dataclass com sucesso.\n"
            Clock.schedule_once(lambda dt: setattr(self.terminal, 'text', log_msg_1), 0)

            # Motor de Monte Carlo (10.000 iterações estocásticas por partida)
            todos_resultados = []
            for p in partidas:
                vitorias = sum(1 for _ in range(10000) if random.random() < (1.0 / p.odd_home))
                prob = vitorias / 10000.0
                todos_resultados.append(prob)
                
                stake = banca * (risco / 100.0)
                retorno = stake * p.odd_home
                
                bilhete = BilheteSimulacao(
                    partida=f"{p.home_team} vs {p.away_team}",
                    mercado="Match Odds (Casa)",
                    odd_selecionada=p.odd_home,
                    probabilidade_estimada=prob,
                    stake_sugerida=stake,
                    retorno_potencial=retorno
                )
                
                # Persistência relacional atômica
                self.db.salvar_bilhete(bilhete)

            # Atualização segura da interface gráfica via Clock Scheduler
            Clock.schedule_once(lambda dt: self.graph_widget.atualizar_dados(todos_resultados), 0)
            
            historico = self.db.obter_historico()
            log_final = (
                f"Iniciando pipeline...\n"
                f"[API] {len(partidas)} partidas validadas via Dataclass com sucesso.\n"
                f"[SUCESSO] Simulação concluída! Gráfico renderizado.\n"
                f"Total no banco relacional: {len(historico)} registros.\n"
            )
            Clock.schedule_once(lambda dt: setattr(self.terminal, 'text', log_final), 0)

        except Exception as e:
            err_msg = f"[ERRO CRÍTICO] {str(e)}\n"
            Clock.schedule_once(lambda dt: setattr(self.terminal, 'text', err_msg), 0)


class NexusApp(App):
    def build(self):
        self.db = NexusDatabase()
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(self.db, name='dashboard'))
        return sm

if __name__ == '__main__':
    NexusApp().run()
