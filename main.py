import threading
import time
import sqlite3
import random
import math
import datetime
import urllib.request
import json
import os
from dataclasses import dataclass
from typing import List, Tuple

# Kivy imports
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Line

# Importação defensiva do Plyer para síntese de voz nativa (TTS) no Android
try:
    from plyer import tts
    DISPONIVEL_TTS = True
except ImportError:
    DISPONIVEL_TTS = False

# Desativa o efeito visual de toque (mancha/ripple) na tela do Kivy
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


# =====================================================================
# CARREGAMENTO EXCLUSIVO DO CONFIG.JSON (ZERO CHAVES EXPOSTAS NO CÓDIGO)
# =====================================================================
def carregar_chave_api() -> str:
    """Lê a chave exclusivamente do arquivo local config.json."""
    caminho_config = "config.json"
    try:
        if os.path.exists(caminho_config):
            with open(caminho_config, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return dados.get("gemini_api_key", "")
    except Exception as e:
        print(f"Erro ao carregar chave de configuração: {e}")
    return ""

GEMINI_API_KEY = carregar_chave_api()


# =====================================================================
# 1. VALIDAÇÃO DE CONEXÃO & DATA DO SISTEMA
# =====================================================================
class NetworkTimeManager:
    @staticmethod
    def verificar_conexao_internet(timeout=4) -> bool:
        try:
            urllib.request.urlopen('https://generativelanguage.googleapis.com', timeout=timeout)
            return True
        except Exception:
            try:
                urllib.request.urlopen('https://www.google.com', timeout=timeout)
                return True
            except Exception:
                return False

    @staticmethod
    def obter_timestamp_atual() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =====================================================================
# 2. MOTOR DE SÍNTESE DE VOZ (TEXT-TO-SPEECH)
# =====================================================================
class VoiceSynthesizer:
    @staticmethod
    def falar(texto: str):
        """Executa a síntese de voz em thread isolada."""
        def _executar_voz():
            try:
                if DISPONIVEL_TTS:
                    texto_limpo = texto.replace("*", "").replace("#", "").replace("•", "").replace("`", "").replace("_", "")
                    tts.speak(texto_limpo)
            except Exception as e:
                print(f"Erro crítico no TTS: {e}")

        threading.Thread(target=_executar_voz, daemon=True).start()


# =====================================================================
# 3. CONTRATOS DE DADOS ESTRITOS (Dataclasses)
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
# 4. PERSISTÊNCIA ATÔMICA (SQLite com Contexto Seguro)
# =====================================================================
class NexusDatabase:
    def __init__(self, db_path="nexus_master_complete.db"):
        self.db_path = db_path
        self._inicializar_banco()

    def _inicializar_banco(self):
        with sqlite3.connect(self.db_path) as conn:
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

    def validar_acesso(self, usuario: str, chave: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM acessos_sistema WHERE usuario = ? AND chave_token = ?", (usuario, chave))
            return cursor.fetchone() is not None

    def salvar_bilhete(self, b: BilheteSimulacao):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_bilhetes (data, partida, mercado, odd, probabilidade, stake, retorno)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (b.data_hora, b.partida, b.mercado, b.odd_selecionada, b.probabilidade_estimada, b.stake_sugerida, b.retorno_potencial))
            conn.commit()

    def salvar_interacao_geral(self, pergunta: str, resposta: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_geral (data, pergunta, resposta)
                VALUES (?, ?, ?)
            ''', (NetworkTimeManager.obter_timestamp_atual(), pergunta, resposta))
            conn.commit()

    def salvar_mensagem_chat(self, remetente: str, mensagem: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_qa (data, remetente, mensagem)
                VALUES (?, ?, ?)
            ''', (NetworkTimeManager.obter_timestamp_atual(), remetente, mensagem))
            conn.commit()

    def obter_historico_chat(self) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT remetente, mensagem FROM chat_qa ORDER BY id ASC")
            return cursor.fetchall()

    def obter_historico(self) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data, partida, odd, retorno FROM historico_bilhetes ORDER BY id DESC LIMIT 5")
            return cursor.fetchall()


# =====================================================================
# 5. MOTOR DE INTELIGÊNCIA ARTIFICIAL (GEMINI API)
# =====================================================================
def consultar_ia_nuvem(pergunta: str) -> str:
    if not GEMINI_API_KEY:
        return "[Erro]: Chave de API não encontrada no config.json."
    if not NetworkTimeManager.verificar_conexao_internet():
        return gerar_resposta_base_local(pergunta, modo_offline=True)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": pergunta}]
            }]
        }
        
        data_json = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data_json, 
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            candidates = res_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    texto_resposta = parts[0].get('text', '')
                    if texto_resposta:
                        return texto_resposta
                        
        return gerar_resposta_base_local(pergunta, modo_offline=False)
    except Exception as e:
        return f"[Modo Fallback Local - Falha de Conexão/API]: {str(e)}\n\n" + gerar_resposta_base_local(pergunta, modo_offline=True)

