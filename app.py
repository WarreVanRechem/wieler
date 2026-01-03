import streamlit as st
import pandas as pd
import pulp
import os
from datetime import datetime, date

# --- CONFIGURATIE ---
st.set_page_config(
    page_title="Sporza Wielermanager 2026 Optimizer",
    page_icon="🚴",
    layout="wide"
)

# Datum van Omloop Het Nieuwsblad 2026 (Start Seizoen)
START_SEIZOEN = datetime(2026, 2, 28, 11, 0) # 28 feb 2026, 11:00

# --- SESSION STATE ---
if 'optimized_team' not in st.session_state:
    st.session_state['optimized_team'] = None
if 'optimization_success' not in st.session_state:
    st.session_state['optimization_success'] = False

# --- FUNCTIES ---

def get_countdown():
    """Berekent de tijd tot de start van het seizoen."""
    now = datetime.now()
    delta = START_SEIZOEN - now
    
    if delta.days < 0:
        return "Het seizoen is begonnen! 🏁"
    else:
        return f"{delta.days} dagen, {delta.seconds // 3600} uur tot de Omloop"

@st.cache_data(ttl=3600)
def load_data():
    """
    Laadt data. Als renners.csv niet bestaat, laden we historische data
    als 'oefenmateriaal' voor de pre-season fase.
    """
    csv_file = "renners.csv"
    
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            # Normaliseer kolomnamen
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Valideer kolommen
            required = {'naam', 'prijs', 'verwachte_punten'}
            if not required.issubset(df.columns):
                st.error(f"CSV Fout. Vereiste kolommen: {required}")
                return pd.DataFrame()
            
            if 'type' not in df.columns:
                df['type'] = 'Onbekend'
                
            df['actuele_prijs'] = df['prijs']
            df['waarde'] = df['verwachte_punten'] / df['actuele_prijs']
            return df
            
        except Exception as e:
            st.error(f"Fout bij lezen CSV: {e}")
            return pd.DataFrame()

    else:
        # FALLBACK DATA (Vorig jaar / Schattingen)
        # Zodat je de app kunt testen terwijl je wacht op de lancering
        data = [
            {"naam": "Mathieu van der Poel", "type": "Kopman", "prijs": 12.0, "verwachte_punten": 1150},
            {"naam": "Tadej Pogacar", "type": "Kopman", "prijs": 12.5, "verwachte_punten": 900},
            {"naam": "Wout van Aert", "type": "Kopman", "prijs": 12.0, "verwachte_punten": 950},
            {"naam": "Jasper Philipsen", "type": "Sprinter", "prijs": 11.0, "verwachte_punten": 850},
            {"naam": "Mads Pedersen", "type": "Klassiek", "prijs": 10.0, "verwachte_punten": 920},
            {"naam": "Tom Pidcock", "type": "Klassiek", "prijs": 9.0, "verwachte_punten": 550},
            {"naam": "Arnaud De Lie", "type": "Sprinter", "prijs": 8.0, "verwachte_punten": 600},
            {"naam": "Olav Kooij", "type": "Sprinter", "prijs": 7.0, "verwachte_punten": 450},
            {"naam": "Maxim Van Gils", "type": "Klimmer", "prijs": 6.0, "verwachte_punten": 520},
            {"naam": "Thibau Nys", "type": "Puncher", "prijs": 5.0, "verwachte_punten": 350},
            {"naam": "Tim Merlier", "type": "Sprinter", "prijs": 6.0, "verwachte_punten": 440},
            {"naam": "Biniam Girmay", "type": "Sprinter", "prijs": 6.5, "verwachte_punten": 480},
        ]
        # Opvulling
        import random
        for i in range(1, 40):
            data.append({
                "naam": f"Knecht/Talent {i}", 
                "type": "Knecht", 
                "prijs": round(random.uniform(2, 5), 1), 
                "verwachte_punten": random.randint(50, 200)
            })
            
        df = pd.DataFrame(data)
        df['actuele_prijs'] = df['prijs']
        df['waarde'] = df['verwachte_punten'] / df['actuele_prijs']
        return df

