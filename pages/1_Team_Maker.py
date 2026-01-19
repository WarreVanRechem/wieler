import streamlit as st
import pandas as pd
import pulp
import os

st.set_page_config(page_title="Team Maker", page_icon="🏆", layout="wide")

# --- 1. DATA LADEN (De veilige manier) ---
def laad_data():
    # Zoek het bestand in de hoofdmap, ook al draaien we in de 'pages' map
    huidige_map = os.path.dirname(__file__)
    pad_naar_excel = os.path.join(huidige_map, "..", "renners_data.xlsx")
    
    if not os.path.exists(pad_naar_excel):
        return None
    
    try:
        return pd.read_excel(pad_naar_excel).fillna(0)
    except:
        return None

# --- 2. DE REKENMACHINE (Het algoritme) ---
def optimaliseer_team(df, budget, max_renners, verplichte_renners, race_kolommen):
    # Bereken totaalscore (som van alle ingevulde races)
    df['Totaal_Score'] = df[race_kolommen].sum(axis=1)

    # Maak het optimalisatie probleem aan
    prob = pulp.LpProblem("Sporza_Team", pulp.LpMaximize)
    
    # Variabelen: Elke renner is een 'switch' (0 = niet in team, 1 = wel in team)
    renner_vars = pulp.LpVariable.dicts("Renner", df.index, cat='Binary')

    # Doel: Maximaliseer de som van scores
    prob += pulp.lpSum([df.loc[i, 'Totaal_Score'] * renner_vars[i] for i in df.index])

    # Regel 1: Budget limiet
    prob += pulp.lpSum([df.loc[i, 'Prijs'] * renner_vars[i] for i in df.index]) <= budget
    
    # Regel 2: Exact aantal renners
    prob += pulp.lpSum([renner_vars[i] for i in df.index]) == max_renners

    # Regel 3: Verplichte renners (Must-haves)
    for renner_naam in verplichte_renners:
        idx = df[df['Naam'] == renner_naam].index
        if not idx.empty:
            prob += renner_vars[idx[0]] == 1

    # Los op!
    prob.solve()

    if pulp.LpStatus[prob.status] == 'Optimal':
        indices = [i for i in df.index if renner_vars[i].varValue == 1]
        return df.loc[indices]
    return None

# --- 3. DE APP INTERFACE (Wat je ziet op het scherm) ---
st.title("🏆 Bouw het winnende team")

df = laad_data()

if df is not None:
    # Kolommen detecteren die koersen zijn (alles behalve Naam, Team, Prijs, Type)
    basis_kolommen = ['Naam', 'Team', 'Prijs', 'Type', 'Totaal_Score']
    race_kolommen = [col for col in df.columns if col not in basis_kolommen]

    # --- Sidebar Instellingen ---
    st.sidebar.header("⚙️ Instellingen")
    budget_input = st.sidebar.number_input("Budget (€)", value=100000000, step=1000000, format="%d")
    aantal_renners = st.sidebar.number_input("Aantal Renners", value=20, step=1)
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"Gevonden koersen in data: {len(race_kolommen)}")

    # --- Hoofdscherm ---
    st.subheader("1. Kies je zekerheden")
    must_haves = st.multiselect("Welke renners wil je SOWIESO in je team?", df['Naam'].tolist())

    st.subheader("2. Laat de AI rekenen")
    if st.button("🚀 Genereer Optimaal Team", type="primary"):
        
        with st.spinner('De computer puzzelt de beste combinatie...'):
            beste_team = optimaliseer_team(df, budget_input, aantal_renners, must_haves, race_kolommen)

        if beste_team is not None:
            totaal_punten = beste_team['Totaal_Score'].sum()
            st.balloons()
            st.success(f"✅ Team gevonden! Verwachte totaalscore: **{totaal_punten:.0f}**")

            # Scorebord
            col1, col2, col3 = st.columns(3)
            col1.metric("Totale Kosten", f"€ {beste_team['Prijs'].sum():,}")
            col2.metric("Budget Over", f"€ {budget_input - beste_team['Prijs'].sum():,}")
            col3.metric("Aantal Renners", len(beste_team))

            # De Tabel (Heatmap)
            st.markdown("### 📅 Jouw Team & Kalender")
            st.write("Hoe donkerder groen, hoe meer punten verwacht in die koers.")
            
            # Data voorbereiden voor weergave
            heatmap_data = beste_team.set_index('Naam')[race_kolommen]
            
            # Sorteren op wie het meeste scoort
            heatmap_data['Totaal'] = heatmap_data.sum(axis=1)
            heatmap_data = heatmap_data.sort_values('Totaal', ascending=False).drop(columns=['Totaal'])

            st.dataframe(
                heatmap_data.style.background_gradient(cmap="Greens", axis=None).format("{:.0f}"),
                use_container_width=True,
                height=600
            )
            
        else:
            st.error("❌ Geen team gevonden. Probeer je budget te verhogen of minder 'must-haves' te kiezen.")
            st.warning("Tip: Misschien heb je te dure renners verplicht gesteld?")

else:
    st.warning("⚠️ Bestand 'renners_data.xlsx' niet gevonden of leeg.")
    st.info("Ga in het menu links naar **'Data Update'** en klik op de knop om de data te downloaden.")