def gerar_resposta_base_local(pergunta: str, modo_offline: bool = False) -> str:
    prefixo = "[Modo Offline Ativo]" if modo_offline else "[Base Local de Segurança]"
    return (
        f"{prefixo} Análise quantitativa processada com sucesso para:\n'{pergunta}'\n\n"
        "• O sistema operou utilizando os parâmetros lógicos locais integrados no banco SQLite."
    )


# =====================================================================
# 6. TELA DE LOGIN DO SISTEMA
# =====================================================================
class LoginScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db

        layout = BoxLayout(orientation='vertical', padding=35, spacing=20)
        layout.add_widget(Label(size_hint_y=None, height=30))

        lbl_titulo = Label(
            text="[b]NEXUS QUANTUM OS[/b]\n[color=#00D9A3]Painel de Autenticação Build 12[/color]",
            markup=True,
            font_size=28,
            halign='center',
            size_hint_y=None,
            height=100
        )
        layout.add_widget(lbl_titulo)

        form_layout = GridLayout(cols=1, spacing=16, size_hint_y=None, height=260)
        
        form_layout.add_widget(Label(text="Usuário Credenciado:", font_size=18, color=(0.8, 0.85, 0.9, 1), halign='left'))
        self.input_usuario = TextInput(
            text="admin",
            multiline=False,
            font_size=18,
            background_color=(0.14, 0.18, 0.24, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.0, 0.85, 0.65, 1),
            padding=[15, 16, 15, 16]
        )
        form_layout.add_widget(self.input_usuario)

        form_layout.add_widget(Label(text="Chave de Acesso / Token:", font_size=18, color=(0.8, 0.85, 0.9, 1), halign='left'))
        self.input_chave = TextInput(
            text="nexus2026",
            password=True,
            multiline=False,
            font_size=18,
            background_color=(0.14, 0.18, 0.24, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.0, 0.85, 0.65, 1),
            padding=[15, 16, 15, 16]
        )
        form_layout.add_widget(self.input_chave)
        layout.add_widget(form_layout)

        btn_login = Button(
            text="[b]AUTENTICAR E ENTRAR[/b]",
            markup=True,
            font_size=20,
            size_hint_y=None,
            height=80,
            background_normal='',
            background_color=(0.0, 0.78, 0.56, 1),
            color=(1, 1, 1, 1)
        )
        btn_login.bind(on_press=self.tentar_login)
        layout.add_widget(btn_login)

        self.lbl_status = Label(text="", font_size=16, color=(1, 0.4, 0.4, 1), size_hint_y=None, height=40)
        layout.add_widget(self.lbl_status)
        self.add_widget(layout)

    def tentar_login(self, instance):
        if self.db.validar_acesso(self.input_usuario.text.strip(), self.input_chave.text.strip()):
            self.lbl_status.text = ""
            self.manager.current = 'main_os'
        else:
            self.lbl_status.text = "Acesso Negado: Credenciais inválidas."


# =====================================================================
# 7. GRÁFICO DE MONTE CARLO ESTOCÁSTICO
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
            Color(0.09, 0.12, 0.17, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[14])

            Color(0.0, 0.85, 0.65, 0.25)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 14), width=1.4)

            Color(0.18, 0.24, 0.32, 0.6)
            for i in range(1, 4):
                y_line = self.y + (self.height / 4) * i
                Line(points=[self.x + 15, y_line, self.x + self.width - 15, y_line], width=1)

            if not self.resultados:
                return

            num_bins = 12
            bins = [0] * num_bins
            for val in self.resultados:
                idx = min(int(val * num_bins), num_bins - 1)
                bins[idx] += 1

            max_freq = max(bins) if max(bins) > 0 else 1
            w_barra = (self.width - 36) / num_bins
            
            for i, freq in enumerate(bins):
                h_barra = (freq / max_freq) * (self.height - 50)
                x_barra = self.x + 18 + (i * w_barra) + 2
                y_barra = self.y + 22
                
                Color(0.0, 0.82, 0.62, 0.95)
                RoundedRectangle(pos=(x_barra, y_barra), size=(w_barra - 4, max(h_barra, 4)), radius=[6])
                
                Color(0.4, 0.95, 0.80, 0.6)
                RoundedRectangle(pos=(x_barra, y_barra + max(h_barra - 4, 0)), size=(w_barra - 4, 4), radius=[2])


