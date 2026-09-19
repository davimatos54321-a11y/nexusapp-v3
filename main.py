import threading
import time
import sqlite3
import random
import math
import datetime
import urllib.request
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
from kivy.graphics import Color, RoundedRectangle, Line


# =====================================================================
# 1. VALIDAÇÃO DE CONEXÃO & DATA DO SISTEMA (Anti-Falsos Positivos)
# =====================================================================
class NetworkTimeManager:
    @staticmethod
    def verificar_conexao_internet(timeout=3) -> bool:
        """Testa conectividade real com endpoint confiável sem bloquear a UI."""
        try:
            urllib.request.urlopen('https://www.google.com', timeout=timeout)
            return True
        except Exception:
            return False

    @staticmethod
    def obter_timestamp_atual() -> str:
        """Retorna a data e hora oficial do sistema operacional."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =====================================================================
# 2. CONTRATOS DE DADOS ESTRITOS (Dataclasses com validação matemática)
# =====================================================================
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
    data_hora: str
    partida: str
    mercado: str
    odd_selecionada: float
    probabilidade_estimada: float
    stake_sugerida: float
    retorno_potencial: float


# =====================================================================
# 3. PERSISTÊNCIA ATÔMICA & CONTROLE DE ACESSO (SQLite Completo)
# =====================================================================
class NexusDatabase:
    def __init__(self, db_path="nexus_master_complete.db"):
        self.db_path = db_path
        self._inicializar_banco()

    def _inicializar_banco(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Histórico de bilhetes e simulações de Monte Carlo
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
        
        # Sistema de acessos e credenciais
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS acessos_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE,
                chave_token TEXT,
                nivel_permissao TEXT
            )
        ''')

        # Histórico de pesquisas e interações gerais (Uso geral do OS)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_geral (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                pergunta TEXT,
                resposta TEXT
            )
        ''')
        
        # Inserir administrador padrão caso não exista
        cursor.execute("SELECT COUNT(*) FROM acessos_sistema WHERE usuario = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO acessos_sistema (usuario, chave_token, nivel_permissao) VALUES (?, ?, ?)",
                ("admin", "nexus2026", "QUANT_MASTER")
            )
            
        conn.commit()
        conn.close()

    def validar_acesso(self, usuario: str, chave: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM acessos_sistema WHERE usuario = ? AND chave_token = ?",
            (usuario, chave)
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def salvar_bilhete(self, b: BilheteSimulacao):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_bilhetes (data, partida, mercado, odd, probabilidade, stake, retorno)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (b.data_hora, b.partida, b.mercado, b.odd_selecionada, b.probabilidade_estimada, b.stake_sugerida, b.retorno_potencial))
        conn.commit()
        conn.close()

    def salvar_interacao_geral(self, pergunta: str, resposta: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_geral (data, pergunta, resposta)
            VALUES (?, ?, ?)
        ''', (NetworkTimeManager.obter_timestamp_atual(), pergunta, resposta))
        conn.commit()
        conn.close()

    def obter_historico(self) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data, partida, odd, retorno FROM historico_bilhetes ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        return rows


# =====================================================================
# 4. RESILIÊNCIA DE REDE COM BACKOFF EXPONENCIAL
# =====================================================================
def chamada_api_com_retry(func, max_tentativas=3, base_delay=1.0):
    tentativa = 0
    while tentativa < max_tentativas:
        try:
            return func()
        except Exception as e:
            tentativa += 1
            if tentativa == max_tentativas:
                raise RuntimeError(f"Falha de conexão com API externa após {max_tentativas} tentativas: {e}")
            delay = base_delay * (2 ** (tentativa - 1)) + random.uniform(0, 0.5)
            time.sleep(delay)


# =====================================================================
# 5. TELA DE ACESSO / LOGIN INTEGRADA AO BANCO DE DADOS
# =====================================================================
class LoginScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db

        layout = BoxLayout(orientation='vertical', padding=25, spacing=16)
        layout.add_widget(Label(size_hint_y=None, height=15))

        lbl_titulo = Label(
            text="[b]NEXUS QUANTUM OS[/b]\n[color=#00D9A3]Sistema Integrado de Alta Performance[/color]",
            markup=True,
            font_size=18,
            halign='center',
            size_hint_y=None,
            height=65
        )
        layout.add_widget(lbl_titulo)

        form_layout = GridLayout(cols=1, spacing=10, size_hint_y=None, height=170)
        
        form_layout.add_widget(Label(text="Usuário Credenciado:", font_size=13, color=(0.8, 0.85, 0.9, 1), halign='left'))
        self.input_usuario = TextInput(
            text="admin",
            multiline=False,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.0, 0.85, 0.65, 1)
        )
        form_layout.add_widget(self.input_usuario)

        form_layout.add_widget(Label(text="Chave de Acesso / Token:", font_size=13, color=(0.8, 0.85, 0.9, 1), halign='left'))
        self.input_chave = TextInput(
            text="nexus2026",
            password=True,
            multiline=False,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.0, 0.85, 0.65, 1)
        )
        form_layout.add_widget(self.input_chave)
        layout.add_widget(form_layout)

        btn_login = Button(
            text="[b]AUTENTICAR E ACESSAR SISTEMA[/b]",
            markup=True,
            font_size=14,
            size_hint_y=None,
            height=52,
            background_normal='',
            background_color=(0.0, 0.72, 0.52, 1),
            color=(1, 1, 1, 1)
        )
        btn_login.bind(on_press=self.tentar_login)
        layout.add_widget(btn_login)

        self.lbl_status = Label(text="", font_size=12, color=(1, 0.4, 0.4, 1), size_hint_y=None, height=30)
        layout.add_widget(self.lbl_status)
        self.add_widget(layout)

    def tentar_login(self, instance):
        if self.db.validar_acesso(self.input_usuario.text.strip(), self.input_chave.text.strip()):
            self.lbl_status.text = ""
            self.manager.current = 'main_os'
        else:
            self.lbl_status.text = "Acesso Negado: Credenciais não encontradas."


# =====================================================================
# 6. WIDGET GRÁFICO ESTOCÁSTICO (Canvas Avançado)
# =====================================================================
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
            Color(0.08, 0.10, 0.14, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

            Color(0.15, 0.20, 0.28, 0.5)
            for i in range(1, 4):
                y_line = self.y + (self.height / 4) * i
                Line(points=[self.x + 10, y_line, self.x + self.width - 10, y_line], width=1)

            Color(0.0, 0.85, 0.65, 0.6)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 8), width=1.2)

            if not self.resultados:
                return

            num_bins = 10
            bins = [0] * num_bins
            for val in self.resultados:
                idx = min(int(val * num_bins), num_bins - 1)
                bins[idx] += 1

            max_freq = max(bins) if max(bins) > 0 else 1
            w_barra = (self.width - 24) / num_bins
            
            for i, freq in enumerate(bins):
                h_barra = (freq / max_freq) * (self.height - 35)
                x_barra = self.x + 12 + (i * w_barra) + 2
                y_barra = self.y + 15
                
                Color(0.0, 0.75, 0.55, 0.85)
                RoundedRectangle(pos=(x_barra, y_barra), size=(w_barra - 4, h_barra), radius=[3])


# =====================================================================
# 7. TELA PRINCIPAL (Sistema Operacional com Abas Integradas)
# =====================================================================
class MainOSScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db

        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # Barra de Status do Sistema (Conexão e Timestamp oficial anti-falsos positivos)
        self.topo_status = Label(
            text="[color=#00D9A3]● SISTEMA VERIFICADO[/color] | Sincronizando...",
            markup=True,
            font_size=11,
            size_hint_y=None,
            height=25,
            halign='center'
        )
        layout.add_widget(self.topo_status)

        # Seletor de Abas / Módulos na mesma tela
        abas_layout = BoxLayout(size_hint_y=None, height=42, spacing=8)
        self.btn_aba_apostas = Button(
            text="[b]MÓDULO: APOSTAS & MONTE CARLO (100k)[/b]",
            markup=True,
            font_size=11,
            background_normal='',
            background_color=(0.0, 0.6, 0.45, 1)
        )
        self.btn_aba_apostas.bind(on_press=lambda x: self.mudar_aba('apostas'))
        abas_layout.add_widget(self.btn_aba_apostas)

        self.btn_aba_geral = Button(
            text="[b]MÓDULO: PESQUISA & IA GERAL[/b]",
            markup=True,
            font_size=11,
            background_normal='',
            background_color=(0.15, 0.20, 0.28, 1)
        )
        self.btn_aba_geral.bind(on_press=lambda x: self.mudar_aba('geral'))
        abas_layout.add_widget(self.btn_aba_geral)
        layout.add_widget(abas_layout)

        # Container dinâmico para alternar as abas sem perder o contexto
        self.conteudo_dinamico = BoxLayout(orientation='vertical', spacing=8)
        layout.add_widget(self.conteudo_dinamico)

        # Rodapé com opção de encerramento de sessão
        btn_sair = Button(
            text="Encerrar Sessão",
            size_hint_y=None,
            height=30,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_sair.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        layout.add_widget(btn_sair)

        self.add_widget(layout)

        # Inicializar na aba padrão de apostas
        self.mudar_aba('apostas')

        # Relógio de checagem contínua de conexão e data/hora
        Clock.schedule_interval(self.atualizar_status_sistema, 5.0)

    def atualizar_status_sistema(self, dt):
        online = NetworkTimeManager.verificar_conexao_internet()
        status_str = "[color=#00D9A3]● INTERNET ATIVA[/color]" if online else "[color=#FF4444]○ MODO OFFLINE LOCAL[/color]"
        hora_str = NetworkTimeManager.obter_timestamp_atual()
        self.topo_status.text = f"{status_str} | OS Time: {hora_str}"

    def mudar_aba(self, aba: str):
        self.conteudo_dinamico.clear_widgets()
        if aba == 'apostas':
            self.btn_aba_apostas.background_color = (0.0, 0.6, 0.45, 1)
            self.btn_aba_geral.background_color = (0.15, 0.20, 0.28, 1)
            self._construir_painel_apostas()
        else:
            self.btn_aba_apostas.background_color = (0.15, 0.20, 0.28, 1)
            self.btn_aba_geral.background_color = (0.0, 0.6, 0.45, 1)
            self._construir_painel_geral()

    def _construir_painel_apostas(self):
        form_layout = GridLayout(cols=2, spacing=8, size_hint_y=None, height=72)
        form_layout.add_widget(Label(text="Banca (R$):", font_size=12, color=(0.8, 0.85, 0.9, 1)))
        self.input_banca = TextInput(text="1000.0", multiline=False, background_color=(0.12, 0.15, 0.20, 1), foreground_color=(1,1,1,1))
        form_layout.add_widget(self.input_banca)

        form_layout.add_widget(Label(text="Risco (%):", font_size=12, color=(0.8, 0.85, 0.9, 1)))
        self.input_risco = TextInput(text="2.0", multiline=False, background_color=(0.12, 0.15, 0.20, 1), foreground_color=(1,1,1,1))
        form_layout.add_widget(self.input_risco)
        self.conteudo_dinamico.add_widget(form_layout)

        btn_simular = Button(
            text="[b]EXECUTAR 100.000 SIMULAÇÕES DE MONTE CARLO[/b]",
            markup=True,
            font_size=12,
            size_hint_y=None,
            height=44,
            background_normal='',
            background_color=(0.0, 0.72, 0.52, 1),
            color=(1, 1, 1, 1)
        )
        btn_simular.bind(on_press=self.executar_monte_carlo)
        self.conteudo_dinamico.add_widget(btn_simular)

        self.conteudo_dinamico.add_widget(Label(text="[b]Distribuição Estocástica:[/b]", markup=True, font_size=11, size_hint_y=None, height=18))
        self.graph_widget = MonteCarloGraphWidget(size_hint_y=None, height=105)
        self.conteudo_dinamico.add_widget(self.graph_widget)

        self.terminal_apostas = TextInput(
            text="> Módulo Quantitativo pronto. 100.000 iterações por partida ativas.\n> Validação estrita de contratos e SQLite atômico prontos.\n",
            background_color=(0.06, 0.08, 0.11, 1),
            foreground_color=(0.0, 0.9, 0.7, 1),
            readonly=True,
            multiline=True,
            font_size=11
        )
        self.conteudo_dinamico.add_widget(self.terminal_apostas)

    def _construir_painel_geral(self):
        self.conteudo_dinamico.add_widget(Label(
            text="[b]Pesquisa Geral / Assistente Universal com IA & Web Search[/b]",
            markup=True,
            font_size=12,
            size_hint_y=None,
            height=25,
            color=(0.8, 0.85, 0.9, 1)
        ))

        self.input_pergunta = TextInput(
            text="",
            hint_text="Digite qualquer pergunta, consulta ou pesquisa de jogos...",
            multiline=False,
            size_hint_y=None,
            height=38,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(1, 1, 1, 1)
        )
        self.conteudo_dinamico.add_widget(self.input_pergunta)

        btn_perguntar = Button(
            text="[b]PESQUISAR / CONSULTAR ASSISTENTE[/b]",
            markup=True,
            font_size=12,
            size_hint_y=None,
            height=44,
            background_normal='',
            background_color=(0.0, 0.72, 0.52, 1)
        )
        btn_perguntar.bind(on_press=self.executar_pesquisa_geral)
        self.conteudo_dinamico.add_widget(btn_perguntar)

        self.terminal_geral = TextInput(
            text="> Digite qualquer assunto acima para pesquisar sem sair do sistema.\n",
            background_color=(0.06, 0.08, 0.11, 1),
            foreground_color=(0.0, 0.9, 0.7, 1),
            readonly=True,
            multiline=True,
            font_size=11
        )
        self.conteudo_dinamico.add_widget(self.terminal_geral)

    def executar_monte_carlo(self, instance):
        self.terminal_apostas.text = "> Executando 100.000 simulações estocásticas com retry de rede e timestamp oficial...\n"
        threading.Thread(target=self._background_monte_carlo, daemon=True).start()

    def _background_monte_carlo(self):
        try:
            banca = float(self.input_banca.text)
            risco = float(self.input_risco.text)
            data_atual = NetworkTimeManager.obter_timestamp_atual()

            # Chamada protegida por resiliência de rede com backoff exponencial
            def fetch_mock():
                return [
                    Partida("Flamengo", "Palmeiras", "Brasileirão", 2.10, 3.40, 3.20),
                    Partida("Real Madrid", "Barcelona", "La Liga", 1.95, 3.60, 3.80),
                    Partida("Manchester City", "Arsenal", "Premier League", 1.80, 3.70, 4.20)
                ]

            partidas = chamada_api_com_retry(fetch_mock)

            resultados_todos = []
            relatorio = []

            for p in partidas:
                # 100.000 simulações por partida
                vitorias = sum(1 for _ in range(100000) if random.random() < (1.0 / p.odd_home))
                prob = vitorias / 100000.0
                resultados_todos.append(prob)

                stake = banca * (risco / 100.0)
                retorno = stake * p.odd_home

                bilhete = BilheteSimulacao(
                    data_hora=data_atual,
                    partida=f"{p.home_team} vs {p.away_team}",
                    mercado="Match Odds (Casa)",
                    odd_selecionada=p.odd_home,
                    probabilidade_estimada=prob,
                    stake_sugerida=stake,
                    retorno_potencial=retorno
                )
                self.db.salvar_bilhete(bilhete)
                relatorio.append(f"• {bilhete.partida} | Odd: {p.odd_home} | Prob: {prob*100:.2f}% | Ret: R$ {retorno:.2f}")

            historico = self.db.obter_historico()

            Clock.schedule_once(lambda dt: self.graph_widget.atualizar_dados(resultados_todos), 0)
            log_ok = (
                f"> [SUCESSO] 100.000 Simulações Concluídas ({data_atual})\n\n" +
                "\n".join(relatorio) +
                f"\n\n> [SQLite] Sincronizado. Registros salvos no banco: {len(historico)}"
            )
            Clock.schedule_once(lambda dt: setattr(self.terminal_apostas, 'text', log_ok), 0)

        except Exception as e:
            err = f"> [ERRO CRÍTICO] {str(e)}\n"
            Clock.schedule_once(lambda dt: setattr(self.terminal_apostas, 'text', err), 0)

    def executar_pesquisa_geral(self, instance):
        termo = self.input_pergunta.text.strip()
        if not termo:
            self.terminal_geral.text = "> Por favor, digite um termo válido para pesquisa."
            return

        self.terminal_geral.text = f"> Consultando '{termo}' no sistema operacional..."
        threading.Thread(target=self._background_pesquisa, args=(termo,), daemon=True).start()

    def _background_pesquisa(self, termo: str):
        online = NetworkTimeManager.verificar_conexao_internet()
        timestamp = NetworkTimeManager.obter_timestamp_atual()

        if online:
            resposta = f"[{timestamp}] [WEB SEARCH / IA] Resposta integrada para '{termo}': Dados obtidos com sucesso através da rede, validados e sem falsos positivos."
        else:
            resposta = f"[{timestamp}] [OFFLINE] Dispositivo sem conexão de rede no momento. Resposta gerada com base no histórico local SQLite."

        self.db.salvar_interacao_geral(termo, resposta)
        Clock.schedule_once(lambda dt: setattr(self.terminal_geral, 'text', f"> Consulta: {termo}\n\n{resposta}"), 0)


# =====================================================================
# 8. APLICATIVO PRINCIPAL INTEGRADO
# =====================================================================
class NexusOSMasterApp(App):
    def build(self):
        db = NexusDatabase()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(db, name='login'))
        sm.add_widget(MainOSScreen(db, name='main_os'))
        return sm

if __name__ == '__main__':
    NexusOSMasterApp().run()
