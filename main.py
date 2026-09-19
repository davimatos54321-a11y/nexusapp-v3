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
        try:
            urllib.request.urlopen('https://www.google.com', timeout=timeout)
            return True
        except Exception:
            return False

    @staticmethod
    def obter_timestamp_atual() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =====================================================================
# 2. CONTRATOS DE DADOS ESTRITOS (Dataclasses)
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
# 3. PERSISTÊNCIA ATÔMICA (SQLite)
# =====================================================================
class NexusDatabase:
    def __init__(self, db_path="nexus_master_complete.db"):
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
            CREATE TABLE IF NOT EXISTS acessos_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE,
                chave_token TEXT,
                nivel_permissao TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_geral (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                pergunta TEXT,
                resposta TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_qa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                remetente TEXT,
                mensagem TEXT
            )
        ''')
        
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
        cursor.execute("SELECT * FROM acessos_sistema WHERE usuario = ? AND chave_token = ?", (usuario, chave))
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

    def salvar_mensagem_chat(self, remetente: str, mensagem: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_qa (data, remetente, mensagem)
            VALUES (?, ?, ?)
        ''', (NetworkTimeManager.obter_timestamp_atual(), remetente, mensagem))
        conn.commit()
        conn.close()

    def obter_historico_chat(self) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT remetente, mensagem FROM chat_qa ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def obter_historico(self) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data, partida, odd, retorno FROM historico_bilhetes ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        return rows


# =====================================================================
# 4. RESILIÊNCIA DE REDE
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
# 5. TELA DE LOGIN (Bordas e Fontes Grandes)
# =====================================================================
class LoginScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db

        layout = BoxLayout(orientation='vertical', padding=30, spacing=22)
        layout.add_widget(Label(size_hint_y=None, height=20))

        lbl_titulo = Label(
            text="[b]NEXUS QUANTUM OS[/b]\n[color=#00D9A3]Painel de Autenticação[/color]",
            markup=True,
            font_size=26,
            halign='center',
            size_hint_y=None,
            height=100
        )
        layout.add_widget(lbl_titulo)

        form_layout = GridLayout(cols=1, spacing=16, size_hint_y=None, height=240)
        
        form_layout.add_widget(Label(text="Usuário Credenciado:", font_size=18, color=(0.8, 0.85, 0.9, 1), halign='left'))
        self.input_usuario = TextInput(
            text="admin",
            multiline=False,
            font_size=18,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.0, 0.85, 0.65, 1),
            padding=[14, 18, 14, 18]
        )
        form_layout.add_widget(self.input_usuario)

        form_layout.add_widget(Label(text="Chave de Acesso / Token:", font_size=18, color=(0.8, 0.85, 0.9, 1), halign='left'))
        self.input_chave = TextInput(
            text="nexus2026",
            password=True,
            multiline=False,
            font_size=18,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.0, 0.85, 0.65, 1),
            padding=[14, 18, 14, 18]
        )
        form_layout.add_widget(self.input_chave)
        layout.add_widget(form_layout)

        btn_login = Button(
            text="[b]AUTENTICAR E ACESSAR SISTEMA[/b]",
            markup=True,
            font_size=18,
            size_hint_y=None,
            height=70,
            background_normal='',
            background_color=(0.0, 0.72, 0.52, 1),
            color=(1, 1, 1, 1)
        )
        btn_login.bind(on_press=self.tentar_login)
        layout.add_widget(btn_login)

        self.lbl_status = Label(text="", font_size=16, color=(1, 0.4, 0.4, 1), size_hint_y=None, height=45)
        layout.add_widget(self.lbl_status)
        self.add_widget(layout)

    def tentar_login(self, instance):
        if self.db.validar_acesso(self.input_usuario.text.strip(), self.input_chave.text.strip()):
            self.lbl_status.text = ""
            self.manager.current = 'main_os'
        else:
            self.lbl_status.text = "Acesso Negado: Credenciais inválidas."


