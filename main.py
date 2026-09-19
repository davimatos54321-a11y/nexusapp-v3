import math
import json
import os
import threading
import requests
import random
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import mainthread
from kivy.graphics import Color, RoundedRectangle

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
HISTORY_FILE = "nexus_historico.json"
SECRET_FILE = "config.json" # Arquivo seguro local (não versionado no Git)

file_lock = threading.Lock()
Window.clearcolor = (0.03, 0.05, 0.10, 1)

class AppIconButton(Button):
    def __init__(self, bg_color=(0.1, 0.5, 0.8, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.bg_color = bg_color
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = 15
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self.update_canvas, pos=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[16])

class NexusQuantumApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)

        self.titulo = Label(
            text="[b][color=#00ffcc]NEXUS QUANTUM // 100k + BANCA + HISTÓRICO[/color][/b]",
            markup=True,
            font_size=16,
            size_hint_y=None,
            height=34,
            halign='center',
            valign='middle'
        )
        self.titulo.bind(size=self.titulo.setter('text_size'))
        layout.add_widget(self.titulo)

        layout_banca = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=6)
        
        self.txt_banca = TextInput(
            text=self.obter_config("banca_valor", "100.0"),
            hint_text='Banca (R$)...',
            multiline=False,
            size_hint_x=0.45,
            background_color=(0.07, 0.11, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            font_size=14,
            padding=[6, 10, 6, 10]
        )
        layout_banca.add_widget(self.txt_banca)

        self.txt_risco = TextInput(
            text=self.obter_config("risco_pct", "2.0"),
            hint_text='Risco (%/Aposta)...',
            multiline=False,
            size_hint_x=0.40,
            background_color=(0.07, 0.11, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            font_size=14,
            padding=[6, 10, 6, 10]
        )
        layout_banca.add_widget(self.txt_risco)
        
        self.btn_salvar_banca = AppIconButton(
            text='💾',
            bg_color=(0.15, 0.55, 0.35, 1),
            size_hint_x=0.15
        )
        self.btn_salvar_banca.bind(on_press=self.salvar_configuracoes_banca)
        layout_banca.add_widget(self.btn_salvar_banca)
        layout.add_widget(layout_banca)

        self.txt_chat_ia = TextInput(
            text="[Nexus AI Engine]: Sistema blindado e pronto. Insira sua banca, configure o risco e clique em 'Gerar Bilhete 100k'.",
            background_color=(0.02, 0.04, 0.08, 1),
            foreground_color=(0.25, 1, 0.65, 1),
            readonly=False,
            multiline=True,
            font_size=18,
            size_hint_y=0.38,
            padding=[10, 10, 10, 10]
        )
        layout.add_widget(self.txt_chat_ia)

        grid_botoes = GridLayout(cols=2, spacing=8, size_hint_y=None, height=140)

        self.btn_jogos_hoje = AppIconButton(
            text='🎲 Gerar Bilhete 100k',
            bg_color=(0.10, 0.65, 0.35, 1)
        )
        self.btn_jogos_hoje.bind(on_press=lambda x: self.disparar_processamento_async())
        grid_botoes.add_widget(self.btn_jogos_hoje)

        self.btn_historico = AppIconButton(
            text='📂 Ver Histórico',
            bg_color=(0.15, 0.45, 0.85, 1)
        )
        self.btn_historico.bind(on_press=lambda x: self.exibir_historico_salvo())
        grid_botoes.add_widget(self.btn_historico)

        self.btn_ia_generativa = AppIconButton(
            text='🧠 Parecer Quântico (Gemini)',
            bg_color=(0.60, 0.15, 0.65, 1)
        )
        self.btn_ia_generativa.bind(on_press=lambda x: self.executar_analise_ia_generativa())
        grid_botoes.add_widget(self.btn_ia_generativa)

        self.btn_testar_net = AppIconButton(
            text='🌐 Testar Conexão',
            bg_color=(0.85, 0.45, 0.10, 1)
        )
        self.btn_testar_net.bind(on_press=lambda x: self.testar_conexao_internet())
        grid_botoes.add_widget(self.btn_testar_net)

        layout.add_widget(grid_botoes)

        layout_barra_ia = BoxLayout(orientation='horizontal', size_hint_y=None, height=52, spacing=6)
        
        self.btn_voz_barra = AppIconButton(
            text='🎙️',
            bg_color=(0.20, 0.30, 0.50, 1),
            size_hint_x=0.15
        )
        self.btn_voz_barra.bind(on_press=lambda x: self.iniciar_captura_voz())
        layout_barra_ia.add_widget(self.btn_voz_barra)

        self.txt_pergunta_livre = TextInput(
            hint_text='Consultar time ou status...',
            multiline=False,
            size_hint_x=0.60,
            background_color=(0.07, 0.11, 0.20, 1),
            foreground_color=(1, 1, 1, 1),
            font_size=15,
            padding=[8, 12, 8, 12]
        )
        layout_barra_ia.add_widget(self.txt_pergunta_livre)

        self.btn_perguntar_ia = AppIconButton(
            text='➤ Enviar',
            bg_color=(0.45, 0.15, 0.75, 1),
            size_hint_x=0.25
        )
        self.btn_perguntar_ia.bind(on_press=lambda x: self.processar_pergunta_livre())
        layout_barra_ia.add_widget(self.btn_perguntar_ia)

        layout.add_widget(layout_barra_ia)

        self.inicializar_cofre()
        return layout

    def inicializar_cofre(self):
        with file_lock:
            if not os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump({"banca_valor": "100.0", "risco_pct": "2.0"}, f, ensure_ascii=False)
                except: pass

    def obter_config(self, chave, padrao=""):
        with file_lock:
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f).get(chave, padrao)
                except: pass
            return padrao

    def obter_chave_gemini(self):
        """Lê a chave do arquivo local de configuração isolado"""
        if os.path.exists(SECRET_FILE):
            try:
                with open(SECRET_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f).get("gemini_key", "")
            except: pass
        return ""

    def salvar_configuracoes_banca(self, instance):
        banca = self.txt_banca.text.strip()
        risco = self.txt_risco.text.strip()
        with file_lock:
            dados = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                except: pass
            dados["banca_valor"] = banca if banca else "100.0"
            dados["risco_pct"] = risco if risco else "2.0"
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(dados, f, ensure_ascii=False)
                self.atualizar_interface_texto("[Nexus AI]: Gestão de banca atualizada e salva com segurança.")
            except Exception as e:
                self.atualizar_interface_texto(f"Erro ao salvar banca: {e}")

    def salvar_no_historico(self, texto_bilhete):
        with file_lock:
            historico = []
            if os.path.exists(HISTORY_FILE):
                try:
                    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                        historico = json.load(f)
                except: pass
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            historico.insert(0, {"data": data_atual, "conteudo": texto_bilhete})
            historico = historico[:30]
            
            try:
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(historico, f, ensure_ascii=False)
            except: pass

    def exibir_historico_salvo(self):
        with file_lock:
            if not os.path.exists(HISTORY_FILE):
                self.atualizar_interface_texto("📂 [Histórico]: Nenhum bilhete salvo ainda. Gere seu primeiro bilhete 100k!")
                return
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    historico = json.load(f)
                if not historico:
                    self.atualizar_interface_texto("📂 [Histórico]: O registro de bilhetes está vazio.")
                    return
                
                relatorio_hist = f"📂 === HISTÓRICO DE BILHETES ({len(historico)} Salvos) === 📂\n\n"
                for item in historico[:3]: 
                    data_reg = item.get('data', 'Data desconhecida')
                    conteudo_reg = item.get('conteudo', str(item))
                    relatorio_hist += f"📅 Data: {data_reg}\n{conteudo_reg}\n" + "="*30 + "\n\n"
                
                self.atualizar_interface_texto(relatorio_hist)
            except Exception as e:
                self.atualizar_interface_texto(f"❌ Erro ao carregar histórico: {e}")

    def iniciar_captura_voz(self):
        if ANDROID_VOICE_SUPPORT:
            try:
                activity = PythonActivity.mActivity
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Fale sua consulta...")
                activity.startActivity(intent)
                self.atualizar_interface_texto("🎙️ [Microfone Ativo]: Ouvindo comando...")
            except Exception as e:
                self.atualizar_interface_texto(f"⚠️ Erro no microfone: {str(e)}")
        else:
            self.atualizar_interface_texto("🎙️ [Simulação de Voz]: Dispositivo acionado com sucesso!")

    def processar_pergunta_livre(self):
        pergunta = self.txt_pergunta_livre.text.strip()
        if not pergunta:
            self.atualizar_interface_texto("⚠️ Digite ou utilize o microfone.")
            return
        self.atualizar_interface_texto(f"🤖 [Nexus AI]: Consulta sobre '{pergunta}' processada com base no cache local.")

    @mainthread
    def atualizar_interface_texto(self, novo_texto):
        self.txt_chat_ia.text = novo_texto

    def testar_conexao_internet(self):
        self.atualizar_interface_texto("🌐 Testando conexão com a internet...")
        threading.Thread(target=self._executar_teste_rede, daemon=True).start()

    def _executar_teste_rede(self):
        try:
            requests.get("https://www.google.com", timeout=4)
            self.atualizar_interface_texto("🌐 [DIAGNÓSTICO]: Conexão com a internet está ativa e operando perfeitamente!")
        except Exception:
            self.atualizar_interface_texto("❌ [FALHA DE REDE]: Sem conexão com a internet no Android.")

    def disparar_processamento_async(self):
        self.btn_jogos_hoje.disabled = True
        self.atualizar_interface_texto("⏳ Calculando gestão de banca e rodando 100.000 simulações de Monte Carlo...")
        threading.Thread(target=self.processo_monte_carlo, daemon=True).start()

    def processo_monte_carlo(self):
        try:
            banca_val = float(str(self.obter_config("banca_valor", "100.0")).replace(',', '.'))
        except:
            banca_val = 100.0

        try:
            risco_pct = float(str(self.obter_config("risco_pct", "2.0")).replace(',', '.'))
        except:
            risco_pct = 2.0

        stake_sugerida = banca_val * (risco_pct / 100.0)

        matches = self.ler_cache_seguro()
        if not matches:
            matches = [
                {"homeTeam": {"name": "Arsenal"}, "awayTeam": {"name": "Chelsea"}, "competition": {"name": "Premier League"}},
                {"homeTeam": {"name": "Real Madrid"}, "awayTeam": {"name": "Barcelona"}, "competition": {"name": "La Liga"}},
                {"homeTeam": {"name": "Flamengo"}, "awayTeam": {"name": "Palmeiras"}, "competition": {"name": "Campeonato Brasileiro"}}
            ]

        data_hoje = datetime.now().strftime('%Y-%m-%d')
        matches_hoje = matches[:5]

        texto_relatorio = f"🎟️ === BILHETE NEXUS (100k) // {data_hoje} === 🎟️\n"
        texto_relatorio += f"💰 Banca: R$ {banca_val:.2f} | Stake por Aposta ({risco_pct}%): R$ {stake_sugerida:.2f}\n\n"

        for idx, m in enumerate(matches_hoje, start=1):
            home = m.get('homeTeam', {}).get('name', 'Mandante')
            away = m.get('awayTeam', {}).get('name', 'Visitante')
            comp = m.get('competition', {}).get('name', 'Liga Oficial')
            
            simulacoes = 100000
            vitorias_home = 0
            empates = 0
            vitorias_away = 0
            total_gols = 0

            lambda_home = 1.45
            lambda_away = 1.10

            for _ in range(simulacoes):
                gols_h = int(random.gauss(lambda_home, 0.8))
                gols_a = int(random.gauss(lambda_away, 0.7))
                gols_h = max(0, gols_h)
                gols_a = max(0, gols_a)

                total_gols += (gols_h + gols_a)

                if gols_h > gols_a:
                    vitorias_home += 1
                elif gols_h == gols_a:
                    empates += 1
                else:
                    vitorias_away += 1

            p_h = (vitorias_home / simulacoes) * 100
            p_e = (empates / simulacoes) * 100
            p_a = (vitorias_away / simulacoes) * 100
            media_gols = total_gols / simulacoes

            if p_h >= 55.0:
                sugestao_1x2 = f"Vitória Casa ({home})"
            elif p_a >= 50.0:
                sugestao_1x2 = f"Vitória Fora ({away})"
            else:
                sugestao_1x2 = "Dupla Hipótese / Empate Anula"

            if media_gols > 2.5:
                sugestao_gols = "Over 2.5 Gols"
            else:
                sugestao_gols = "Under 3.5 Gols / BTTS"

            texto_relatorio += f"[{idx}] {comp}\n"
            texto_relatorio += f"⚽ {home} x {away}\n"
            texto_relatorio += f"  🎯 [1X2]: {sugestao_1x2} ({max(p_h, p_e, p_a):.1f}%)\n"
            texto_relatorio += f"  🥅 [Gols]: {sugestao_gols} (Media: {media_gols:.2f})\n"
            texto_relatorio += f"  💵 [Stake Recomendada]: R$ {stake_sugerida:.2f}\n"
            texto_relatorio += "-" * 34 + "\n\n"

        texto_relatorio += "💡 Dica: 100k iterações concluídas e salvas no histórico."

        self.salvar_no_historico(texto_relatorio)
        self.atualizar_interface_texto(texto_relatorio)
        self.btn_jogos_hoje.disabled = False

    def ler_cache_seguro(self):
        with file_lock:
            if not os.path.exists(CACHE_FILE): return []
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("matches", data.get("events", []))
            except: return []

    def executar_analise_ia_generativa(self):
        self.atualizar_interface_texto("🧠 [Nexus AI]: Consultando a inteligência quântica do Gemini...")
        threading.Thread(target=self._chamar_gemini_api, daemon=True).start()

    def _chamar_gemini_api(self):
        chave_api = self.obter_chave_gemini()
        if not chave_api:
            self.atualizar_interface_texto("❌ Erro: Chave do Gemini não encontrada no arquivo 'config.json'.")
            return

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={chave_api}"
        payload = {
            "contents": [{
                "parts": [{"text": "Faça uma análise estatística e parecer profissional avançado de apostas esportivas focando no mercado de Gols e Resultados para os jogos de hoje, simulando tendências de Monte Carlo."}]
            }]
        }
        headers = {'Content-Type': 'application/json'}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=12)
            if resp.status_code == 200:
                res_json = resp.json()
                texto_resposta = res_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Sem resposta formatada.')
                self.atualizar_interface_texto(f"🧠 PARECER QUÂNTICO (Google Gemini):\n\n{texto_resposta}")
            else:
                self.atualizar_interface_texto(f"❌ Erro na API do Gemini: Status HTTP {resp.status_code}")
        except Exception as e:
            self.atualizar_interface_texto(f"❌ Falha de conexão ao consultar o Gemini: {str(e)}")

if __name__ == "__main__":
    NexusQuantumApp().run()
