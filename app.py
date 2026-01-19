import streamlit as st
import pandas as pd
import pulp

st.set_page_config(page_title="Wielermanager Pro", layout="wide")

# --- FUNCTIES ---
def laad_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df = df.fillna(0) # Lege cellen worden 0
        return df
    return None

def optimaliseer_team(df, budget, max_renners, verplichte_renners, race_kolommen):
    # Bereken totaalscore (som van alle races)
    df['Totaal_Score'] = df[race_kolommen].sum(axis=1)

    prob = pulp.LpProblem("Sporza_Team", pulp.LpMaximize)
    renner_vars = pulp.LpVariable.dicts("Renner", df.index, cat='Binary')

    # Objective
    prob += pulp.lpSum([df.loc[i, 'Totaal_Score'] * renner_vars[i] for i in df.index])

    # Constraints
    prob += pulp.lpSum([df.loc[i, 'Prijs'] * renner_vars[i] for i in df.index]) <= budget
    prob += pulp.lpSum([renner_vars[i] for i in df.index]) == max_renners

    # Verplichte renners
    for renner_naam in verplichte_renners:
        idx = df[df['Naam'] == renner_naam].index
        if not idx.empty:
            prob += renner_vars[idx[0]] == 1

    prob.solve()

    if pulp.LpStatus[prob.status] == 'Optimal':
        indices = [i for i in df.index if renner_vars[i].varValue == 1]
        return df.loc[indices]
    return None

# --- APP ---
st.title("🚴 Sporza Kalender Optimizer")

uploaded_file = st.sidebar.file_uploader("Upload je Kalender Excel", type=["xlsx"])
budget = st.sidebar.number_input("Budget", value=100000000, step=1000000)
aantal = st.sidebar.number_input("Aantal Renners", value=20)

if uploaded_file:
    df = laad_data(uploaded_file)
    
    # Automatisch detecteren welke kolommen koersen zijn
    # We nemen aan dat alles na 'Type' een koers is
    basis_kolommen = ['Naam', 'Team', 'Prijs', 'Type']
    race_kolommen = [col for col in df.columns if col not in basis_kolommen and col != 'Totaal_Score']

    st.info(f"Koersen gevonden in data: {', '.join(race_kolommen)}")

    must_haves = st.multiselect("Verplichte Renners", df['Naam'].tolist())

    if st.button("🚀 Genereer Team"):
        beste_team = optimaliseer_team(df, budget, aantal, must_haves, race_kolommen)

        if beste_team is not None:
            totaal_punten = beste_team['Totaal_Score'].sum()
            st.success(f"Team Compleet! Verwachte totaalscore: {totaal_punten:.0f}")

            # 1. Team Overzicht
            st.subheader("Het Selecteerde Team")
            weergave_cols = ['Naam', 'Team', 'Prijs', 'Totaal_Score']
            st.dataframe(beste_team[weergave_cols], use_container_width=True)

            # 2. De Kalender Analyse (Heatmap)
            st.subheader("📅 Kalender & Puntenverdeling")
            st.markdown("Hoe donkerder de cel, hoe meer punten verwacht in die koers.")
            
            # We maken een heatmap met Pandas styling
            heatmap_data = beste_team.set_index('Naam')[race_kolommen]
            
            # Sorteer op totaalscore voor overzichtelijkheid
            heatmap_data['Totaal'] = heatmap_data.sum(axis=1)
            heatmap_data = heatmap_data.sort_values('Totaal', ascending=False).drop(columns=['Totaal'])

            st.dataframe(
                heatmap_data.style.background_gradient(cmap="Greens", axis=None).format("{:.0f}"),
                use_container_width=True,
                height=600
            )
            
            # 3. Grafiek: Punten per Koers
            st.subheader("📊 Waar scoor je het meest?")
            koers_totalen = beste_team[race_kolommen].sum().sort_values(ascending=False)
            st.bar_chart(koers_totalen)

        else:
            st.error("Geen team gevonden binnen budget.")
else:
    st.info("Upload eerst je Excel bestand.")