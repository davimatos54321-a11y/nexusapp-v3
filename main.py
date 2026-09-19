import streamlit as st
import numpy as np
import sqlite3

# Configuração da página do aplicativo
st.set_page_config(page_title="Gerador de Bilhete Inteligente", page_icon="🎟️", layout="centered")

# ==========================================
# 1. BANCO DE DADOS LOCAL
# ==========================================
class BettingDatabase:
    def __init__(self, db_name="betting_engine.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_xg REAL,
                away_xg REAL,
                status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contextual_factors (
                match_id INTEGER,
                team TEXT,
                key_injuries INTEGER,
                is_reserves BOOLEAN,
                motivation_level TEXT,
                FOREIGN KEY(match_id) REFERENCES matches(id)
            )
        ''')
        self.conn.commit()

    def save_morning_data(self, date, home, away, h_xg, a_xg):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO matches (date, home_team, away_team, home_xg, away_xg, status)
            VALUES (?, ?, ?, ?, ?, 'PENDENTE')
        ''', (date, home, away, h_xg, a_xg))
        self.conn.commit()
        return cursor.lastrowid

    def save_context(self, match_id, team, key_injuries, is_reserves, motivation_level):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO contextual_factors (match_id, team, key_injuries, is_reserves, motivation_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (match_id, team, key_injuries, is_reserves, motivation_level))
        self.conn.commit()

    def close(self):
        self.conn.close()

# ==========================================
# 2. INTELIGÊNCIA CONTEXTUAL E MONTE CARLO
# ==========================================
class ContextualIntelligence:
    @staticmethod
    def calculate_modifiers(key_injuries, is_reserves, motivation_level):
        modifier = 1.0
        modifier -= (key_injuries * 0.04)
        if is_reserves:
            modifier -= 0.18
        if motivation_level == 'BAIXA':
            modifier -= 0.15
        elif motivation_level == 'ALTA':
            modifier += 0.08
        return max(0.5, min(modifier, 1.2))

class MultiMarketMonteCarloEngine:
    def __init__(self, simulations=100000):
        self.simulations = simulations

    def analyze_match(self, h_name, a_name, base_home_xg, base_away_xg, h_mod, a_mod, base_corners=9.5, base_cards=4.5):
        adj_home_xg = base_home_xg * h_mod
        adj_away_xg = base_away_xg * a_mod
        
        home_goals = np.random.poisson(adj_home_xg, self.simulations)
        away_goals = np.random.poisson(adj_away_xg, self.simulations)
        
        home_wins = np.sum(home_goals > away_goals)
        draws = np.sum(home_goals == away_goals)
        away_wins = np.sum(home_goals < away_goals)
        
        p_home = (home_wins / self.simulations) * 100
        p_draw = (draws / self.simulations) * 100
        p_away = (away_wins / self.simulations) * 100

        total_goals = home_goals + away_goals
        p_over_goals = (np.sum(total_goals > 1.5) / self.simulations) * 100

        sim_corners = np.random.poisson(base_corners, self.simulations)
        p_over_corners = (np.sum(sim_corners > 8.5) / self.simulations) * 100

        sim_cards = np.random.poisson(base_cards, self.simulations)
        p_over_cards = (np.sum(sim_cards > 3.5) / self.simulations) * 100

        options = [
            {"market": f"VITÓRIA DO {h_name.upper()}", "prob": p_home},
            {"market": f"VITÓRIA DO {a_name.upper()}", "prob": p_away},
            {"market": "EMPATE", "prob": p_draw},
            {"market": "MAIS DE 1.5 GOLS", "prob": p_over_goals},
            {"market": "MAIS DE 8.5 ESCANTEIOS", "prob": p_over_corners},
            {"market": "MAIS DE 3.5 CARTÕES", "prob": p_over_cards}
        ]

        return max(options, key=lambda x: x["prob"])

# ==========================================
# INTERFACE GRÁFICA DO APLICATIVO
# ==========================================
st.title("🎟️ Gerador de Bilhete Múltipla")
st.markdown("### Sistema Inteligente de Apostas Esportivas")
st.write("Clique no botão abaixo para executar o motor de simulações e montar o seu bilhete com 6 seleções de maior valor.")

stake_value = st.number_input("Valor da Aposta (R$):", min_value=1.0, value=40.0, step=5.0)