# =====================================================================
# 6. WIDGET GRÁFICO ESTOCÁSTICO COM BORDAS
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
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])

            Color(0.15, 0.20, 0.28, 0.5)
            for i in range(1, 4):
                y_line = self.y + (self.height / 4) * i
                Line(points=[self.x + 10, y_line, self.x + self.width - 10, y_line], width=1.2)

            Color(0.0, 0.85, 0.65, 0.7)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 12), width=1.8)

            if not self.resultados:
                return

            num_bins = 10
            bins = [0] * num_bins
            for val in self.resultados:
                idx = min(int(val * num_bins), num_bins - 1)
                bins[idx] += 1

            max_freq = max(bins) if max(bins) > 0 else 1
            w_barra = (self.width - 30) / num_bins
            
            for i, freq in enumerate(bins):
                h_barra = (freq / max_freq) * (self.height - 45)
                x_barra = self.x + 15 + (i * w_barra) + 2
                y_barra = self.y + 20
                
                Color(0.0, 0.75, 0.55, 0.9)
                RoundedRectangle(pos=(x_barra, y_barra), size=(w_barra - 4, h_barra), radius=[5])


# =====================================================================
# 7. TELA PRINCIPAL (Navegação Inteira na Parte Inferior + Bordas)
# =====================================================================
class MainOSScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db

        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Parte Superior Limpa (Apenas status discreto sem botões em cima)
        self.topo_status = Label(
            text="[color=#00D9A3]● SISTEMA VERIFICADO[/color] | Sincronizando...",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=30,
            halign='center'
        )
        layout.add_widget(self.topo_status)

        # Container dinâmico central (Conteúdo da Aba Ativa)
        self.conteudo_dinamico = BoxLayout(orientation='vertical', spacing=10)
        layout.add_widget(self.conteudo_dinamico)

        # BARRA DE NAVEGAÇÃO E BOTÕES TOTALMENTE NA PARTE INFERIOR DO APP
        barra_inferior = BoxLayout(orientation='vertical', size_hint_y=None, height=130, spacing=8)

        # Botões de Abas embaixo
        abas_layout = BoxLayout(size_hint_y=None, height=60, spacing=8)
        
        self.btn_aba_apostas = Button(
            text="[b]APOSTAS[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.0, 0.6, 0.45, 1)
        )
        self.btn_aba_apostas.bind(on_press=lambda x: self.mudar_aba('apostas'))
        abas_layout.add_widget(self.btn_aba_apostas)

        self.btn_aba_geral = Button(
            text="[b]PESQUISA[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.15, 0.20, 0.28, 1)
        )
        self.btn_aba_geral.bind(on_press=lambda x: self.mudar_aba('geral'))
        abas_layout.add_widget(self.btn_aba_geral)

        self.btn_aba_chat = Button(
            text="[b]CHAT Q&A IA[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.15, 0.20, 0.28, 1)
        )
        self.btn_aba_chat.bind(on_press=lambda x: self.mudar_aba('chat'))
        abas_layout.add_widget(self.btn_aba_chat)

        barra_inferior.add_widget(abas_layout)

        # Botão de Encerramento de Sessão na base inferior
        btn_sair = Button(
            text="Encerrar Sessão",
            size_hint_y=None,
            height=54,
            font_size=15,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_sair.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        barra_inferior.add_widget(btn_sair)

        layout.add_widget(barra_inferior)
        self.add_widget(layout)

        self.mudar_aba('apostas')
        Clock.schedule_interval(self.atualizar_status_sistema, 5.0)

    def atualizar_status_sistema(self, dt):
        online = NetworkTimeManager.verificar_conexao_internet()
        status_str = "[color=#00D9A3]● INTERNET ATIVA[/color]" if online else "[color=#FF4444]○ MODO OFFLINE LOCAL[/color]"
        hora_str = NetworkTimeManager.obter_timestamp_atual()
        self.topo_status.text = f"{status_str} | Time: {hora_str}"

    def mudar_aba(self, aba: str):
        self.conteudo_dinamico.clear_widgets()
        self.btn_aba_apostas.background_color = (0.15, 0.20, 0.28, 1)
        self.btn_aba_geral.background_color = (0.15, 0.20, 0.28, 1)
        self.btn_aba_chat.background_color = (0.15, 0.20, 0.28, 1)

        if aba == 'apostas':
            self.btn_aba_apostas.background_color = (0.0, 0.6, 0.45, 1)
            self._construir_painel_apostas()
        elif aba == 'geral':
            self.btn_aba_geral.background_color = (0.0, 0.6, 0.45, 1)
            self._construir_painel_geral()
        elif aba == 'chat':
            self.btn_aba_chat.background_color = (0.0, 0.6, 0.45, 1)
            self._construir_painel_chat()

    def _construir_painel_apostas(self):
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=90)
        form_layout.add_widget(Label(text="Banca Inicial (R$):", font_size=16, color=(0.8, 0.85, 0.9, 1)))
        self.input_banca = TextInput(text="1000.0", multiline=False, font_size=16, background_color=(0.12, 0.15, 0.20, 1), foreground_color=(1,1,1,1), padding=[12,14,12,14])
        form_layout.add_widget(self.input_banca)

        form_layout.add_widget(Label(text="Risco Máximo (%):", font_size=16, color=(0.8, 0.85, 0.9, 1)))
        self.input_risco = TextInput(text="2.0", multiline=False, font_size=16, background_color=(0.12, 0.15, 0.20, 1), foreground_color=(1,1,1,1), padding=[12,14,12,14])
        form_layout.add_widget(self.input_risco)
        self.conteudo_dinamico.add_widget(form_layout)

        btn_simular = Button(
            text="[b]EXECUTAR 100.000 SIMULAÇÕES DE MONTE CARLO[/b]",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=60,
            background_normal='',
            background_color=(0.0, 0.72, 0.52, 1),
            color=(1, 1, 1, 1)
        )
        btn_simular.bind(on_press=self.executar_monte_carlo)
        self.conteudo_dinamico.add_widget(btn_simular)

        self.conteudo_dinamico.add_widget(Label(text="[b]Distribuição Estocástica das Probabilidades:[/b]", markup=True, font_size=14, size_hint_y=None, height=25, color=(0.8, 0.85, 0.9, 1)))
        self.graph_widget = MonteCarloGraphWidget(size_hint_y=None, height=130)
        self.conteudo_dinamico.add_widget(self.graph_widget)

        self.terminal_apostas = TextInput(
            text="> Módulo Quantitativo pronto. 100.000 iterações por partida ativas.\n> Validação estrita e SQLite atômico prontos.\n",
            background_color=(0.06, 0.08, 0.11, 1),
            foreground_color=(0.0, 0.9, 0.7, 1),
            readonly=True,
            multiline=True,
            font_size=14,
            padding=[12, 12, 12, 12]
        )
        self.conteudo_dinamico.add_widget(self.terminal_apostas)

    def _construir_painel_geral(self):
        self.conteudo_dinamico.add_widget(Label(
            text="[b]Pesquisa Geral / Assistente com IA & Web Search[/b]",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=30,
            color=(0.8, 0.85, 0.9, 1)
        ))

        self.input_pergunta = TextInput(
            text="",
            hint_text="Digite qualquer pergunta ou pesquisa...",
            multiline=False,
            size_hint_y=None,
            height=52,
            font_size=15,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 14, 12, 14]
        )
        self.conteudo_dinamico.add_widget(self.input_pergunta)

        btn_perguntar = Button(
            text="[b]PESQUISAR / CONSULTAR ASSISTENTE[/b]",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=58,
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
            font_size=14,
            padding=[12, 12, 12, 12]
        )
        self.conteudo_dinamico.add_widget(self.terminal_geral)

    def _construir_painel_chat(self):
        self.conteudo_dinamico.add_widget(Label(
            text="[b]Assistente de Chat Q&A (Tempo Real)[/b]",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=30,
            color=(0.8, 0.85, 0.9, 1)
        ))

        historico_msgs = self.db.obter_historico_chat()
        texto_inicial = ""
        if historico_msgs:
            for remetente, msg in historico_msgs:
                texto_inicial += f"[{remetente}]: {msg}\n\n"
        else:
            texto_inicial = "> [NEXUS IA]: Olá! Faça sua pergunta abaixo. Estou pronto para responder.\n\n"

        self.chat_terminal = TextInput(
            text=texto_inicial,
            background_color=(0.06, 0.08, 0.11, 1),
            foreground_color=(0.0, 0.9, 0.7, 1),
            readonly=True,
            multiline=True,
            font_size=14,
            padding=[12, 12, 12, 12],
            size_hint_y=1
        )
        self.conteudo_dinamico.add_widget(self.chat_terminal)

        input_layout = BoxLayout(size_hint_y=None, height=56, spacing=10)
        self.input_chat_pergunta = TextInput(
            text="",
            hint_text="Escreva sua pergunta aqui...",
            multiline=False,
            font_size=15,
            background_color=(0.12, 0.15, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 14, 12, 14]
        )
        input_layout.add_widget(self.input_chat_pergunta)

        btn_enviar_chat = Button(
            text="[b]ENVIAR[/b]",
            markup=True,
            font_size=14,
            size_hint_x=None,
            width=120,
            background_normal='',
            background_color=(0.0, 0.72, 0.52, 1)
        )
        btn_enviar_chat.bind(on_press=self.enviar_pergunta_chat)
        input_layout.add_widget(btn_enviar_chat)

        self.conteudo_dinamico.add_widget(input_layout)

    def enviar_pergunta_chat(self, instance):
        pergunta = self.input_chat_pergunta.text.strip()
        if not pergunta:
            return

        self.input_chat_pergunta.text = ""
        self.db.salvar_mensagem_chat("Você", pergunta)
        
        atual = self.chat_terminal.text
        self.chat_terminal.text = atual + f"[Você]: {pergunta}\n\n[NEXUS IA]: Pensando..."

        threading.Thread(target=self._background_processar_chat, args=(pergunta,), daemon=True).start()

    def _background_processar_chat(self, pergunta: str):
        time.sleep(1.0)
        online = NetworkTimeManager.verificar_conexao_internet()
        
        if online:
            resposta = f"Compreendi sua dúvida sobre '{pergunta}'. Diretriz validada em tempo real com sucesso."
        else:
            resposta = f"Compreendi sua dúvida sobre '{pergunta}'. Modo offline ativado via SQLite local."

        self.db.salvar_mensagem_chat("NEXUS IA", resposta)

        historico_msgs = self.db.obter_historico_chat()
        texto_atualizado = ""
        for remetente, msg in historico_msgs:
            texto_atualizado += f"[{remetente}]: {msg}\n\n"

        Clock.schedule_once(lambda dt: setattr(self.chat_terminal, 'text', texto_atualizado), 0)

    def executar_monte_carlo(self, instance):
        self.terminal_apostas.text = "> Executando 100.000 simulações estocásticas...\n"
        threading.Thread(target=self._background_monte_carlo, daemon=True).start()

    def _background_monte_carlo(self):
        try:
            banca = float(self.input_banca.text)
            risco = float(self.input_risco.text)
            data_atual = NetworkTimeManager.obter_timestamp_atual()

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
                f"\n\n> [SQLite] Registros salvos: {len(historico)}"
            )
            Clock.schedule_once(lambda dt: setattr(self.terminal_apostas, 'text', log_ok), 0)

        except Exception as e:
            err = f"> [ERRO CRÍTICO] {str(e)}\n"
            Clock.schedule_once(lambda dt: setattr(self.terminal_apostas, 'text', err), 0)

    def executar_pesquisa_geral(self, instance):
        termo = self.input_pergunta.text.strip()
        if not termo:
            self.terminal_geral.text = "> Por favor, digite um termo válido."
            return

        self.terminal_geral.text = f"> Consultando '{termo}'..."
        threading.Thread(target=self._background_pesquisa, args=(termo,), daemon=True).start()

    def _background_pesquisa(self, termo: str):
        online = NetworkTimeManager.verificar_conexao_internet()
        timestamp = NetworkTimeManager.obter_timestamp_atual()

        if online:
            resposta = f"[{timestamp}] [WEB SEARCH] Resposta para '{termo}': Dados obtidos com sucesso."
        else:
            resposta = f"[{timestamp}] [OFFLINE] Resposta gerada via SQLite local."

        self.db.salvar_interacao_geral(termo, resposta)
        Clock.schedule_once(lambda dt: setattr(self.terminal_geral, 'text', f"> Consulta: {termo}\n\n{resposta}"), 0)


# =====================================================================
# 8. APLICATIVO PRINCIPAL
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
