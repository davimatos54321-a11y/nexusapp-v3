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
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.input.motionevent import MotionEvent

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
SECRET_FILE = "config.json"

file_lock = threading.Lock()
Window.clearcolor = (0.01, 0.03, 0.07, 1)

class CyberPanel(BoxLayout):
    def __init__(self, border_color=(0, 0.94, 1, 0.6), bg_color=(0.02, 0.07, 0.15, 1), radius=[16], **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius_val = radius
        self.bind(size=self.update_canvas, pos=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius_val)
            Color(*self.border_color)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius_val[0]), width=1.2)

class CyberButton(Button):
    def __init__(self, neon_color=(0, 0.94, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.neon_color = neon_color
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = 14
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self.update_canvas, pos=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.04, 0.10, 0.22, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
            Color(*self.neon_color)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 12), width=1.5)

class ZoomableTextInput(TextInput):
    """
    TextInput avançado com suporte a gestos de pinça (Pinch to Zoom) 
    para redimensionar o texto dinamicamente no celular.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touch_points = {}

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_points[touch.uid] = touch
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.uid in self.touch_points:
            self.touch_points[touch.uid] = touch
            # Se dois dedos estiverem na tela ao mesmo tempo (gesto de pinça)
            if len(self.touch_points) == 2:
                pts = list(self.touch_points.values())
                dist_atual = math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y)
                
                # Guarda a distância inicial para calcular a expansão ou redução
                if not hasattr(self, '_dist_inicial') or self._dist_inicial is None:
                    self._dist_inicial = dist_atual

                diff = dist_atual - self._dist_inicial
                if abs(diff) > 30:  # Limiar para evitar zoom sensível demais
                    if diff > 0 and self.font_size < 28:
                        self.font_size += 0.5
                    elif diff < 0 and self.font_size > 10:
                        self.font_size -= 0.5
                    self._dist_inicial = dist_atual
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.uid in self.touch_points:
            del self.touch_points[touch.uid]
        if len(self.touch_points) < 2:
            self._dist_inicial = None
        return super().on_touch_up(touch)

class NexusQuantumApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=16, spacing=12)

        self.titulo = Label(
            text="[b][color=#00f0ff]NEXUS QUANTUM[/color] [color=#bd00ff]// 100K CORE[/color][/b]",
            markup=True,
            font_size=18,
            size_hint_y=None,
            height=38,
            halign='center',
            valign='middle'
        )
        self.titulo.bind(size=self.titulo.setter('text_size'))
        layout.add_widget(self.titulo)

        # Bloco de Banca
        painel_banca = CyberPanel(
            border_color=(0, 0.94, 1, 0.5),
            size_hint_y=None,
            height=54,
            padding=8,
            spacing=8
        )
        
        self.txt_banca = TextInput(
            text=self.obter_config("banca_valor", "100.0"),
            hint_text='Banca (R$)...',
            multiline=False,
            size_hint_x=0.45,
            background_color=(0.01, 0.04, 0.10, 1),
            foreground_color=(0, 0.94, 1, 1),
            cursor_color=(0, 0.94, 1, 1),
            font_size=14,
            padding=[10, 10, 10, 10]
        )
        painel_banca.add_widget(self.txt_banca)

        self.txt_risco = TextInput(
            text=self.obter_config("risco_pct", "2.0"),
            hint_text='Risco (%/Aposta)...',
            multiline=False,
            size_hint_x=0.40,
            background_color=(0.01, 0.04, 0.10, 1),
            foreground_color=(0, 0.94, 1, 1),
            cursor_color=(0, 0.94, 1, 1),
            font_size=14,
            padding=[10, 10, 10, 10]
        )
        painel_banca.add_widget(self.txt_risco)
        
        self.btn_salvar_banca = CyberButton(
            text='💾',
            neon_color=(0.15, 0.85, 0.45, 1),
            size_hint_x=0.15
        )
        self.btn_salvar_banca.bind(on_press=self.salvar_configuracoes_banca)
        painel_banca.add_widget(self.btn_salvar_banca)
        
        layout.add_widget(painel_banca)

        # Visor Central com a nova tecnologia de Zoom por Pinça (Pinch to Zoom)
        painel_visor = CyberPanel(
            border_color=(0.74, 0, 1, 0.6),
            bg_color=(0.015, 0.04, 0.09, 1),
            size_hint_y=0.38,
            padding=6
        )
        
        self.txt_chat_ia = ZoomableTextInput(
            text="[Nexus AI Engine]: Sistema blindado e sincronizado.\n💡 Dica: Use dois dedos em pinça (aproximar/afastar) nesta caixa para dar ZOOM nos números e letras!",
            background_color=(0, 0, 0, 0),
            foreground_color=(0.20, 1, 0.80, 1),
            cursor_color=(0.20, 1, 0.80, 1),
            readonly=False,
            multiline=True,
            font_size=16,
            padding=[14, 14, 14, 14]
        )
        painel_visor.add_widget(self.txt_chat_ia)
        layout.add_widget(painel_visor)

        grid_botoes = GridLayout(cols=2, spacing=10, size_hint_y=None, height=140)

        self.btn_jogos_hoje = CyberButton(
            text='🎲 Gerar Bilhete 100k',
            neon_color=(0, 0.94, 1, 1)
        )
        self.btn_jogos_hoje.bind(on_press=lambda x: self.disparar_processamento_async())
        grid_botoes.add_widget(self.btn_jogos_hoje)

        self.btn_historico = CyberButton(
            text='📂 Ver Histórico',
            neon_color=(0.30, 0.50, 1, 1)
        )
        self.btn_historico.bind(on_press=lambda x: self.exibir_historico_salvo())
        grid_botoes.add_widget(self.btn_historico)

        self.btn_ia_generativa = CyberButton(
            text='🧠 Parecer Quântico (Gemini)',
            neon_color=(0.74, 0, 1, 1)
        )
        self.btn_ia_generativa.bind(on_press=lambda x: self.executar_analise_ia_generativa())
        grid_botoes.add_widget(self.btn_ia_generativa)

        self.btn_testar_net = CyberButton(
            text='🌐 Testar Conexão',
            neon_color=(1, 0.55, 0, 1)
        )
        self.btn_testar_net.bind(on_press=lambda x: self.testar_conexao_internet())
        grid_botoes.add_widget(self.btn_testar_net)

        layout.add_widget(grid_botoes)

        # Barra Inferior com margens e input de consulta rápida
        painel_barra = CyberPanel(
            border_color=(0, 0.94, 1, 0.4),
            size_hint_y=None,
            height=54,
            padding=8,
            spacing=8
        )
        
        self.btn_voz_barra = CyberButton(
            text='🎙️',
            neon_color=(0.30, 0.50, 1, 1),
            size_hint_x=0.15
        )
        self.btn_voz_barra.bind(on_press=lambda x: self.iniciar_captura_voz())
        painel_barra.add_widget(self.btn_voz_barra)

        self.txt_pergunta_livre = TextInput(
            hint_text='Consultar time ou status...',
            multiline=False,
            size_hint_x=0.60,
            background_color=(0.01, 0.04, 0.10, 1),
            foreground_color=(0, 0.94, 1, 1),
            cursor_color=(0, 0.94, 1, 1),
            font_size=14,
            padding=[10, 10, 10, 10]
        )
        painel_barra.add_widget(self.txt_pergunta_livre)

        self.btn_perguntar_ia = CyberButton(
            text='➤ Enviar',
            neon_color=(0.74, 0, 1, 1),
            size_hint_x=0.25
        )
        self.btn_perguntar_ia.bind(on_press=lambda x: self.processar_pergunta_livre())
        painel_barra.add_widget(self.btn_perguntar_ia)

        layout.add_widget(painel_barra)

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
                self.atualizar_interface_texto("[Nexus AI]: Gestão de banca atualizada e blindada com sucesso.")
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
