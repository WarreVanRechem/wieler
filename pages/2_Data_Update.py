import streamlit as st
import pandas as pd
import cloudscraper  # DE OPLOSSING VOOR 403 ERRORS
from bs4 import BeautifulSoup
import time
import random
import os

st.set_page_config(page_title="Data Scraper", page_icon="🌍", layout="wide")

# --- CONFIGURATIE ---
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

# --- FUNCTIES ---
def clean_naam(pcs_naam):
    """Zet 'VAN DER POEL Mathieu' om naar 'Mathieu van der Poel'"""
    try:
        parts = pcs_naam.split()
        last_name_parts = [p for p in parts if p.isupper()]
        first_name_parts = [p for p in parts if not p.isupper()]
        if len(last_name_parts) > 0:
            last_name = " ".join(last_name_parts).title().replace("Van Der", "van der").replace("De ", "de ")
            first_name = " ".join(first_name_parts)
            return f"{first_name} {last_name}"
        return pcs_naam.title()
    except:
        return pcs_naam

def scrape_race(url, race_code, status_log):
    renners_gevonden = []
    try:
        # HIER GEBRUIKEN WE CLOUDSCRAPER IN PLAATS VAN REQUESTS
        scraper = cloudscraper.create_scraper() 
        response = scraper.get(url)
        
        if response.status_code == 403:
            status_log.error(f"❌ {race_code}: Nog steeds geblokkeerd (403).")
            return []
        elif response.status_code != 200:
            status_log.warning(f"⚠️ {race_code}: Status code {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Probeer de standaard 'rider' links
        rider_links = soup.select('a[href^="rider/"]')
        
        # 2. Fallback: Soms zitten ze in een specifieke lijst structuur
        if not rider_links:
            rider_links = soup.select('div.main > ul > li > a')

        for link in rider_links:
            raw_name = link.text.strip()
            if raw_name:
                renners_gevonden.append(clean_naam(raw_name))
        
        return list(set(renners_gevonden))

    except Exception as e:
        status_log.error(f"Fout bij {race_code}: {e}")
    return []

def get_manual_data():
    """Backup dataset voor als het scrapen faalt"""
    data = [
        {'Naam': 'Tadej Pogacar', 'Team': 'UAE Team Emirates', 'Prijs': 12000000, 'Type': 'Klimmer/Kassei', 'SB': 100, 'MSR': 80, 'LBL': 120},
        {'Naam': 'Mathieu van der Poel', 'Team': 'Alpecin-Deceuninck', 'Prijs': 12000000, 'Type': 'Kassei', 'MSR': 90, 'E3': 80, 'GW': 80, 'RVV': 120, 'PR': 120},
        {'Naam': 'Wout van Aert', 'Team': 'Visma-Lease a Bike', 'Prijs': 11000000, 'Type': 'Kassei/Sprint', 'OHN': 70, 'KBK': 60, 'E3': 90, 'GW': 80, 'DDV': 70, 'RVV': 100, 'PR': 100},
        {'Naam': 'Remco Evenepoel', 'Team': 'Soudal Quick-Step', 'Prijs': 11000000, 'Type': 'Heuvel', 'AGR': 80, 'WP': 90, 'LBL': 100},
        {'Naam': 'Mads Pedersen', 'Team': 'Lidl-Trek', 'Prijs': 10000000, 'Type': 'Kassei/Sprint', 'OHN': 60, 'KBK': 60, 'MSR': 70, 'E3': 70, 'GW': 90, 'RVV': 80, 'PR': 80},
        {'Naam': 'Jasper Philipsen', 'Team': 'Alpecin-Deceuninck', 'Prijs': 10000000, 'Type': 'Sprinter', 'OHN': 50, 'KBK': 70, 'MSR': 100, 'GW': 90, 'PR': 80, 'EF': 50},
        {'Naam': 'Arnaud De Lie', 'Team': 'Lotto Dstny', 'Prijs': 9000000, 'Type': 'Sprinter/Kassei', 'OHN': 80, 'KBK': 50, 'GW': 60, 'DDV': 50, 'RVV': 40, 'EF': 40},
        {'Naam': 'Tom Pidcock', 'Team': 'INEOS Grenadiers', 'Prijs': 8000000, 'Type': 'Heuvel/Kassei', 'OHN': 40, 'SB': 90, 'MSR': 40, 'RVV': 50, 'AGR': 70, 'WP': 60, 'LBL': 60},
        {'Naam': 'Matteo Jorgenson', 'Team': 'Visma-Lease a Bike', 'Prijs': 7000000, 'Type': 'Heuvel', 'OHN': 50, 'KBK': 40, 'E3': 60, 'DDV': 50, 'RVV': 60},
        {'Naam': 'Maxim Van Gils', 'Team': 'Lotto Dstny', 'Prijs': 5000000, 'Type': 'Heuvel', 'SB': 60, 'MSR': 30, 'AGR': 50, 'WP': 60, 'LBL': 50, 'EF': 40},
        {'Naam': 'Oier Lazkano', 'Team': 'Movistar Team', 'Prijs': 3000000, 'Type': 'Kassei', 'OHN': 40, 'KBK': 30, 'E3': 40, 'DDV': 45, 'RVV': 30, 'PR': 30},
        {'Naam': 'Tim Wellens', 'Team': 'UAE Team Emirates', 'Prijs': 5000000, 'Type': 'Heuvel/Kassei', 'OHN': 60, 'KBK': 40, 'SB': 40, 'E3': 50, 'RVV': 40}
    ]
    return pd.DataFrame(data).fillna(0)

def save_data(df):
    huidige_map = os.path.dirname(__file__)
    pad = os.path.join(huidige_map, "..", "renners_data.xlsx")
    
    # Kolommen fixen
    for code in RACES.keys():
        if code not in df.columns:
            df[code] = 0
    df = df.fillna(0)
    df.to_excel(pad, index=False)
    return pad

# --- APP INTERFACE ---
st.title("🌍 Data Beheer")

# Huidige status tonen
huidige_map = os.path.dirname(__file__)
pad = os.path.join(huidige_map, "..", "renners_data.xlsx")
if os.path.exists(pad):
    try:
        df_huidig = pd.read_excel(pad)
        st.info(f"📂 Database bevat **{len(df_huidig)} renners**.")
        with st.expander("Bekijk huidige data"):
            st.dataframe(df_huidig)
    except:
        st.error("Excel bestand is corrupt of leeg.")
else:
    st.warning("⚠️ Nog geen data gevonden.")

st.markdown("---")

col1, col2 = st.columns(2)

# --- OPTIE 1: CLOUDSCRAPER ---
with col1:
    st.subheader("Optie 1: Live Scrapen (Slim)")
    st.caption("Probeert de PCS blokkade te omzeilen met Cloudscraper.")
    
    if st.button("🚀 Start Live Update"):
        status_box = st.status("Verbinden met PCS...", expanded=True)
        all_riders_dict = {}
        progress_bar = status_box.progress(0)
        
        totaal_gevonden = 0
        
        for i, (code, url) in enumerate(RACES.items()):
            status_box.write(f"Scrapen van **{code}**...")
            riders = scrape_race(url, code, status_box)
            
            if len(riders) > 0:
                totaal_gevonden += len(riders)
                for naam in riders:
                    if naam not in all_riders_dict:
                        all_riders_dict[naam] = {'Naam': naam, 'Team': 'Check Excel', 'Prijs': 5000000, 'Type': 'Algemeen'}
                    all_riders_dict[naam][code] = 100 # Renner start = 100 punten
            
            # Pauze is nog steeds belangrijk!
            time.sleep(random.uniform(1.0, 3.0)) 
            progress_bar.progress((i + 1) / len(RACES))

        if totaal_gevonden > 0:
            df_nieuw = pd.DataFrame(list(all_riders_dict.values()))
            save_data(df_nieuw)
            status_box.update(label="✅ Klaar!", state="complete", expanded=False)
            st.success(f"Gelukt! {len(df_nieuw)} renners gevonden.")
            st.rerun()
        else:
            status_box.update(label="❌ Mislukt", state="error", expanded=True)
            st.error("Cloudscraper kwam er ook niet doorheen. Gebruik Optie 2!")

# --- OPTIE 2: BACKUP ---
with col2:
    st.subheader("Optie 2: Noodoplossing")
    st.caption("Werkt de scraper niet? Laad hier direct een werkende basis-set in.")
    
    if st.button("💾 Laad Backup Data"):
        df_backup = get_manual_data()
        save_data(df_backup)
        st.success(f"Backup data geladen! ({len(df_backup)} renners)")
        time.sleep(1)
        st.rerun()