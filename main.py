# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import subprocess
import threading
import time
import urllib.request

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    TEM_CRYPTOGRAPHY = True
except Exception:
    TEM_CRYPTOGRAPHY = False

try:
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.textinput import TextInput
    TEM_KIVY = True
except Exception:
    TEM_KIVY = False


# ==================== CONFIGURAÇÕES DO APP ====================
MEU_NOME = "Adailton"
MEU_NUMERO = "+5519999999999"
DDI_PADRAO = "55"
DDD_PADRAO = "19"

# URL do seu servidor de sinalização WebRTC/mensagens (ex: https://seu-servidor.com)
URL_SINALIZACAO_PADRAO = ""

SERVIDORES_ICE = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
]


def _resolver_pasta_dados() -> str:
    candidatos = [
        "/storage/emulated/0/Download/JanusCallCommercial",
        os.path.expanduser("~/Downloads/JanusCallCommercial"),
        os.path.join(os.getcwd(), "janus_call_data"),
    ]
    for pasta in candidatos:
        try:
            os.makedirs(pasta, exist_ok=True)
            teste_arq = os.path.join(pasta, ".write_test")
            with open(teste_arq, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(teste_arq)
            return pasta
        except Exception:
            continue
    return os.getcwd()


PASTA_DADOS = _resolver_pasta_dados()
CAMINHO_DB = os.path.join(PASTA_DADOS, "janus_call.sqlite")
CAMINHO_CHAVE_PRIV = os.path.join(PASTA_DADOS, "chave_privada_x25519.pem")


def normalizar_e164(numero: str, ddi_padrao: str = DDI_PADRAO, ddd_padrao: str = DDD_PADRAO) -> str:
    limpo = "".join(ch for ch in (numero or "").strip() if ch.isdigit())
    if not limpo:
        return ""
    if (numero or "").strip().startswith("+"):
        return f"+{limpo}"
    if len(limpo) in (8, 9) and ddd_padrao and ddi_padrao:
        return f"+{ddi_padrao}{ddd_padrao}{limpo}"
    if len(limpo) in (10, 11) and ddi_padrao:
        return f"+{ddi_padrao}{limpo}"
    return f"+{limpo}"


# ==================== AGENTE GUARDIÃO DE RESILIÊNCIA ====================
class AgenteResilienciaJanus:
    """Agente leve de regras para prevenir falhas de estado, rede e entrada."""

    def __init__(self):
        self.falhas_sinalizacao = 0
        self.ultimo_erro_rede = ""

    def validar_destino(self, numero_raw: str):
        num = normalizar_e164(numero_raw)
        if not num:
            return False, "", "Destino inválido ou vazio. Informe DDD + número ou formato +E164."
        digitos = "".join(ch for ch in num if ch.isdigit())
        if len(digitos) < 10:
            return False, num, f"Número curto ({num}). Verifique DDI/DDD."
        return True, num, "Destino válido."

    def pode_iniciar_chamada(self, estado_atual: str, destino_atual: str):
        if estado_atual == "EM_CHAMADA":
            return False, f"Já existe chamada ativa com {destino_atual}. Encerre antes de nova ligação."
        if estado_atual == "CHAMANDO":
            return False, f"Já há tentativa em andamento para {destino_atual}."
        return True, "Pronto para iniciar."

    def registrar_falha_rede(self, erro_msg: str):
        self.falhas_sinalizacao += 1
        self.ultimo_erro_rede = erro_msg

    def registrar_sucesso_rede(self):
        self.falhas_sinalizacao = 0
        self.ultimo_erro_rede = ""

    def recomendar_rota(self, url_sinalizacao: str, midia: str):
        if not url_sinalizacao:
            return "FALLBACK_LOCAL", "Sem servidor de sinalização; usando modo local ou LIGAR (TEL)."
        if midia == "VIDEO" and self.falhas_sinalizacao >= 2:
            return "VOZ_PREFERENCIAL", "Múltiplas falhas de rede; priorize VOZ ou LIGAR (TEL)."
        return "WEBRTC_HTTP", "Rota de sinalização disponível."


# ==================== CRIPTOGRAFIA E2EE (X25519 + HKDF + AES-256-GCM + FALLBACK) ====================
class CofreSeguranca:
    def __init__(self, caminho_chave_priv: str):
        self.caminho_chave = caminho_chave_priv
        self.modo = "X25519-AESGCM" if TEM_CRYPTOGRAPHY else "FALLBACK-HMAC"
        self._priv = None
        self._pub = None
        self._fallback_secret = self._carregar_ou_gerar_fallback()

        if TEM_CRYPTOGRAPHY:
            try:
                self._priv = self._carregar_ou_gerar_chave_x25519()
                self._pub = self._priv.public_key()
            except Exception:
                self.modo = "FALLBACK-HMAC"
                self._priv = None
                self._pub = None

    def _carregar_ou_gerar_fallback(self) -> bytes:
        caminho_fb = self.caminho_chave + ".fb.key"
        if os.path.isfile(caminho_fb):
            with open(caminho_fb, "rb") as f:
                raw = f.read()
                if len(raw) >= 32:
                    return raw[:32]
        chave = os.urandom(32)
        with open(caminho_fb, "wb") as f:
            f.write(chave)
        return chave

    def _carregar_ou_gerar_chave_x25519(self):
        if os.path.isfile(self.caminho_chave):
            with open(self.caminho_chave, "rb") as f:
                return serialization.load_pem_private_key(f.read(), password=None)
        priv = x25519.X25519PrivateKey.generate()
        pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with open(self.caminho_chave, "wb") as f:
            f.write(pem)
        return priv

    def chave_publica_b64(self) -> str:
        if self.modo == "X25519-AESGCM" and self._pub is not None:
            raw = self._pub.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            return base64.b64encode(raw).decode("ascii")
        digest = hashlib.sha256(self._fallback_secret).digest()
        return base64.b64encode(digest).decode("ascii")

    def derivar_chave_sessao(self, pub_remota_b64: str, info: bytes = b"JanusCall-v1") -> bytes:
        if self.modo == "X25519-AESGCM" and self._priv is not None:
            pub_bytes = base64.b64decode(pub_remota_b64.encode("ascii"))
            pub_remota = x25519.X25519PublicKey.from_public_bytes(pub_bytes)
            segredo = self._priv.exchange(pub_remota)
            return HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=info,
            ).derive(segredo)
        return hashlib.pbkdf2_hmac(
            "sha256",
            self._fallback_secret,
            pub_remota_b64.encode("utf-8"),
            100000,
            dklen=32,
        )

    def cifrar_pacote(self, chave_aes: bytes, texto_plano: str, aad: str = "") -> str:
        if self.modo == "X25519-AESGCM":
            nonce = os.urandom(12)
            ct = AESGCM(chave_aes).encrypt(
                nonce,
                texto_plano.encode("utf-8"),
                aad.encode("utf-8") if aad else None,
            )
            return base64.b64encode(nonce + ct).decode("ascii")

        nonce = os.urandom(12)
        pt = texto_plano.encode("utf-8")
        stream = bytearray()
        contador = 0
        while len(stream) < len(pt):
            bloco = hmac.new(
                chave_aes,
                nonce + contador.to_bytes(4, "big") + aad.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            stream.extend(bloco)
            contador += 1
        cifrado = bytes(a ^ b for a, b in zip(pt, stream[: len(pt)]))
        tag = hmac.new(
            chave_aes,
            nonce + cifrado + aad.encode("utf-8"),
            hashlib.sha256,
        ).digest()[:16]
        return base64.b64encode(nonce + cifrado + tag).decode("ascii")


# ==================== BANCO DE DADOS (CONTATOS E CHAMADAS) ====================
class BancoChamadas:
    def __init__(self, caminho_db: str):
        self.caminho_db = caminho_db
        self.lock = threading.Lock()
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.caminho_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.lock, self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contatos (
                    numero TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    pubkey_b64 TEXT DEFAULT '',
                    atualizado_em INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL,
                    canal TEXT NOT NULL,
                    tipo_midia TEXT NOT NULL,
                    status TEXT NOT NULL,
                    criado_em INTEGER NOT NULL
                )
                """
            )

    def salvar_contato(self, numero: str, nome: str = "", pubkey_b64: str = ""):
        num = normalizar_e164(numero)
        if not num:
            return None
        agora = int(time.time())
        with self.lock, self._conn() as conn:
            atual = conn.execute(
                "SELECT nome, pubkey_b64 FROM contatos WHERE numero = ?", (num,)
            ).fetchone()
            nome_final = (nome or "").strip() or (atual["nome"] if atual else num)
            pub_final = (pubkey_b64 or "").strip() or (atual["pubkey_b64"] if atual else "")
            conn.execute(
                """
                INSERT INTO contatos (numero, nome, pubkey_b64, atualizado_em)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(numero) DO UPDATE SET
                    nome = excluded.nome,
                    pubkey_b64 = excluded.pubkey_b64,
                    atualizado_em = excluded.atualizado_em
                """,
                (num, nome_final, pub_final, agora),
            )
        return num

    def listar_contatos(self):
        with self.lock, self._conn() as conn:
            rows = conn.execute(
                "SELECT numero, nome, pubkey_b64 FROM contatos ORDER BY nome ASC"
            ).fetchall()
        return [
            {"numero": r["numero"], "nome": r["nome"], "pubkey_b64": r["pubkey_b64"]}
            for r in rows
        ]

    def registrar_chamada(self, numero: str, canal: str, tipo_midia: str, status: str):
        num = normalizar_e164(numero) or (numero or "").strip() or "DESCONHECIDO"
        with self.lock, self._conn() as conn:
            conn.execute(
                """
                INSERT INTO historico (numero, canal, tipo_midia, status, criado_em)
                VALUES (?, ?, ?, ?, ?)
                """,
                (num, canal, tipo_midia, status, int(time.time())),
            )

    def listar_historico(self, limite: int = 15):
        with self.lock, self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, numero, canal, tipo_midia, status, criado_em
                FROM historico
                ORDER BY id DESC
                LIMIT ?
                """,
                (limite,),
            ).fetchall()
        return [dict(r) for r in rows]