def optimize_team(df, budget, max_renners, verplichte_renners):
    # Solver setup
    prob = pulp.LpProblem("WielerTeam2026", pulp.LpMaximize)
    indices = df.index.tolist()
    keuze = pulp.LpVariable.dicts("Selecteer", indices, 0, 1, pulp.LpBinary)

    # Doelfunctie: Max punten
    prob += pulp.lpSum([df.loc[i, 'verwachte_punten'] * keuze[i] for i in indices])

    # Constraints
    prob += pulp.lpSum([df.loc[i, 'actuele_prijs'] * keuze[i] for i in indices]) <= budget
    prob += pulp.lpSum([keuze[i] for i in indices]) == max_renners
    
    # Verplichte renners
    for naam in verplichte_renners:
        matches = df[df['naam'] == naam].index
        if len(matches) > 0:
            prob += keuze[matches[0]] == 1

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if pulp.LpStatus[prob.status] == "Optimal":
        selection = [i for i in indices if keuze[i].varValue == 1]
        return df.loc[selection].copy(), True
    return None, False

# --- UI LAYOUT ---

# Header met Countdown
col_title, col_count = st.columns([2, 1])
with col_title:
    st.title("🚴 Sporza Wielermanager 2026")
    st.caption("De officieuze team optimizer")

with col_count:
    st.info(f"⏱️ **Countdown:**\n\n{get_countdown()}")

st.divider()

# Sidebar
st.sidebar.header("⚙️ Instellingen")
budget = st.sidebar.number_input("Budget (€M)", value=100.0, step=0.5)
aantal = st.sidebar.number_input("Aantal Renners", value=16, step=1)

# Data Laden
df = load_data()

# Status melding over data
if not os.path.exists("renners.csv"):
    st.warning("""
    ⚠️ **Let op:** De officiële Sporza prijzen voor 2026 zijn nog niet beschikbaar. 
    Deze app gebruikt nu **geschatte data** of data van vorig jaar om te oefenen.
    Upload `renners.csv` zodra de prijzen bekend zijn!
    """)
else:
    st.success("✅ Actuele data (renners.csv) geladen.")

# Selectie Logica
if not df.empty:
    st.sidebar.subheader("Verplichte Renners")
    must_haves = st.sidebar.multiselect("Wie moet er zeker mee?", df['naam'].sort_values())

    c1, c2 = st.sidebar.columns(2)
    if c1.button("🚀 Optimaliseer", type="primary"):
        with st.spinner("Puzzelen..."):
            res, ok = optimize_team(df, budget, aantal, must_haves)
            st.session_state['optimized_team'] = res
            st.session_state['optimization_success'] = ok
    
    if c2.button("Reset"):
        st.session_state['optimized_team'] = None
        st.session_state['optimization_success'] = False
        st.rerun()

    # Resultaat Weergave
    if st.session_state['optimization_success'] and st.session_state['optimized_team'] is not None:
        team = st.session_state['optimized_team']
        
        # KPI's
        k1, k2, k3 = st.columns(3)
        k1.metric("Verwachte Punten", int(team['verwachte_punten'].sum()))
        kost = team['actuele_prijs'].sum()
        k2.metric("Kosten", f"€{kost:.1f}M", delta=f"€{budget - kost:.1f}M over")
        k3.metric("Renners", len(team))
        
        # Grafische weergave verdeling
        with st.expander("📊 Zie verdeling budget"):
            st.bar_chart(team, x="naam", y="actuele_prijs")

        st.subheader("Jouw Winnende Selectie")
        st.dataframe(
            team[['naam', 'type', 'actuele_prijs', 'verwachte_punten', 'waarde']].sort_values('actuele_prijs', ascending=False),
            column_config={
                "naam": "Renner",
                "actuele_prijs": st.column_config.NumberColumn("Prijs", format="€%.1f"),
                "waarde": st.column_config.ProgressColumn("Punten/Miljoen", min_value=0, max_value=200, format="%.1f")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Export
        csv = team.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download Selectie", csv, "mijn_team_2026.csv", "text/csv")

else:
    st.error("Geen data beschikbaar.")
