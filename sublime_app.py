import streamlit as st
import pandas as pd
import requests
import time
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="SUBLIME Agro - Mapa Google Maps", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS (NUVEM) ---
@st.cache_resource
def get_gspread_client():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

def load_cache_cloud():
    try:
        client = get_gspread_client()
        if not client: return {}
        sheet_id = st.secrets["gcp"]["spreadsheet_id"]
        sh = client.open_by_key(sheet_id)
        try:
            ws = sh.worksheet("cache_cep")
        except:
            ws = sh.add_worksheet(title="cache_cep", rows=1000, cols=3)
            ws.append_row(["cep", "lat", "lng"])
            return {}

        data = ws.get_all_records()
        cache = {}
        for row in data:
            try:
                cache[str(row['cep']).replace('-','').strip()] = (float(row['lat']), float(row['lng']))
            except: pass
        return cache
    except Exception as e:
        st.warning(f"Cache nuvem offline: {e}")
        return {}

def save_cache_cloud(cep, lat, lng):
    try:
        client = get_gspread_client()
        if not client: return
        sheet_id = st.secrets["gcp"]["spreadsheet_id"]
        sh = client.open_by_key(sheet_id)
        ws = sh.worksheet("cache_cep")
        cep_clean = str(cep).replace('-','').strip()
        ws.append_row([cep_clean, lat, lng])
    except Exception as e:
        pass

# Carrega cache da nuvem
if 'cache_cep' not in st.session_state:
    with st.spinner("Carregando cache da nuvem..."):
        st.session_state.cache_cep = load_cache_cloud()

# --- FUNÇÃO DE BUSCAR LAT/LNG DO CEP ---
def get_lat_lng(cep):
    cep_clean = str(cep).replace('-','').replace('.','').strip()
    if len(cep_clean)!= 8:
        return None, None

    # 1. Tenta cache
    if cep_clean in st.session_state.cache_cep:
        return st.session_state.cache_cep[cep_clean]

    # 2. Busca na API ViaCEP + BrasilAPI
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep_clean}/json/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'erro' not in data:
                # Usa BrasilAPI para geocode
                r2 = requests.get(f"https://brasilapi.com.br/api/cep/v2/{cep_clean}", timeout=5)
                if r2.status_code == 200:
                    d2 = r2.json()
                    if 'location' in d2 and d2['location']['coordinates']:
                        lng = float(d2['location']['coordinates']['longitude'])
                        lat = float(d2['location']['coordinates']['latitude'])
                        st.session_state.cache_cep[cep_clean] = (lat, lng)
                        save_cache_cloud(cep_clean, lat, lng)
                        time.sleep(0.2)
                        return lat, lng
    except:
        pass
    return None, None

# --- INTERFACE ---
st.title("🌱 SUBLIME Agro - Mapa Google Maps")

tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Google Maps por Raio", "📦 Fornecedores", "📦 Produtos"])

with tab1:
    st.write("Arraste sua planilha")
    uploaded = st.file_uploader("Upload", type=["xlsx","csv","xls"], label_visibility="collapsed")

    if uploaded:
        if uploaded.name.endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)

        st.success(f"Planilha carregada! {len(df)} linhas | Cache nuvem: {len(st.session_state.cache_cep)} CEPs")
        st.dataframe(df.head())

        if st.button("🚀 Gerar Mapa"):
            # Exemplo - aqui entra sua lógica de raio
            for idx, row in df.iterrows():
                # pega coluna de CEP (ajuste nome da coluna conforme sua planilha)
                cep_col = [c for c in df.columns if 'cep' in c.lower()][0] if any('cep' in c.lower() for c in df.columns) else df.columns[0]
                cep = row[cep_col]
                lat, lng = get_lat_lng(cep)
                if lat:
                    st.write(f"✅ {cep} -> {lat}, {lng}")
                else:
                    st.write(f"❌ {cep} não encontrado")

    st.info(f"💾 CEPs já salvos na nuvem: {len(st.session_state.cache_cep)}")

with tab2:
    st.write("Fornecedores")

with tab3:
    st.write("Produtos")
