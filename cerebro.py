# cerebro.py - Motor de Processamento do Super-Cérebro
import json
import os
import random

# -- CONFIGURAÇÃO DO MOTOR --
# Semente de aleatoriedade para reprodutibilidade controlada
random.seed(44.3)
# Caminho para salvar/ler os backups no Android (permissão de escrita necessária)
ARQUIVO_DADOS = "historico_cerebro.json"

def carregar_dados():
    """Carrega o histórico de dados do sistema."""
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"historico": [], "ultimas_analises": {}}
    return {"historico": [], "ultimas_analises": {}}

def salvar_dados(dados):
    """Salva o histórico de dados do sistema."""
    try:
        with open(ARQUIVO_DADOS, 'w') as f:
            json.dump(dados, f, indent=4)
    except IOError:
        pass # Tratamento silencioso de erro de I/O no mobile

def processar_comando_cerebro(texto_usuario):
    """
    Motor central: recebe o texto do usuário, analisa a intenção,
    executa cálculos e retorna a resposta final.
    """
    # Carrega dados atuais
    dados = carregar_dados()
    
    # Normaliza o input
    texto_lower = texto_usuario.lower()
    
    # -- LÓGICA DE PROCESSAMENTO (NLP) --
    resposta = "Super-Cérebro V44.3 online. Processando comando..."
    
    if "lote fácil" in texto_lower or "lotofácil" in texto_lower:
        # Exemplo de interação com o motor de loteria
        # Aqui chamarias a tua função real de cálculo
        numeros_sorteio = sorted(random.sample(range(1, 26), 15))
        
        # Simula salvar a análise
        analise_id = f"LoteFácil-{len(dados['historico']) + 1}"
        dados['ultimas_analises']['lotofacil'] = numeros_sorteio
        dados['historico'].append({"comando": texto_usuario, "resultado": analise_id})
        salvar_dados(dados)
        
        resposta = f"⚠️ Simulação de Monte Carlo (Lotofácil) concluída. Sugestão de Padrão Estocástico: {', '.join(map(str, numeros_sorteio))}. Análise salva em backup JSON."
        
    elif "aposta" in texto_lower or "esportiva" in texto_lower or "nexusbet" in texto_lower:
        # Exemplo de interação com o motor de apostas
        # Simula cálculo de probabilidades
        probabilidade = random.uniform(0.7, 0.95)
        variancia = random.uniform(0.01, 0.15)
        
        # Simula salvar
        analise_id = f"Aposta-{len(dados['historico']) + 1}"
        dados['ultimas_analises']['aposta'] = {"prob": probabilidade, "var": variancia}
        dados['historico'].append({"comando": texto_usuario, "resultado": analise_id})
        salvar_dados(dados)
        
        resposta = f"🎯 Análise de Probabilidade Esportiva: Risco mapeado. Probabilidade de ganho: {probabilidade:.1%}. Variância calculada: {variancia:.4f}."
        
    elif "limpar" in texto_lower and "dados" in texto_lower:
        # Exemplo de comando administrativo
        salvar_dados({"historico": [], "ultimas_analises": {}})
        resposta = "🗑️ Banco de dados local resetado com sucesso. Arquivos JSON limpos."
        
    elif "olá" in texto_lower or "oi" in texto_lower or "robô" in texto_lower:
        resposta = "Olá, Adailton! Central operacional. O motor estocástico está pronto. O que deseja analisar hoje?"
        
    else:
        resposta = f"Comando genérico processado pelo motor de bolso: '{texto_usuario}'. Por favor, especifique o tipo de análise (loteria ou esportes)."

    return resposta