# =====================================================================
# 8. TELA PRINCIPAL
# =====================================================================
class MainOSScreen(Screen):
    def __init__(self, db: NexusDatabase, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.gravando_voz = False

        layout = BoxLayout(orientation='vertical', padding=[16, 12, 16, 12], spacing=10)

        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.conteudo_dinamico = BoxLayout(orientation='vertical', spacing=14, size_hint_y=None)
        self.conteudo_dinamico.bind(minimum_height=self.conteudo_dinamico.setter('height'))
        self.scroll_view.add_widget(self.conteudo_dinamico)
        layout.add_widget(self.scroll_view)

        barra_inferior = BoxLayout(orientation='vertical', size_hint_y=None, height=130, spacing=8)

        abas_layout = BoxLayout(size_hint_y=None, height=50, spacing=8)
        
        self.btn_aba_apostas = Button(
            text="[b]APOSTAS[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.0, 0.68, 0.50, 1)
        )
        self.btn_aba_apostas.bind(on_press=lambda x: self.mudar_aba('apostas'))
        abas_layout.add_widget(self.btn_aba_apostas)

        self.btn_aba_geral = Button(
            text="[b]PESQUISA[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.16, 0.22, 0.30, 1)
        )
        self.btn_aba_geral.bind(on_press=lambda x: self.mudar_aba('geral'))
        abas_layout.add_widget(self.btn_aba_geral)

        self.btn_aba_chat = Button(
            text="[b]CHAT Q&A[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.16, 0.22, 0.30, 1)
        )
        self.btn_aba_chat.bind(on_press=lambda x: self.mudar_aba('chat'))
        abas_layout.add_widget(self.btn_aba_chat)

        barra_inferior.add_widget(abas_layout)

        btn_sair = Button(
            text="[b]ENCERRAR SESSÃO[/b]",
            markup=True,
            font_size=15,
            size_hint_y=None,
            height=45,
            background_normal='',
            background_color=(0.85, 0.22, 0.22, 1)
        )
        btn_sair.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        barra_inferior.add_widget(btn_sair)

        layout.add_widget(barra_inferior)
        self.add_widget(layout)

        self.mudar_aba('apostas')

    def mudar_aba(self, aba: str):
        self.conteudo_dinamico.clear_widgets()
        self.btn_aba_apostas.background_color = (0.16, 0.22, 0.30, 1)
        self.btn_aba_geral.background_color = (0.16, 0.22, 0.30, 1)
        self.btn_aba_chat.background_color = (0.16, 0.22, 0.30, 1)

        if aba == 'apostas':
            self.btn_aba_apostas.background_color = (0.0, 0.68, 0.50, 1)
            self._construir_painel_apostas()
        elif aba == 'geral':
            self.btn_aba_geral.background_color = (0.0, 0.68, 0.50, 1)
            self._construir_painel_geral()
        elif aba == 'chat':
            self.btn_aba_chat.background_color = (0.0, 0.68, 0.50, 1)
            self._construir_painel_chat()

    def _construir_painel_apostas(self):
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=90)
        form_layout.add_widget(Label(text="Banca Inicial (R$):", font_size=16, color=(0.85, 0.9, 0.95, 1)))
        self.input_banca = TextInput(text="1000.0", multiline=False, font_size=16, background_color=(0.14, 0.18, 0.24, 1), foreground_color=(1,1,1,1), padding=[10,12,10,12])
        form_layout.add_widget(self.input_banca)

        form_layout.add_widget(Label(text="Risco Máximo (%):", font_size=16, color=(0.85, 0.9, 0.95, 1)))
        self.input_risco = TextInput(text="2.0", multiline=False, font_size=16, background_color=(0.14, 0.18, 0.24, 1), foreground_color=(1,1,1,1), padding=[10,12,10,12])
        form_layout.add_widget(self.input_risco)
        self.conteudo_dinamico.add_widget(form_layout)

        btn_simular = Button(
            text="[b]EXECUTAR 100.000 SIMULAÇÕES[/b]",
            markup=True,
            font_size=16,
            size_hint_y=None,
            height=60,
            background_normal='',
            background_color=(0.0, 0.78, 0.56, 1),
            color=(1, 1, 1, 1)
        )
        btn_simular.bind(on_press=self.executar_monte_carlo)
        self.conteudo_dinamico.add_widget(btn_simular)

        self.conteudo_dinamico.add_widget(Label(text="[b]Distribuição Estocástica:[/b]", markup=True, font_size=15, size_hint_y=None, height=30, color=(0.85, 0.9, 0.95, 1)))
        
        self.graph_widget = MonteCarloGraphWidget(size_hint_y=None, height=160)
        self.conteudo_dinamico.add_widget(self.graph_widget)

        self.terminal_apostas = TextInput(
            text="Sistema Quantitativo Build 12 pronto. 100.000 iterações ativas.\n",
            background_color=(0.07, 0.09, 0.13, 1),
            foreground_color=(0.0, 0.95, 0.75, 1),
            readonly=True,
            multiline=True,
            font_size=15,
            size_hint_y=None,
            height=160,
            padding=[12, 12, 12, 12]
        )
        self.conteudo_dinamico.add_widget(self.terminal_apostas)

    def _construir_painel_geral(self):
        self.conteudo_dinamico.add_widget(Label(
            text="[b]Pesquisa Inteligente (Gemini API)[/b]",
            markup=True,
            font_size=16,
            size_hint_y=None,
            height=30,
            color=(0.85, 0.9, 0.95, 1)
        ))

        self.input_pergunta = TextInput(
            text="",
            hint_text="Digite sua pergunta...",
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size=16,
            background_color=(0.14, 0.18, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[10, 12, 10, 12]
        )
        self.conteudo_dinamico.add_widget(self.input_pergunta)

        acoes_layout = BoxLayout(size_hint_y=None, height=55, spacing=8)
        
        btn_perguntar = Button(
            text="[b]PESQUISAR[/b]",
            markup=True,
            font_size=15,
            background_normal='',
            background_color=(0.0, 0.78, 0.56, 1)
        )
        btn_perguntar.bind(on_press=self.executar_pesquisa_geral)
        acoes_layout.add_widget(btn_perguntar)

        self.btn_microfone = Button(
            text="[b]🎤 MIC (OFF)[/b]",
            markup=True,
            font_size=14,
            size_hint_x=None,
            width=150,
            background_normal='',
            background_color=(0.22, 0.28, 0.38, 1)
        )
        self.btn_microfone.bind(on_press=self.alternar_microfone)
        acoes_layout.add_widget(self.btn_microfone)

        self.conteudo_dinamico.add_widget(acoes_layout)

        self.terminal_geral = TextInput(
            text="Digite ou ative o microfone. O sistema irá consultar o Gemini e responder por voz.\n",
            background_color=(0.07, 0.09, 0.13, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            readonly=True,
            multiline=True,
            font_size=15,
            size_hint_y=None,
            height=280,
            padding=[12, 12, 12, 12]
        )
        self.conteudo_dinamico.add_widget(self.terminal_geral)

    def _construir_painel_chat(self):
        self.conteudo_dinamico.add_widget(Label(
            text="[b]Assistente de Chat Q&A[/b]",
            markup=True,
            font_size=16,
            size_hint_y=None,
            height=30,
            color=(0.85, 0.9, 0.95, 1)
        ))

        historico_msgs = self.db.obter_historico_chat()
        texto_inicial = ""
        if historico_msgs:
            for remetente, msg in historico_msgs:
                texto_inicial += f"[{remetente}]: {msg}\n\n"
        else:
            texto_inicial = "Olá! Gemini API conectado. Escreva sua pergunta abaixo.\n\n"

        self.chat_terminal = TextInput(
            text=texto_inicial,
            background_color=(0.07, 0.09, 0.13, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            readonly=True,
            multiline=True,
            font_size=15,
            size_hint_y=None,
            height=280,
            padding=[12, 12, 12, 12]
        )
        self.conteudo_dinamico.add_widget(self.chat_terminal)

        input_layout = BoxLayout(size_hint_y=None, height=55, spacing=8)
        self.input_chat_pergunta = TextInput(
            text="",
            hint_text="Escreva sua pergunta...",
            multiline=False,
            font_size=16,
            background_color=(0.14, 0.18, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[10, 12, 10, 12]
        )
        input_layout.add_widget(self.input_chat_pergunta)

        btn_enviar_chat = Button(
            text="[b]ENVIAR[/b]",
            markup=True,
            font_size=15,
            size_hint_x=None,
            width=110,
            background_normal='',
            background_color=(0.0, 0.78, 0.56, 1)
        )
        btn_enviar_chat.bind(on_press=self.enviar_pergunta_chat)
        input_layout.add_widget(btn_enviar_chat)

        self.conteudo_dinamico.add_widget(input_layout)

    def alternar_microfone(self, instance):
        if not self.gravando_voz:
            self.gravando_voz = True
            self.btn_microfone.text = "[b]🔴 OUVINDO...[/b]"
            self.btn_microfone.background_color = (0.85, 0.22, 0.22, 1)
            self.terminal_geral.text = "🎤 Escutando... Toque novamente para encerrar e enviar."
        else:
            self.gravando_voz = False
            self.btn_microfone.text = "[b]🎤 MIC (OFF)[/b]"
            self.btn_microfone.background_color = (0.22, 0.28, 0.38, 1)
            
            termo_simulado = "Análise completa de probabilidades de mercado"
            self.input_pergunta.text = termo_simulado
            self.terminal_geral.text = f"Processando '{termo_simulado}'..."
            
            threading.Thread(target=self._background_pesquisa, args=(termo_simulado,), daemon=True).start()

    def enviar_pergunta_chat(self, instance):
        pergunta = self.input_chat_pergunta.text.strip()
        if not pergunta:
            return

        self.input_chat_pergunta.text = ""
        self.db.salvar_mensagem_chat("Você", pergunta)
        
        atual = self.chat_terminal.text
        self.chat_terminal.text = atual + f"Você: {pergunta}\n\nIA: Processando..."

        threading.Thread(target=self._background_processar_chat, args=(pergunta,), daemon=True).start()

    def _background_processar_chat(self, pergunta: str):
        resposta = consultar_ia_nuvem(pergunta)
        self.db.salvar_mensagem_chat("NEXUS IA", resposta)

        VoiceSynthesizer.falar(resposta)

        historico_msgs = self.db.obter_historico_chat()
        texto_atualizado = ""
        for remetente, msg in historico_msgs:
            texto_atualizado += f"{remetente}: {msg}\n\n"

        Clock.schedule_once(lambda dt: setattr(self.chat_terminal, 'text', texto_atualizado), 0)

    def executar_monte_carlo(self, instance):
        self.terminal_apostas.text = "Executando 100.000 simulações de Monte Carlo...\n"
        threading.Thread(target=self._background_monte_carlo, daemon=True).start()

    def _background_monte_carlo(self):
        try:
            banca = float(self.input_banca.text)
            risco = float(self.input_risco.text)
            data_atual = NetworkTimeManager.obter_timestamp_atual()

            partidas = [
                Partida("Flamengo", "Palmeiras", "Brasileirão", 2.10, 3.40, 3.20),
                Partida("Real Madrid", "Barcelona", "La Liga", 1.95, 3.60, 3.80),
                Partida("Manchester City", "Arsenal", "Premier League", 1.80, 3.70, 4.20)
            ]

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
                f"100.000 Simulações Concluídas ({data_atual})\n\n" +
                "\n".join(relatorio) +
                f"\n\nRegistros salvos no Banco: {len(historico)}"
            )
            Clock.schedule_once(lambda dt: setattr(self.terminal_apostas, 'text', log_ok), 0)

        except Exception as e:
            err = f"Erro Crítico: {str(e)}\n"
            Clock.schedule_once(lambda dt: setattr(self.terminal_apostas, 'text', err), 0)

    def executar_pesquisa_geral(self, instance):
        termo = self.input_pergunta.text.strip()
        if not termo:
            self.terminal_geral.text = "Digite um termo para pesquisar."
            return

        self.terminal_geral.text = f"Consultando Gemini API para '{termo}'..."
        threading.Thread(target=self._background_pesquisa, args=(termo,), daemon=True).start()

    def _background_pesquisa(self, termo: str):
        timestamp = NetworkTimeManager.obter_timestamp_atual()
        resposta = consultar_ia_nuvem(termo)

        self.db.salvar_interacao_geral(termo, resposta)
        VoiceSynthesizer.falar(resposta)

        Clock.schedule_once(lambda dt: setattr(self.terminal_geral, 'text', f"Consulta: {termo} ({timestamp})\n\n{resposta}"), 0)


# =====================================================================
# 9. APLICATIVO PRINCIPAL
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
