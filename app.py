import streamlit as st
import pandas as pd

st.set_page_config(page_title="Wielermanager Dashboard", page_icon="🚴", layout="wide")

st.title("🚴 Sporza Wielermanager Dashboard")

st.markdown("""
Welkom bij je persoonlijke assistent voor het voorjaar!
Gebruik het menu aan de linkerkant om te navigeren:

* **🏆 Team Maker:** Upload je data en laat de AI het beste team berekenen.
* **🌍 Data Update:** Haal de laatste startlijsten van ProCyclingStats.
""")

# Snel overzicht van je huidige database
try:
    df = pd.read_excel("renners_data.xlsx")
    st.info(f"📂 Huidige database status: **{len(df)} renners** ingeladen.")
    
    # Leuke statistiek
    top_favoriet = df.sort_values('Totaal_Score', ascending=False).iloc[0]
    st.metric("Huidige Top Favoriet", top_favoriet['Naam'], f"{top_favoriet['Totaal_Score']} ptn")
    
except:
    st.warning("Nog geen 'renners_data.xlsx' gevonden. Ga naar 'Data Update' om te beginnen!")