if st.button("GERAR APOSTA", type="primary", use_container_width=True):
    with st.spinner("A executar 100.000 simulações e a consultar o banco de dados..."):
        db = BettingDatabase()
        mc = MultiMarketMonteCarloEngine(simulations=100000)

        matches_to_process = [
            {
                "date": "20/09/2026", "home": "Grêmio", "away": "Palmeiras", 
                "h_xg": 1.45, "a_xg": 1.20, "corners": 9.8, "cards": 4.5,
                "h_inj": 2, "h_res": True, "h_mot": "BAIXA", "a_inj": 0, "a_res": False, "a_mot": "ALTA"
            },
            {
                "date": "20/09/2026", "home": "Corinthians", "away": "Fluminense", 
                "h_xg": 1.55, "a_xg": 1.10, "corners": 10.1, "cards": 5.0,
                "h_inj": 0, "h_res": False, "h_mot": "ALTA", "a_inj": 1, "a_res": False, "a_mot": "MEDIA"
            },
            {
                "date": "20/09/2026", "home": "Flamengo", "away": "RB Bragantino", 
                "h_xg": 1.85, "a_xg": 1.05, "corners": 10.5, "cards": 4.2,
                "h_inj": 1, "h_res": False, "h_mot": "ALTA", "a_inj": 2, "a_res": True, "a_mot": "MEDIA"
            },
            {
                "date": "20/09/2026", "home": "Atlético de Madrid", "away": "Real Madrid", 
                "h_xg": 1.35, "a_xg": 1.40, "corners": 9.2, "cards": 5.5,
                "h_inj": 0, "h_res": False, "h_mot": "ALTA", "a_inj": 1, "a_res": False, "a_mot": "ALTA"
            },
            {
                "date": "20/09/2026", "home": "Juventus", "away": "Atalanta", 
                "h_xg": 1.30, "a_xg": 1.25, "corners": 9.5, "cards": 4.8,
                "h_inj": 1, "h_res": False, "h_mot": "ALTA", "a_inj": 0, "a_res": False, "a_mot": "ALTA"
            },
            {
                "date": "20/09/2026", "home": "São Paulo", "away": "Internacional", 
                "h_xg": 1.60, "a_xg": 1.00, "corners": 10.0, "cards": 4.0,
                "h_inj": 0, "h_res": False, "h_mot": "ALTA", "a_inj": 1, "a_res": False, "a_mot": "BAIXA"
            }
        ]

        multiple_slip = []
        combined_odds = 1.0

        for item in matches_to_process:
            m_id = db.save_morning_data(item["date"], item["home"], item["away"], item["h_xg"], item["a_xg"])
            db.save_context(m_id, item["home"], item["h_inj"], item["h_res"], item["h_mot"])
            db.save_context(m_id, item["away"], item["a_inj"], item["a_res"], item["a_mot"])

            h_mod = ContextualIntelligence.calculate_modifiers(item["h_inj"], item["h_res"], item["h_mot"])
            a_mod = ContextualIntelligence.calculate_modifiers(item["a_inj"], item["a_res"], item["a_mot"])

            best_bet = mc.analyze_match(
                item["home"], item["away"], item["h_xg"], item["a_xg"], 
                h_mod, a_mod, base_corners=item["corners"], base_cards=item["cards"]
            )

            prob = best_bet["prob"]
            estimated_odd = round(100.0 / prob, 2) if prob > 0 else 1.01
            combined_odds *= estimated_odd

            multiple_slip.append({
                "match": f"{item['home']} X {item['away']}",
                "date": item["date"],
                "selection": best_bet["market"],
                "probability": round(prob, 2),
                "odd": estimated_odd
            })

        db.close()

        st.success("Bilhete gerado com sucesso!")
        
        # Exibição visual limpa em blocos
        for i, b in enumerate(multiple_slip, 1):
            with st.container():
                st.markdown(f"**JOGO {i}: {b['match']}** ({b['date']})")
                st.info(f"🎯 **Aposta:** {b['selection']}  \n📊 **Probabilidade:** {b['probability']}% | 📈 **Odd Est.:** {b['odd']}")

        potential_return = stake_value * combined_odds

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Odd Total Estimada", f"{combined_odds:.2f}")
        with col2:
            st.metric("Retorno Potencial", f"R$ {potential_return:.2f}")
