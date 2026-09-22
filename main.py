import json
import os
import re
import unicodedata
import urllib.request
import ssl
import time
import random
import math
import socket

# Timeout global de segurança para evitar travamentos de rede na inicialização
socket.setdefaulttimeout(2.5)

ARQUIVO_BANCO_LOGISTICA = "historico_v41.json"
ARQUIVO_BANCO_LOTOFACIL = "historico_lotofacil_db.json"
BACKUP_BANCO_LOGISTICA = "historico_v41_backup.json"
BACKUP_BANCO_LOTOFACIL = "historico_lotofacil_db_backup.json"

AZUL = "\033[1;34m"
AMARELO = "\033[1;33m"
VERDE = "\033[1;32m"
VERMELHO = "\033[1;31m"
MAGENTA = "\033[1;35m"
RESET = "\033[0m"


def normalizar_texto(texto):
    if not texto:
        return ""
    try:
        texto_separado = re.sub(r"([a-zà-ú])([A-ZÀ-Ú])", r"\1 \2", texto)
        return "".join(
            c
            for c in unicodedata.normalize("NFKD", texto_separado.lower())
            if not unicodedata.combining(c)
        ).strip()
    except Exception:
        return str(texto).lower().strip()


def distancia_levenshtein(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        new_distances = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                new_distances.append(distances[i1])
            else:
                new_distances.append(
                    1 + min((distances[i1], distances[i1 + 1], new_distances[-1]))
                )
        distances = new_distances
    return distances[-1]


def palavra_similar(palavra, alvo, max_dist=1):
    if len(palavra) < 4 or len(alvo) < 4:
        return palavra == alvo
    if abs(len(palavra) - len(alvo)) > max_dist:
        return False
    return distancia_levenshtein(palavra, alvo) <= max_dist


def corrigir_ortografia(texto):
    dicionario_referencia = [
        "localizacao", "gps", "onde", "coordenadas", "fome", "comer",
        "comida", "restaurante", "julia", "escola", "filha", "trabalho",
        "buscar", "trazer", "presidente", "populacao", "habitantes",
        "terra", "brasil", "monte mor", "campinas", "cnpem", "sao paulo",
        "sorocaba", "piracicaba", "jundiai", "hortolandia", "quilometros",
        "metros", "status", "limpar", "futebol", "aposta", "apostas",
        "europeus", "times", "jogos", "jogo", "lotofacil", "megasena",
        "quina", "duplasena", "loteria", "concurso", "bilhete", "clima",
        "tempo", "temperatura", "distancia", "qual", "quanto"
    ]
    palavras = texto.split()
    palavras_corrigidas = []
    for p in palavras:
        p_norm = normalizar_texto(p)
        encontrou = False
        for ref in dicionario_referencia:
            if palavra_similar(p_norm, ref, max_dist=1):
                palavras_corrigidas.append(ref)
                encontrou = True
                break
        if not encontrou:
            palavras_corrigidas.append(p)
    return " ".join(palavras_corrigidas)


class SuperCerebroV41:

    def __init__(self, arquivo_db=ARQUIVO_BANCO_LOGISTICA, backup_db=BACKUP_BANCO_LOGISTICA):
        self.arquivo_db = arquivo_db
        self.backup_db = backup_db
        self.mapa_sp = {
            "monte mor": (-22.9442, -47.9031),
            "campinas": (-22.9056, -47.0608),
            "cnpem": (-22.8225, -47.0347),
            "sao paulo": (-23.5505, -46.6333),
            "hortolandia": (-22.8583, -47.2203),
            "sumare": (-22.8183, -47.2683),
            "piracicaba": (-22.7338, -47.6476),
            "sorocaba": (-23.5015, -47.4526)
        }
        try:
            self._carregar_ledger()
        except Exception as e:
            print(f"\n{VERMELHO}[Aviso de Inicialização]: Erro no ledger. A usar estado padrão: {e}{RESET}")
            self.estado_global = {
                "missao_atual": None,
                "ultima_distancia": 0.0,
                "status_tarefa": "IDLE",
                "historico": [],
            }
            self._salvar_ledger()

    def _carregar_ledger(self):
        dados = None
        if os.path.exists(self.arquivo_db):
            try:
                with open(self.arquivo_db, "r", encoding="utf-8") as f:
                    conteudo = f.read().strip()
                    if conteudo:
                        dados = json.loads(conteudo)
            except Exception:
                if os.path.exists(self.backup_db):
                    try:
                        with open(self.backup_db, "r", encoding="utf-8") as f:
                            conteudo_bkp = f.read().strip()
                            if conteudo_bkp:
                                dados = json.loads(conteudo_bkp)
                    except Exception:
                        dados = None

        if dados and isinstance(dados, dict) and "estado_global" in dados:
            self.estado_global = dados["estado_global"]
        else:
            self.estado_global = {
                "missao_atual": None,
                "ultima_distancia": 0.0,
                "status_tarefa": "IDLE",
                "historico": [],
            }
        self._salvar_ledger()

    def _salvar_ledger(self):
        try:
            if os.path.exists(self.arquivo_db):
                try:
                    with open(self.arquivo_db, "r", encoding="utf-8") as f:
                        conteudo_atual = f.read()
                    if conteudo_atual.strip():
                        with open(self.backup_db, "w", encoding="utf-8") as f:
                            f.write(conteudo_atual)
                except Exception:
                    pass

            with open(self.arquivo_db, "w", encoding="utf-8") as f:
                json.dump({"estado_global": self.estado_global}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"\n{VERMELHO}[Erro ao Salvar Ledger]: {e}{RESET}")

    def processar_entrada(self, texto_bruto):
        try:
            if not texto_bruto or not str(texto_bruto).strip():
                return f"\n{VERMELHO}[Sistema Error]: Entrada vazia.{RESET}"

            texto_limpo = re.sub(r"\s+", " ", str(texto_bruto)).strip()
            texto_corrigido = corrigir_ortografia(texto_limpo)
            norm = normalizar_texto(texto_corrigido)

            if norm in ["sair", "exit", "quit"]:
                return "SAIR"

            if norm == "status":
                return (
                    f"\n{VERDE}[Sistema Status]: Ativo e Operacional.\n"
                    f" • Missão: {self.estado_global.get('missao_atual')}\n"
                    f" • Status: {self.estado_global.get('status_tarefa')}{RESET}"
                )

            return (
                f"\n{VERDE}[Módulo Diálogo]:{RESET}\n"
                f" • Processado com sucesso: '{texto_corrigido}'.\n"
                f" • Sistema estabilizado e pronto para uso."
            )
        except Exception as e:
            return f"\n{VERMELHO}[Erro Crítico]: {e}{RESET}"


if __name__ == "__main__":
    try:
        cerebro = SuperCerebroV41()
        print(f"\n{AZUL} SUPER-CÉREBRO: INICIALIZADO COM SUCESSO (V44.5){RESET}\n")
        while True:
            try:
                entrada = input(f"{AZUL}Adailton > {RESET}").strip()
                if not entrada:
                    continue
                resposta = cerebro.processar_entrada(entrada)
                if resposta == "SAIR":
                    break
                print(resposta)
            except (KeyboardInterrupt, EOFError):
                break
    except Exception as init_err:
        print(f"\n{VERMELHO}[Erro Fatal]: {init_err}{RESET}\n")
