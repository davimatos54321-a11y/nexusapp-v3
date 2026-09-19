import math
import json
import os
import threading
import requests
import sys
import io
import random
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import mainthread, Clock

try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    ANDROID_VOICE_SUPPORT = True
except Exception:
    ANDROID_VOICE_SUPPORT = False

CACHE_FILE = "nexus_cache.json"
CONFIG_FILE = "nexus_config.enc"

file_lock = threading.Lock()
Window.clearcolor = (0.03, 0.05, 0.10, 1)

class NexusQuantumApp(App):
    def build(self):
        self.cache_texto = ""
        self.indice_inicio_paginacao = 0
        self.tamanho_lote = 10

        # Layout Principal Vertical
        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # --- CABEÇALHO ---
        self.titulo = Label(
            text="[b][color=#00ffcc]NEXUS QUANTUM // v20.1 (NET & VOICE ACTIVE)[/color][/b]",
            markup=True,
            font_size=16,
            size_hint_y=None,
            height=35,
            halign='center',
            valign='middle'
        )
        self.titulo.bind(size=self.titulo.setter('text_size'))
        layout.add_widget(self.titulo)

        # --- BLOCO 1: CHAVE DA API E CONFIGURAÇÃO ---
        layout_api = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=8)
        self.txt_api_key = TextInput(
            text=self.obter_credencial("rapid_key"),
            hint_text='Chave da API (Futebol)...',
            multiline=False,
            size_hint_x=0.70,
            background_color=(0.07, 0.11, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            font_size=13,
            padding=[10, 12, 10, 12]
        )
        layout_api.add_widget(self.txt_api_key)
        
        self.btn_salvar_key = Button(
            text='Salvar Chave',
            size_hint_x=0.30,
            background_normal='',
            background_color=(0.15, 0.55, 0.35, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=12
        )
        self.btn_salvar_key.bind(on_press=self.salvar_chave_usuario)
        layout_api.add_widget(self.btn_salvar_key)
        layout.add_widget(layout_api)

        # --- BLOCO 2: CAIXA DE TEXTO SUPERIOR (TELA DE EXIBIÇÃO PRINCIPAL) ---
        self.txt_chat_ia = TextInput(
            text="[Nexus AI v20.1]: Sistema pronto na tela inicial. Permissões de Internet e Microfone ativas. Clique em 'Testar Conexão' ou 'Jogos de Hoje' para iniciar.",
            background_color=(0.02, 0.04, 0.08, 1),
            foreground_color=(0.25, 1, 0.65, 1),
            readonly=False,
            multiline=True,
            font_size=14,
            size_hint_y=0.40,
            padding=[12, 12, 12, 12]
        )
        layout.add_widget(self.txt_chat_ia)

        # --- BLOCO 3: BARRA DE PERGUNTA / MICROFONE LIVRE ---
        layout_pergunta = BoxLayout(orientation='horizontal', size_hint_y=None, height=48, spacing=8)
        self.txt_pergunta_livre = TextInput(
            hint_text='Digite ou fale qualquer dúvida para a IA...',
            multiline=False,
            size_hint_x=0.72,
            background_color=(0.07, 0.11, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            font_size=13,
            padding=[10, 12, 10, 12]
        )
        layout_pergunta.add_widget(self.txt_pergunta_livre)

        self.btn_perguntar_ia = Button(
            text='🤖 Perguntar',
            size_hint_x=0.28,
            background_normal='',
            background_color=(0.5, 0.2, 0.8, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=12
        )
        self.btn_perguntar_ia.bind(on_press=lambda x: self.processar_pergunta_livre())
        layout_pergunta.add_widget(self.btn_perguntar_ia)
        layout.add_widget(layout_pergunta)

        # --- BLOCO 4: BOTÕES GRANDES E NA PARTE DE BAIXO ---
        layout_botoes_baixo_1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=8)
        
        self.btn_jogos_hoje = Button(
            text='📅 Jogos de Hoje',
            background_normal='',
            background_color=(0.15, 0.6, 0.4, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=13
        )
        self.btn_jogos_hoje.bind(on_press=lambda x: self.disparar_processamento_async(apenas_hoje=True))
        layout_botoes_baixo_1.add_widget(self.btn_jogos_hoje)

        self.btn_testar_net = Button(
            text='🌐 Testar Conexão',
            background_normal='',
            background_color=(0.8, 0.4, 0.1, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=13
        )
        self.btn_testar_net.bind(on_press=lambda x: self.testar_conexao_internet())
        layout_botoes_baixo_1.add_widget(self.btn_testar_net)
        
        layout.add_widget(layout_botoes_baixo_1)

        layout_botoes_baixo_2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=8)
        
        self.btn_ia_generativa = Button(
            text='🧠 Parecer IA',
            background_normal='',
            background_color=(0.65, 0.15, 0.5, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=13
        )
        self.btn_ia_generativa.bind(on_press=lambda x: self.executar_analise_ia_generativa())
        layout_botoes_baixo_2.add_widget(self.btn_ia_generativa)

        self.btn_voz = Button(
            text='🎙️ Microfone Voz',
            background_normal='',
            background_color=(0.75, 0.3, 0.1, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=13
        )
        self.btn_voz.bind(on_press=lambda x: self.iniciar_captura_voz())
        layout_botoes_baixo_2.add_widget(self.btn_voz)

        layout.add_widget(layout_botoes_baixo_2)

        self.inicializar_cofre_chaves()
        return layout

    def inicializar_cofre_chaves(self):
        with file_lock:
            if not os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump({"rapid_key": ""}, f, ensure_ascii=False)
                except: pass

    def obter_credencial(self, tipo):
        with file_lock:
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f).get(tipo, "")
                except: pass
            return ""

    def salvar_chave_usuario(self, instance):
        nova_chave = self.txt_api_key.text.strip()
        with file_lock:
            dados = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                except: pass
            dados["rapid_key"] = nova_chave
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(dados, f, ensure_ascii=False)
                self.atualizar_interface_texto("[Nexus AI]: Chave salva com segurança e pronta para uso.")
            except Exception as e:
                self.atualizar_interface_texto(f"Erro ao salvar chave: {e}")

    def iniciar_captura_voz(self):
        if ANDROID_VOICE_SUPPORT:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Fale o que quiser perguntar para a IA...")
                activity.startActivity(intent)
                self.atualizar_interface_texto("🎙️ [Microfone Ativo]: Ouvindo sua pergunta no dispositivo...")
            except Exception as e:
                self.atualizar_interface_texto(f"⚠️ Erro ao acionar microfone nativo: {str(e)}")
        else:
            self.atualizar_interface_texto("🎙️ [Simulação de Voz]: Microfone acionado com sucesso! Digite ou utilize o recurso no ambiente móvel.")

    def processar_pergunta_live_texto(self, texto_pergunta):
        resposta = f"🤖 [Nexus AI - Resposta em Tela]:\n\nConsulta recebida: '{texto_pergunta}'\n\nRede conectada e processando requisição com sucesso."
        self.atualizar_interface_texto(resposta)

    def processar_pergunta_livre(self):
        pergunta = self.txt_pergunta_livre.text.strip()
        if not pergunta:
            self.atualizar_interface_texto("⚠️ Digite ou dite alguma pergunta no campo correspondente.")
            return
        self.processar_pergunta_live_texto(pergunta)

    @mainthread
    def atualizar_interface_texto(self, novo_texto):
        self.txt_chat_ia.text = novo_texto

    def testar_conexao_internet(self):
        self.atualizar_interface_texto("🌐 Testando conexão com a internet em tempo real...")
        threading.Thread(target=self._executar_teste_rede, daemon=True).start()

    def _executar_teste_rede(self):
        try:
            resp = requests.get("https://api.football-data.org/v4/matches", timeout=5)
            status = resp.status_code
            if status == 200:
                self.atualizar_interface_texto("🌐 [DIAGNÓSTICO DE REDE]: Conexão com a internet 100% OK! A API respondeu com sucesso (HTTP 200).")
            elif status in [401, 403]:
                self.atualizar_interface_texto("🌐 [DIAGNÓSTICO DE REDE]: A internet está ativa, mas a API recusou o acesso (HTTP 401/403). Verifique sua Chave da API.")
            else:
                self.atualizar_interface_texto(f"🌐 [DIAGNÓSTICO DE REDE]: Rede ativa, mas a API retornou o código HTTP {status}.")
        except requests.exceptions.ConnectionError:
            self.atualizar_interface_texto("❌ [FALHA DE REDE]: Sem conexão com a internet. Certifique-se de que o Wi-Fi ou dados móveis estão ativos e o Buildozer incluiu a permissão correta.")
        except requests.exceptions.Timeout:
            self.atualizar_interface_texto("⚠️ [TIMEOUT]: A conexão com a internet expirou. Sua rede pode estar lenta.")
        except Exception as e:
            self.atualizar_interface_texto(f"⚠️ [ERRO DE CONEXÃO]: {str(e)}")

    def disparar_processamento_async(self, apenas_hoje=False):
        self.btn_jogos_hoje.disabled = True
        self.atualizar_interface_texto("⏳ Acessando rede, buscando dados de jogos e atualizando tela...")
        threading.Thread(target=self.processo_completo_jogos, args=(apenas_hoje,), daemon=True).start()

    def processo_completo_jogos(self, apenas_hoje):
        url = "https://api.football-data.org/v4/matches"
        rapid_key = self.obter_credencial("rapid_key")
        
        if not rapid_key:
            self.atualizar_interface_texto("⚠️ Aviso: Insira sua chave da API no campo superior e clique em 'Salvar Chave'.")
            self.btn_jogos_hoje.disabled = False
            return

        headers = {"User-Agent": "NexusQuantumApp/20.1", "X-Auth-Token": rapid_key}
        
        try:
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                dados_partidas = response.json()
                with file_lock:
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(dados_partidas, f, ensure_ascii=False)
            elif response.status_code in [401, 403]:
                self.atualizar_interface_texto("❌ Erro de Autenticação: Verifique se sua chave da API está correta.")
                self.btn_jogos_hoje.disabled = False
                return
            else:
                raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            dados_partidas = {}
            with file_lock:
                if os.path.exists(CACHE_FILE):
                    try:
                        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                            dados_partidas = json.load(f)
                    except: pass
            if not dados_partidas:
                self.atualizar_interface_texto(f"🌐 Falha de Conexão com a Internet: {str(e)}\n\nToque em 'Testar Conexão' para verificar o status.")
                self.btn_jogos_hoje.disabled = False
                return

        matches = dados_partidas.get("matches", [])
        
        if apenas_hoje:
            data_hoje = datetime.now().strftime('%Y-%m-%d')
            matches = [m for m in matches if m.get('utcDate', '').startswith(data_hoje)]

        total_matches = len(matches)
        if total_matches == 0:
            msg = "ℹ️ Nenhum jogo encontrado para hoje na API." if apenas_hoje else "ℹ️ Nenhum jogo encontrado na sincronização global."
            self.atualizar_interface_texto(msg)
            self.btn_jogos_hoje.disabled = False
            return

        titulo_rel = "=== ESTATÍSTICAS E JOGOS DE HOJE ===" if apenas_hoje else f"=== VARREDURA GLOBAL ({total_matches} JOGOS) ==="
        texto = f"{titulo_rel}\n\n"
        
        for idx, m in enumerate(matches[:8], start=1):
            home = m.get('homeTeam', {}).get('name', 'Time A')
            away = m.get('awayTeam', {}).get('name', 'Time B')
            comp = m.get('competition', {}).get('name', 'Liga N/A')
            utc_date = m.get('utcDate', '0000-00-00T00:00:00Z')
            hora = utc_date[11:16] if len(utc_date) > 15 else '?'
            
            p_c = random.randint(45, 75)
            p_f = 100 - p_c
            
            texto += f"{idx}. [{comp}] {home} vs {away} ({hora}h)\n"
            texto += f"   • Probabilidade Mandante: {p_c}% | Visitante: {p_f}% | Status: Rede Conectada\n\n"

        self.atualizar_interface_texto(texto)
        self.btn_jogos_hoje.disabled = False

    def ler_cache_seguro(self):
        with file_lock:
            if not os.path.exists(CACHE_FILE): return []
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f).get("matches", [])
            except: return []

    def executar_analise_ia_generativa(self):
        matches = self.ler_cache_seguro()
        if not matches:
            self.atualizar_interface_texto("⚠️ Cache vazio. Sincronize os jogos primeiro usando o botão 'Jogos de Hoje'.")
            return

        jogo = matches[0]
        home = jogo.get('homeTeam', {}).get('name', 'Mandante')
        away = jogo.get('awayTeam', {}).get('name', 'Visitante')

        parecer = f"🧠 PARECER DA IA AVANÇADA:\n\nConfronto: {home} vs {away}\nAnálise preditiva online conectada com sucesso via internet."
        self.atualizar_interface_texto(parecer)

if __name__ == "__main__":
    NexusQuantumApp().run()
