import streamlit as st
import pandas as pd
import pulp

# --- CONFIGURATIE ---
st.set_page_config(page_title="Wielermanager Optimizer", layout="wide")

# --- FUNCTIES ---
def laad_data(uploaded_file):
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file)
    return None

def optimaliseer_team(df, budget, max_renners, verplichte_renners):
    # 1. Het Probleem definiëren (Maximaliseren)
    prob = pulp.LpProblem("Sporza_Team_Selectie", pulp.LpMaximize)

    # 2. Variabelen aanmaken (Elke renner is 0 of 1)
    # We gebruiken de index van de dataframe als ID
    renner_vars = pulp.LpVariable.dicts("Renner", df.index, cat='Binary')

    # 3. Objective Function: Maximaliseer de som van 'Verwachte_Score'
    prob += pulp.lpSum([df.loc[i, 'Verwachte_Score'] * renner_vars[i] for i in df.index])

    # 4. Constraints (De regels)
    
    # A. Budget regel
    prob += pulp.lpSum([df.loc[i, 'Prijs'] * renner_vars[i] for i in df.index]) <= budget
    
    # B. Aantal renners regel
    prob += pulp.lpSum([renner_vars[i] for i in df.index]) == max_renners

    # C. Verplichte renners (Must-haves die jij hebt aangevinkt)
    if verplichte_renners:
        # Zoek de indices van de geselecteerde namen
        for renner_naam in verplichte_renners:
            idx = df[df['Naam'] == renner_naam].index
            if not idx.empty:
                prob += renner_vars[idx[0]] == 1

    # 5. Los het op
    prob.solve()

    # 6. Resultaat verwerken
    if pulp.LpStatus[prob.status] == 'Optimal':
        gekozen_indices = [i for i in df.index if renner_vars[i].varValue == 1]
        return df.loc[gekozen_indices]
    else:
        return None

# --- DE APP INTERFACE ---
st.title("🚴 Sporza Voorjaar Optimizer")
st.markdown("Upload je Excel en laat de wiskunde het perfecte team bouwen.")

# Sidebar voor instellingen
st.sidebar.header("Instellingen")
budget_input = st.sidebar.number_input("Budget (€)", value=100000000, step=1000000, format="%d")
aantal_renners = st.sidebar.number_input("Aantal Renners", value=20, step=1)

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload renners_data.xlsx", type=["xlsx"])

if uploaded_file:
    df = laad_data(uploaded_file)
    
    # Even checken of de kolommen kloppen
    required_cols = ['Naam', 'Prijs', 'Verwachte_Score', 'Team']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Je Excel mist kolommen! Zorg voor: {required_cols}")
    else:
        # Pre-filter optie (Must-haves)
        st.subheader("Jouw Data")
        
        # Laat gebruiker renners kiezen die SOWIESO in het team moeten
        alle_namen = df['Naam'].tolist()
        must_haves = st.multiselect("Welke renners wil je verplicht in je team?", alle_namen)
        
        # Berekening starten
        if st.button("🚀 Bereken Optimaal Team", type="primary"):
            with st.spinner('De computer kraakt de cijfers...'):
                beste_team = optimaliseer_team(df, budget_input, aantal_renners, must_haves)
            
            if beste_team is not None:
                st.success(f"Team gevonden! Totaal verwachte punten: **{beste_team['Verwachte_Score'].sum():.0f}**")
                
                # Mooie weergave van het team
                col1, col2, col3 = st.columns(3)
                col1.metric("Totale Kost", f"€ {beste_team['Prijs'].sum():,}")
                col2.metric("Resterend Budget", f"€ {budget_input - beste_team['Prijs'].sum():,}")
                col3.metric("Aantal Renners", len(beste_team))
                
                st.dataframe(
                    beste_team[['Naam', 'Team', 'Prijs', 'Verwachte_Score']].style.background_gradient(subset=['Verwachte_Score'], cmap="Greens"),
                    use_container_width=True
                )
                
                # Analyse van het team
                st.subheader("Team Balans")
                st.bar_chart(beste_team['Team'].value_counts())
                
            else:
                st.error("Geen oplossing gevonden. Probeer je budget te verhogen of minder 'must-haves' te kiezen.")
else:
    st.info("Upload een Excel bestand in de sidebar om te beginnen.")