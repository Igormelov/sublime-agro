import streamlit as st
import pandas as pd
import gspread
import folium
import requests
from datetime import datetime
from streamlit_folium import st_folium

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide", initial_sidebar_state="expanded")

# --- CSS QUE CORRIGE O TEMA ESCURO E DEIXA IGUAL AO PRINT ---
st.markdown("""
<style>
/* Força tema claro */
[data-testid="stAppViewContainer"]{background:#efefe9!important}
[data-testid="stHeader"]{background:#efefe9!important}
[data-testid="stSidebar"]{background:#183a27!important; min-width:240px}
[data-testid="stSidebar"] *{color:#ffffff!important}
.main.block-container{padding-top:1rem}

/* Cards */
.card{
 background:white; border-radius:14px; padding:16px;
 box-shadow:0 2px 12px rgba(0,0,0,0.06); border:1px solid #e8e8e0
}

/* Inputs sempre claros */
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"]{
 background:white!important; color:#222!important; border:1px solid #d8d8d0!important
}
label{color:#333!important; font-weight:600!important; font-size:13px!important}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

@st.cache_data(ttl=60)
def load_dados():
    client = get_client()
    sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    def get_df(nome):
        try:
            ws = sh.worksheet(nome)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()
    df_c = get_df("Clientes")
    df_f = get_df("Fornecedores")
    df_p = get_df("Produtos")
    df_cache = get_df("cache_cep")
    return df_c, df_f, df_p, df_cache, sh

def get_latlon(cep, sh):
    cep = ''.join(filter(str.isdigit, str(cep)))
    if len(cep)!=8: return None
    ws = sh.worksheet("cache_cep")
    try:
        cell = ws.find(cep)
        if cell:
            row = ws.row_values(cell.row)
            return float(row[1]), float(row[2])
    except: pass
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=6).json()
        if "erro" in r: return None
        q = f"{r.get('logradouro','')}, {r.get('localidade','')}, {r.get('uf','')}, Brasil"
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1", headers={"User-Agent":"SublimeAgroV3"}, timeout=6).json()
        if geo:
            lat, lon = float(geo[0]['lat']), float(geo[0]['lon'])
            ws.append_row([cep, lat, lon, q, r.get('localidade',''), r.get('uf',''), datetime.now().strftime("%d/%m/%Y")])
            return lat, lon
    except: pass
    return None

try:
    df_c, df_f, df_p, df_cache, sh = load_dados()
except Exception as e:
    st.error(f"Erro ao ler planilha: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🌿 SUBLIME AGRO")
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.radio("menu", ["Clientes - Lista", "Cadastrar Cliente", "Fornecedores", "Produtos"], label_visibility="collapsed")
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<div style='background:#2a5a3a; padding:10px; border-radius:20px; text-align:center; font-size:13px'>☁️ {len(df_cache)} CEPs em cache</div>", unsafe_allow_html=True)

# --- TOPO ---
c1,c2,c3 = st.columns([2,5,2])
with c1:
    st.markdown("<div style='font-weight:800; font-size:18px; color:#222'>🌿 SUBLIME <span style='background:#d4e8c5; color:#2e7d32; font-size:10px; padding:3px 8px; border-radius:6px; vertical-align:middle'>V3</span> Agro</div>", unsafe_allow_html=True)
with c2:
    busca = st.text_input("busca", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with c3:
    st.markdown(f"<div style='text-align:right'><b>👤 Ana Silva</b><br><span style='font-size:12px; color:#666'>{len(df_c)} clientes • {len(df_f)} fornecedores</span></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- CONTEUDO ---
col_map, col_form = st.columns([1.7, 1])

with col_map:
    st.markdown(f"<div class='card'><b>🗺️ Mapa de Clientes e Fornecedores</b> <span style='float:right; font-size:12px; color:#666'>{len(df_c)} clientes no mapa</span></div>", unsafe_allow_html=True)
    m = folium.Map(location=[-23.18, -45.88], zoom_start=11, tiles="CartoDB positron")
    # Plota cache
    for _, r in df_cache.iterrows():
        try:
            lat = float(r.get('lat') or r.get('LAT') or 0)
            lon = float(r.get('lon') or r.get('LON') or 0)
            if lat!=0:
                folium.Marker([lat, lon], tooltip=str(r.get('endereco','')), icon=folium.Icon(color='green', icon='leaf')).add_to(m)
        except: pass
    st_folium(m, width=None, height=560, returned_objects=[])

with col_form:
    st.markdown("<div class='card'><h4 style='margin:0'>+ Cadastrar Cliente</h4><p style='font-size:12px; color:#666; margin:0'>Preencha e buscaremos a localização automática pelo CEP</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome*")
        razao = st.text_input("Razão Social")
        doc = st.text_input("CPF/CNPJ")
        end = st.text_input("Endereço")
        c_cep, c_cid = st.columns(2)
        with c_cep: cep = st.text_input("CEP* (só números)")
        with c_cid: cidade = st.text_input("Cidade")
        c_est, c_tipo = st.columns(2)
        with c_est: estado = st.selectbox("Estado", ["SP","MG","MT","GO","PR","BA","MS","TO"])
        with c_tipo: tipo = st.selectbox("Tipo_Cliente", ["Produtor Rural","Cooperativa","Revenda","Outro"])

        salvar = st.form_submit_button("✔ Salvar Cliente", type="primary", use_container_width=True)
        if salvar:
            if not nome or not cep:
                st.warning("Preencha Nome e CEP")
            else:
                latlon = get_latlon(cep, sh)
                try:
                    sh.worksheet("Clientes").append_row([len(df_c)+1, nome, razao, doc, end, cep, cidade, estado, tipo, datetime.now().strftime("%d/%m/%Y")])
                    st.cache_data.clear()
                    if latlon: st.success(f"✅ {nome} salvo! Localizado em {latlon[0]:.4f}, {latlon[1]:.4f}")
                    else: st.success(f"✅ {nome} salvo! (CEP não localizado, verifique)")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Lista rápida
    if not df_c.empty:
        st.markdown("<div class='card'><b>Últimos clientes</b></div>", unsafe_allow_html=True)
        st.dataframe(df_c.tail(5)[["Nome","Cidade","Estado"]] if "Nome" in df_c.columns else df_c.tail(5), use_container_width=True, hide_index=True)
