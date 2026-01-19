import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import os

st.set_page_config(page_title="Data Scraper", page_icon="🌍", layout="wide")

# --- CONFIGURATIE ---
# De startlijsten voor 2025
RACES = {
    'OHN': 'https://www.procyclingstats.com/race/omloop-het-nieuwsblad/2025/startlist',
    'KBK': 'https://www.procyclingstats.com/race/kuurne-brussel-kuurne/2025/startlist',
    'SB':  'https://www.procyclingstats.com/race/strade-bianche/2025/startlist',
    'MSR': 'https://www.procyclingstats.com/race/milan-san-remo/2025/startlist',
    'E3':  'https://www.procyclingstats.com/race/e3-harelbeke/2025/startlist',
    'GW':  'https://www.procyclingstats.com/race/gent-wevelgem/2025/startlist',
    'DDV': 'https://www.procyclingstats.com/race/dwars-door-vlaanderen/2025/startlist',
    'RVV': 'https://www.procyclingstats.com/race/ronde-van-vlaanderen/2025/startlist',
    'PR':  'https://www.procyclingstats.com/race/paris-roubaix/2025/startlist',
    'AGR': 'https://www.procyclingstats.com/race/amstel-gold-race/2025/startlist',
    'WP':  'https://www.procyclingstats.com/race/fleche-wallonne/2025/startlist',
    'LBL': 'https://www.procyclingstats.com/race/liege-bastogne-liege/2025/startlist'
}

# Headers om te lijken op een echte browser (anders blokkeert PCS je)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- FUNCTIES ---
def clean_naam(pcs_naam):
    """
    Probeert PCS naam (VAN DER POEL Mathieu) om te zetten naar Sporza (Mathieu van der Poel)
    """
    try:
        parts = pcs_naam.split()
        # Vind waar de hoofdletters stoppen (de achternaam)
        last_name_parts = [p for p in parts if p.isupper()]
        first_name_parts = [p for p in parts if not p.isupper()]
        
        if len(last_name_parts) > 0 and len(first_name_parts) > 0:
            # Zet achternaam om naar Title Case (VAN AERT -> Van Aert)
            last_name = " ".join(last_name_parts).title()
            # Uitzondering voor tussenvoegsels die klein moeten (van, der, de)
            last_name = last_name.replace("Van Der", "van der").replace("De ", "de ")
            first_name = " ".join(first_name_parts)
            return f"{first_name} {last_name}"
        return pcs_naam.title()
    except:
        return pcs_naam

def scrape_race(url, race_code):
    renners_gevonden = []
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Zoek alle links die naar een rider profiel gaan
            # We filteren op de main content om sidebar troep te vermijden
            content = soup.find('div', class_='page-content')
            if content:
                rider_links = content.select('a[href^="rider/"]')
            else:
                rider_links = soup.select('a[href^="rider/"]')

            for link in rider_links:
                raw_name = link.text.strip()
                if raw_name:
                    mooie_naam = clean_naam(raw_name)
                    renners_gevonden.append(mooie_naam)
            
            # Unieke namen (soms staat iemand er dubbel in)
            return list(set(renners_gevonden))
    except Exception as e:
        st.error(f"Fout bij {race_code}: {e}")
    return []

def laad_huidige_data():
    huidige_map = os.path.dirname(__file__)
    pad = os.path.join(huidige_map, "..", "renners_data.xlsx")
    if os.path.exists(pad):
        return pd.read_excel(pad)
    return None

# --- APP INTERFACE ---
st.title("🌍 Live Data Scraper (PCS)")
st.markdown("Haal de **echte** startlijsten van 2025 op.")

# Huidige status tonen
df_huidig = laad_huidige_data()
if df_huidig is not None:
    with st.expander(f"Bekijk huidige database ({len(df_huidig)} renners)"):
        st.dataframe(df_huidig)

if st.button("🚀 Start Echte Update"):
    status_box = st.status("Data aan het ophalen...", expanded=True)
    all_riders_dict = {}
    
    # Voortgangsbalk
    progress_bar = status_box.progress(0)
    
    total = len(RACES)
    for i, (code, url) in enumerate(RACES.items()):
        status_box.write(f"Scrapen van **{code}**...")
        riders = scrape_race(url, code)
        
        # Data verwerken
        for naam in riders:
            if naam not in all_riders_dict:
                # Nieuwe renner aanmaken met standaard waarden
                all_riders_dict[naam] = {
                    'Naam': naam, 
                    'Team': 'Check Excel', 
                    'Prijs': 5000000, # Standaard prijs
                    'Type': 'Algemeen'
                }
            
            # Zet de renner op aanwezig (100 ptn) voor deze race
            all_riders_dict[naam][code] = 100
            
        # Pauze om PCS niet boos te maken (zeer belangrijk!)
        time.sleep(random.uniform(0.5, 1.5))
        progress_bar.progress((i + 1) / total)

    # Afronden
    df_nieuw = pd.DataFrame(list(all_riders_dict.values()))
    
    # Zorg dat alle race kolommen bestaan en vul lege plekken met 0
    for code in RACES.keys():
        if code not in df_nieuw.columns:
            df_nieuw[code] = 0
    df_nieuw = df_nieuw.fillna(0)

    # Opslaan
    huidige_map = os.path.dirname(__file__)
    pad_naar_excel = os.path.join(huidige_map, "..", "renners_data.xlsx")
    df_nieuw.to_excel(pad_naar_excel, index=False)
    
    status_box.update(label="✅ Klaar! Database bijgewerkt.", state="complete", expanded=False)
    st.success(f"Update voltooid! {len(df_nieuw)} renners gevonden.")
    
    # Resultaat tonen en downloaden
    st.dataframe(df_nieuw.head(50), use_container_width=True)
    
    with open(pad_naar_excel, "rb") as file:
        st.download_button(
            label="📥 Download Excel Bestand",
            data=file,
            file_name="renners_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )