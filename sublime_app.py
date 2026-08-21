import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

st.set_page_config(page_title="SUBLIME Agro V3.4", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #f5f7f6; }
    [data-testid="stSidebar"] { background-color: #0f2d1f!important; }
    [data-testid="stSidebar"] * { color: #d1e7d6!important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_sheets():
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

def buscar_cep_turbinado(cep_limpo):
    """Busca no ViaCEP + Nominatim e retorna tudo"""
    try:
        # 1. ViaCEP para dados de endereço
        r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5).json()
        if "erro" in r: return None

        cidade = r.get("localidade","")
        uf = r.get("uf","")
        bairro = r.get("bairro","")
        endereco = f"{r.get('logradouro','')} - {cidade}/{uf}"

        # 2. Nominatim para lat/lng
        query = f"{cep_limpo}, {cidade}, {uf}, Brazil"
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1", headers={"User-Agent":"SublimeAgro/3.4"}, timeout=8).json()
        if geo:
            lat = float(geo[0]["lat"])
            lng = float(geo[0]["lon"])
            return {"lat":lat, "lng":lng, "cidade":cidade, "uf":uf, "bairro":bairro, "endereco":endereco}
    except: pass
    return None

def salvar_no_cache_turbinado(ws_cache, cep_limpo, dados):
    """Salva no formato novo: cep | lat | lng | cidade | uf | bairro | endereco | data_cache | qtd_clientes"""
    try:
        df = pd.DataFrame(ws_cache.get_all_records())
        # Se já existe, aumenta contador
        if not df.empty and cep_limpo in df['cep'].astype(str).values:
            idx = df[df['cep'].astype(str)==cep_limpo].index[0] + 2 # +2 por causa do header e 1-index
            qtd_atual = int(df.loc[idx-2, 'qtd_clientes']) if 'qtd_clientes' in df.columns else 1
            ws_cache.update_cell(idx, 9, qtd_atual+1) # coluna 9 = qtd_clientes
            return

        # Se não existe, cria novo
        hoje = datetime.now().strftime("%d/%m/%Y")
        ws_cache.append_row([
            cep_limpo,
            dados["lat"],
            dados["lng"],
            dados["cidade"],
            dados["uf"],
            dados["bairro"],
            dados["endereco"],
            hoje,
            1
        ])
    except Exception as e:
        st.error(f"Erro cache: {e}")

# --- APP ---
sh = get_sheets()

with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    st.caption("V3.4 - Cache Turbinado")
    categoria = st.selectbox("", ["👥 CLIENTES", "🏭 FORNECEDORES", "📦 PRODUTOS", "⚙️ CONFIGURAÇÕES"])
    if "CLIENTES" in categoria:
        pagina = st.radio("", ["📋 Lista", "➕ Cadastrar Cliente", "📍 Mapa Personalizado"])
    elif "FORNECEDORES" in categoria:
        pagina = st.radio("", ["📋 Lista Fornecedores", "➕ Cadastrar Fornecedor"])
    elif "PRODUTOS" in categoria:
        pagina = st.radio("", ["📋 Lista Produtos", "➕ Cadastrar Produto"])
    else:
        pagina = st.radio("", ["🗑️ Limpar Cache", "📊 Status Cache"])

# --- PAGINAS ---
if pagina == "➕ Cadastrar Cliente":
    st.title("➕ Cadastrar Cliente - V3.4")
    st.info("💡 Agora ao salvar, o CEP já busca cidade/bairro/lat/lng e salva turbinado na nuvem. Próxima vez será instantâneo.")
    with st.form("c", clear_on_submit=True):
        c1,c2 = st.columns(2)
        nome = c1.text_input("Nome *")
        razao = c2.text_input("Razão Social")
        c3,c4 = st.columns(2)
        doc = c3.text_input("CPF/CNPJ")
        tel = c4.text_input("Telefone")
        endereco = st.text_input("Endereço (opcional, o ViaCEP já completa)")
        c5,c6,c7 = st.columns(3)
        cidade = c5.text_input("Cidade")
        uf = c6.text_input("UF")
        cep = c7.text_input("CEP *")

        if st.form_submit_button("💾 SALVAR COM CACHE TURBINADO", type="primary", use_container_width=True):
            if nome and cep:
                cep_limpo = "".join(filter(str.isdigit, cep))
                ws_cli = sh.worksheet("Clientes")
                ws_cache = sh.worksheet("cache_cep")

                # 1. Salva cliente
                ws_cli.append_row([nome, razao, doc, endereco, cidade, uf.upper(), cep, tel])

                # 2. Busca e salva cache turbinado
                with st.spinner(f"Buscando CEP {cep}..."):
                    dados = buscar_cep_turbinado(cep_limpo)
                    if dados:
                        salvar_no_cache_turbinado(ws_cache, cep_limpo, dados)
                        st.success(f"✅ {nome} salvo + CEP cacheado: {dados['cidade']}/{dados['uf']} - {dados['bairro']}")
                    else:
                        st.warning(f"✅ {nome} salvo, mas CEP não encontrado para cache. Mapa usará cidade.")
                st.balloons()
            else:
                st.error("Nome e CEP obrigatórios")

elif pagina == "📋 Lista":
    st.title("📋 Clientes")
    df = pd.DataFrame(sh.worksheet("Clientes").get_all_records())
    st.dataframe(df, use_container_width=True)

elif pagina == "📍 Mapa Personalizado":
    st.title("📍 Mapa com Cache Turbinado")
    ws_cache = sh.worksheet("cache_cep")
    df_cache = pd.DataFrame(ws_cache.get_all_records())

    if df_cache.empty:
        st.warning("Cache vazio. Cadastre um cliente para gerar o primeiro pino.")
    else:
        st.metric("CEPs únicos cacheados", len(df_cache))
        st.dataframe(df_cache, use_container_width=True)

        m = folium.Map(location=[df_cache.iloc[0]['lat'], df_cache.iloc[0]['lng']], zoom_start=6)
        for _, r in df_cache.iterrows():
            try:
                folium.Marker(
                    [float(r['lat']), float(r['lng'])],
                    popup=f"{r['cep']} - {r['cidade']}/{r['uf']} - {r['qtd_clientes']} cliente(s)",
                    icon=folium.Icon(color='green')
                ).add_to(m)
            except: pass
        st_folium(m, height=600, use_container_width=True)

elif pagina == "📊 Status Cache":
    st.title("📊 Status do Cache Turbinado")
    ws_cache = sh.worksheet("cache_cep")
    df = pd.DataFrame(ws_cache.get_all_records())
    if not df.empty:
        c1,c2,c3 = st.columns(3)
        c1.metric("CEPs únicos", len(df))
        c2.metric("Total clientes (soma qtd_clientes)", df['qtd_clientes'].astype(int).sum() if 'qtd_clientes' in df.columns else len(df))
        c3.metric("Cidades diferentes", df['cidade'].nunique() if 'cidade' in df.columns else 0)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Cache ainda vazio")

elif pagina == "🗑️ Limpar Cache":
    st.title("🗑️ Limpar Cache Turbinado")
    ws = sh.worksheet("cache_cep")
    df = pd.DataFrame(ws.get_all_records())
    st.metric("CEPs salvos", len(df))
    if st.button("LIMPAR TUDO", type="primary"):
        ws.clear()
        ws.append_row(["cep","lat","lng","cidade","uf","bairro","endereco","data_cache","qtd_clientes"])
        st.success("Cache limpo e pronto pro formato novo!")
        st.rerun()

# Outras listas mantidas
else:
    st.title(pagina)
    aba = pagina.split(" ")[-1]
    try:
        ws = sh.worksheet(aba)
        st.dataframe(pd.DataFrame(ws.get_all_records()), use_container_width=True)
    except:
        st.write("Aba não encontrada")
