import streamlit as st
import pandas as pd
import pulp
import random

# --- CONFIGURATIE ---
st.set_page_config(
    page_title="Sporza Wielermanager Optimizer",
    page_icon="🚴",
    layout="wide"
)

# --- FUNCTIES ---

@st.cache_data
def load_data():
    """
    Laad de rennersdata. 
    In een productie-omgeving zou je hier live scrapen van PCS of Sporza.
    Nu simuleren we data met logica voor 'oude' en 'nieuwe' prijzen.
    """
    # Simulatie database
    data = [
        {"naam": "Wout van Aert", "oude_prijs": 12.0, "nieuwe_prijs": None, "verwachte_punten": 950, "type": "Kopman"},
        {"naam": "Mathieu van der Poel", "oude_prijs": 12.0, "nieuwe_prijs": None, "verwachte_punten": 980, "type": "Kopman"},
        {"naam": "Tadej Pogacar", "oude_prijs": 12.5, "nieuwe_prijs": 13.0, "verwachte_punten": 1100, "type": "Kopman"},
        {"naam": "Jasper Philipsen", "oude_prijs": 10.0, "nieuwe_prijs": 11.0, "verwachte_punten": 700, "type": "Sprinter"},
        {"naam": "Mads Pedersen", "oude_prijs": 9.0, "nieuwe_prijs": None, "verwachte_punten": 750, "type": "Klassiek"},
        {"naam": "Arnaud De Lie", "oude_prijs": 7.0, "nieuwe_prijs": 8.5, "verwachte_punten": 600, "type": "Sprinter"},
        {"naam": "Tom Pidcock", "oude_prijs": 8.0, "nieuwe_prijs": None, "verwachte_punten": 500, "type": "Klassiek"},
        {"naam": "Christophe Laporte", "oude_prijs": 7.0, "nieuwe_prijs": None, "verwachte_punten": 450, "type": "Knecht/Vrij"},
        {"naam": "Olav Kooij", "oude_prijs": 6.0, "nieuwe_prijs": None, "verwachte_punten": 400, "type": "Sprinter"},
        {"naam": "Matteo Jorgenson", "oude_prijs": 5.0, "nieuwe_prijs": None, "verwachte_punten": 550, "type": "Klassiek"},
        {"naam": "Maxim Van Gils", "oude_prijs": 4.0, "nieuwe_prijs": 5.5, "verwachte_punten": 350, "type": "Klimmer"},
        {"naam": "Thibau Nys", "oude_prijs": 3.0, "nieuwe_prijs": 5.0, "verwachte_punten": 300, "type": "Puncher"},
    ]
    
    # Voeg opvulling toe (Knechten en talenten)
    types = ["Knecht", "Klimmer", "Sprinter", "Vrijbuiter"]
    for i in range(1, 40):
        data.append({
            "naam": f"Peloton Renner {i}", 
            "oude_prijs": round(random.uniform(2, 6), 1), 
            "nieuwe_prijs": None, 
            "verwachte_punten": random.randint(20, 250),
            "type": random.choice(types)
        })

    df = pd.DataFrame(data)
    
    # LOGICA: Als er een nieuwe prijs is (van het nieuwe seizoen), gebruik die. Anders fallback.
    df['actuele_prijs'] = df['nieuwe_prijs'].fillna(df['oude_prijs'])
    df['waarde'] = df['verwachte_punten'] / df['actuele_prijs'] # Points per Million
    
    return df

def optimize_team(df, budget, max_renners, verplichte_renners):
    """
    Draait het Lineair Programmering algoritme.
    """
    prob = pulp.LpProblem("Wielermanager_Optimalisatie", pulp.LpMaximize)
    renners_indices = df.index.tolist()
    
    # Variabelen (0 of 1)
    keuze = pulp.LpVariable.dicts("Keuze", renners_indices, 0, 1, pulp.LpBinary)

    # Doelfunctie: Maximaliseer punten
    prob += pulp.lpSum([df.loc[i, 'verwachte_punten'] * keuze[i] for i in renners_indices])

    # Constraint 1: Budget
    prob += pulp.lpSum([df.loc[i, 'actuele_prijs'] * keuze[i] for i in renners_indices]) <= budget

    # Constraint 2: Aantal renners
    prob += pulp.lpSum([keuze[i] for i in renners_indices]) == max_renners
    
    # Constraint 3: Verplichte renners (Must haves)
    for renner_naam in verplichte_renners:
        idx = df[df['naam'] == renner_naam].index[0]
        prob += choice = keuze[idx] == 1

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    status = pulp.LpStatus[prob.status]
    
    if status == "Optimal":
        geselecteerde_indices = [i for i in renners_indices if keuze[i].varValue == 1]
        return df.loc[geselecteerde_indices].copy(), True
    else:
        return None, False

# --- UI LAYOUT ---

st.title("🚴 Sporza Wielermanager: Auto-Optimizer")
st.markdown("""
Dit dashboard berekent het **wiskundig optimale team** voor de voorjaarsklassiekers. 
Het gebruikt prijzen van vorig jaar totdat de nieuwe bekend zijn.
""")

# Sidebar settings
st.sidebar.header("Team Instellingen")
budget_input = st.sidebar.number_input("Budget (€ Miljoen)", value=100.0, step=0.5)
aantal_renners_input = st.sidebar.number_input("Aantal Renners", value=16, step=1)

# Laad data
df = load_data()

# Interactieve filters
st.sidebar.subheader("Verplichte Renners")
st.sidebar.markdown("Kies renners die **zeker** in je team moeten zitten:")
alle_namen = df['naam'].tolist()
verplichte_renners = st.sidebar.multiselect("Selecteer 'Must Haves'", alle_namen)

# Hoofdactie
if st.button("🚀 Bereken Optimaal Team", type="primary"):
    
    with st.spinner('De supercomputer is aan het rekenen...'):
        beste_team, success = optimize_team(df, budget_input, aantal_renners_input, verplichte_renners)

    if success:
        totaal_prijs = beste_team['actuele_prijs'].sum()
        totaal_punten = beste_team['verwachte_punten'].sum()
        
        # Metrics tonen
        col1, col2, col3 = st.columns(3)
        col1.metric("Verwachte Punten", f"{int(totaal_punten)}")
        col2.metric("Totaal Budget", f"€{totaal_prijs:.1f}M", delta=f"{budget_input - totaal_prijs:.1f}M over")
        col3.metric("Aantal Renners", len(beste_team))
        
        st.subheader("Jouw Selectie")
        
        # Mooie tabel weergave
        st.dataframe(
            beste_team[['naam', 'type', 'actuele_prijs', 'verwachte_punten', 'waarde']].sort_values(by='actuele_prijs', ascending=False),
            column_config={
                "naam": "Renner",
                "type": "Specialiteit",
                "actuele_prijs": st.column_config.NumberColumn("Prijs (M)", format="€%.1f"),
                "verwachte_punten": "Exp. Punten",
                "waarde": st.column_config.ProgressColumn("Efficiency (Pts/€)", format="%.2f", min_value=0, max_value=150)
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Download knop
        csv = beste_team.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Team als CSV", data=csv, file_name="mijn_wielerteam.csv", mime="text/csv")
        
    else:
        st.error("Kon geen geldig team vinden. Waarschijnlijk is je budget te laag voor de verplichte renners die je hebt gekozen.")

# Data inspectie sectie (inklapbaar)
with st.expander("🔍 Bekijk volledige renners database"):
    st.dataframe(df)