# ==================== MOTOR DE CHAMADAS INTELIGENTE ====================
class CentralChamadas:
    def __init__(self, meu_numero: str, on_log=None):
        self.meu_numero = normalizar_e164(meu_numero)
        self.cofre = CofreSeguranca(CAMINHO_CHAVE_PRIV)
        self.db = BancoChamadas(CAMINHO_DB)
        self.agente = AgenteResilienciaJanus()
        self.on_log = on_log or (lambda s: print(s))

        self.lock = threading.Lock()
        self.url_sinalizacao = URL_SINALIZACAO_PADRAO
        self.estado = "LIVRE"
        self.midia = "VOZ"
        self.destino_atual = ""
        self.inicio_chamada_em = None

    def log(self, msg: str):
        self.on_log(msg)

    def autodiagnostico(self):
        total_contatos = len(self.db.listar_contatos())
        total_hist = len(self.db.listar_historico(limite=100))
        self.log(
            f"[AGENTE] OK | Pasta: {PASTA_DADOS} | Crypto: {self.cofre.modo} "
            f"| Contatos: {total_contatos} | Histórico: {total_hist}"
        )

    def configurar_servidor(self, url: str):
        limpa = (url or "").strip().rstrip("/")
        with self.lock:
            self.url_sinalizacao = limpa
        self.agente.registrar_sucesso_rede()
        self.log(f"[SERVIDOR] Sinalização configurada: {limpa or 'nenhuma'}")

    def ligar_webrtc(self, numero_raw: str, midia: str = "VOZ"):
        ok_dest, num, msg_dest = self.agente.validar_destino(numero_raw)
        if not ok_dest:
            self.log(f"[AGENTE] {msg_dest}")
            return

        midia = (midia or "VOZ").upper()
        with self.lock:
            pode, motivo = self.agente.pode_iniciar_chamada(self.estado, self.destino_atual)
            if not pode:
                self.log(f"[AGENTE] {motivo}")
                return
            self.estado = "CHAMANDO"
            self.midia = midia
            self.destino_atual = num
            self.inicio_chamada_em = None
            url = self.url_sinalizacao

        rota, dica = self.agente.recomendar_rota(url, midia)
        self.db.registrar_chamada(num, "WEBRTC", midia, "CHAMANDO")
        self.log(f"[CHAMADA {midia}] Destino {num} | Rota: {rota} ({dica})")

        if not url:
            self.log(
                "[AGENTE DICA] Sem URL de sinalização. Use LIGAR (TEL) para rede telefônica "
                "ou informe a URL do servidor para sinalização remota."
            )
            return

        def _enviar_convite():
            try:
                payload = {
                    "de": self.meu_numero,
                    "para": num,
                    "midia": midia,
                    "cipher_mode": self.cofre.modo,
                    "pubkey": self.cofre.chave_publica_b64(),
                    "ice_servers": SERVIDORES_ICE,
                }
                req = urllib.request.Request(
                    f"{url}/call/invite",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "X-Janus-Caller": self.meu_numero,
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    self.agente.registrar_sucesso_rede()
                    self.log(
                        f"[SINALIZAÇÃO] Convite {midia} enviado para {num} (HTTP {resp.status})."
                    )
            except Exception as e:
                self.agente.registrar_falha_rede(str(e))
                self.log(
                    f"[AGENTE ALERTA] Falha de sinalização ({e}). "
                    "Você pode atender/simular sessão ou usar LIGAR (TEL)."
                )

        threading.Thread(target=_enviar_convite, daemon=True).start()

    def atender_chamada(self):
        with self.lock:
            num = self.destino_atual
            if not num:
                self.log("[AGENTE] Nenhuma chamada pendente para atender.")
                return
            self.estado = "EM_CHAMADA"
            self.inicio_chamada_em = int(time.time())
            midia = self.midia
        self.db.registrar_chamada(num, "WEBRTC", midia, "ATENDIDA")
        self.log(f"[EM CHAMADA {midia}] Conectado com {num}.")

    def desligar_chamada(self):
        with self.lock:
            num = self.destino_atual
            midia = self.midia
            inicio = self.inicio_chamada_em
            self.estado = "LIVRE"
            self.destino_atual = ""
            self.inicio_chamada_em = None

        duracao_txt = ""
        if inicio:
            seg = max(0, int(time.time()) - inicio)
            duracao_txt = f" ({seg // 60:02d}:{seg % 60:02d})"

        if num:
            self.db.registrar_chamada(num, "WEBRTC", midia, f"ENCERRADA{duracao_txt}")
        self.log(f"[CHAMADA ENCERRADA]{duracao_txt} Linha liberada.")

    def ligar_telefone_padrao(self, numero_raw: str) -> bool:
        ok_dest, num, msg_dest = self.agente.validar_destino(numero_raw)
        if not ok_dest:
            self.log(f"[AGENTE] {msg_dest}")
            return False

        self.db.registrar_chamada(num, "TELEFONE_NATIVO", "VOZ", "DISCADO")
        self.log(f"[TELEFONE] Abrindo discador padrão para {num}...")

        try:
            subprocess.run(
                ["am", "start", "-a", "android.intent.action.DIAL", "-d", f"tel:{num}"],
                check=True,
            )
            return True
        except Exception as e:
            self.log(f"[AGENTE AVISO] Discador nativo indisponível neste ambiente ({e}).")
            return False


# ==================== INTERFACE DO APLICATIVO (KIVY) ====================
if TEM_KIVY:
    class JanusCallApp(App):
        def build(self):
            Window.clearcolor = (0.05, 0.07, 0.11, 1)
            self.central = CentralChamadas(MEU_NUMERO, on_log=self._log_ui)

            raiz = BoxLayout(orientation="vertical", padding=12, spacing=10)

            raiz.add_widget(
                Label(
                    text=f"JANUS CALL  |  {MEU_NOME} ({MEU_NUMERO})",
                    size_hint_y=None,
                    height=44,
                    bold=True,
                    color=(0.35, 0.8, 1, 1),
                )
            )

            self.txt_numero = TextInput(
                hint_text="Número (ex: 19988887777 ou +5519988887777)",
                multiline=False,
                size_hint_y=None,
                height=52,
                font_size=19,
            )
            raiz.add_widget(self.txt_numero)

            self.txt_nome = TextInput(
                hint_text="Nome do contato (opcional)",
                multiline=False,
                size_hint_y=None,
                height=44,
            )
            raiz.add_widget(self.txt_nome)

            self.txt_servidor = TextInput(
                hint_text="URL servidor sinalização (ex: https://api.seudominio.com)",
                multiline=False,
                size_hint_y=None,
                height=44,
            )
            raiz.add_widget(self.txt_servidor)

            btn_srv = Button(
                text="SALVAR SERVIDOR",
                size_hint_y=None,
                height=44,
                background_color=(0.14, 0.44, 0.85, 1),
                bold=True,
            )
            btn_srv.bind(
                on_press=lambda _: self.central.configurar_servidor(self.txt_servidor.text)
            )
            raiz.add_widget(btn_srv)

            l1 = BoxLayout(size_hint_y=None, height=56, spacing=8)
            b_voz = Button(
                text="CHAMAR VOZ", background_color=(0.12, 0.65, 0.35, 1), bold=True
            )
            b_voz.bind(
                on_press=lambda _: self.central.ligar_webrtc(self.txt_numero.text, "VOZ")
            )

            b_vid = Button(
                text="VIDEOCHAMADA", background_color=(0.15, 0.45, 0.85, 1), bold=True
            )
            b_vid.bind(
                on_press=lambda _: self.central.ligar_webrtc(self.txt_numero.text, "VIDEO")
            )

            l1.add_widget(b_voz)
            l1.add_widget(b_vid)
            raiz.add_widget(l1)

            l2 = BoxLayout(size_hint_y=None, height=54, spacing=8)
            b_at = Button(
                text="ATENDER", background_color=(0.18, 0.72, 0.48, 1), bold=True
            )
            b_at.bind(on_press=lambda _: self.central.atender_chamada())

            b_de = Button(
                text="DESLIGAR", background_color=(0.82, 0.22, 0.22, 1), bold=True
            )
            b_de.bind(on_press=lambda _: self.central.desligar_chamada())

            b_tel = Button(
                text="LIGAR (TEL)", background_color=(0.20, 0.52, 0.90, 1), bold=True
            )
            b_tel.bind(
                on_press=lambda _: self.central.ligar_telefone_padrao(self.txt_numero.text)
            )

            l2.add_widget(b_at)
            l2.add_widget(b_de)
            l2.add_widget(b_tel)
            raiz.add_widget(l2)

            l3 = BoxLayout(size_hint_y=None, height=46, spacing=8)
            b_sal = Button(
                text="SALVAR CONTATO", background_color=(0.16, 0.40, 0.75, 1), bold=True
            )
            b_sal.bind(on_press=self._salvar_contato)

            b_ver = Button(
                text="AGENDA", background_color=(0.16, 0.40, 0.75, 1), bold=True
            )
            b_ver.bind(on_press=self._ver_agenda)

            b_hist = Button(
                text="HISTÓRICO", background_color=(0.16, 0.40, 0.75, 1), bold=True
            )
            b_hist.bind(on_press=self._ver_historico)

            l3.add_widget(b_sal)
            l3.add_widget(b_ver)
            l3.add_widget(b_hist)
            raiz.add_widget(l3)

            self.lbl_log = Label(
                text="",
                size_hint_y=None,
                halign="left",
                valign="top",
                color=(0.65, 0.88, 1, 1),
            )
            self.lbl_log.bind(
                texture_size=lambda inst, val: setattr(
                    inst, "height", max(200, val[1] + 20)
                )
            )
            self.lbl_log.bind(
                size=lambda inst, val: setattr(inst, "text_size", (val[0], None))
            )

            scroll = ScrollView(size_hint=(1, 1))
            scroll.add_widget(self.lbl_log)
            raiz.add_widget(scroll)

            self.central.autodiagnostico()
            return raiz

        def _log_ui(self, msg: str):
            Clock.schedule_once(lambda _: self._append(msg), 0)

        def _append(self, msg: str):
            self.lbl_log.text += f"{msg}\n"

        def _salvar_contato(self, _):
            ok, num, msg = self.central.agente.validar_destino(self.txt_numero.text)
            if not ok:
                self._append(f"[AGENTE] {msg}")
                return
            salvo = self.central.db.salvar_contato(num, self.txt_nome.text)
            if salvo:
                self._append(f"[AGENDA] Contato salvo: {salvo}")

        def _ver_agenda(self, _):
            contatos = self.central.db.listar_contatos()
            if not contatos:
                self._append("[AGENDA] Vazia.")
                return
            linhas = ["[CONTATOS]:"] + [
                f" - {c['nome']} ({c['numero']})" for c in contatos
            ]
            self._append("\n".join(linhas))

        def _ver_historico(self, _):
            itens = self.central.db.listar_historico(limite=15)
            if not itens:
                self._append("[HISTÓRICO] Sem registros.")
                return
            linhas = ["[HISTÓRICO]:"] + [
                f" - [{it['canal']}/{it['tipo_midia']}] {it['numero']} -> {it['status']}"
                for it in itens
            ]
            self._append("\n".join(linhas))


if __name__ == "__main__":
    if TEM_KIVY:
        JanusCallApp().run()
    else:
        print("Kivy não instalado neste ambiente.")
