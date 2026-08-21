import streamlit as st
import pandas as pd
import plotly.express as px
import math, os

st.set_page_config(page_title="SUBLIME Agro - Dashboard", layout="wide")
st.title("🌱 SUBLIME Agro - Prospecção Inteligente")

# --- COORDENADAS DAS PRINCIPAIS CIDADES (para calcular raio sem precisar de lat/lon de cada cliente) ---
CITY_COORDS = {
    "BRASILIA": (-15.79, -47.88), "GOIANIA": (-16.68, -49.25), "SAO PAULO": (-23.55, -46.63),
    "BELO HORIZONTE": (-19.91, -43.93), "ANAPOLIS": (-16.32, -48.95), "UBERLANDIA": (-18.91, -48.27),
    "CAMPO GRANDE": (-20.46, -54.62), "SALVADOR": (-12.97, -38.51), "RIO DE JANEIRO": (-22.90, -43.17),
    "CUIABA": (-15.60, -56.09), "MARABA": (-5.36, -49.11), "PORTO VELHO": (-8.76, -63.89),
    "JATAI": (-17.88, -51.71), "BURITIS": (-15.62, -46.42), "FORTALEZA": (-3.71, -38.54),
    "UBERABA": (-19.74, -47.93), "RIO VERDE": (-17.79, -50.92), "JUIZ DE FORA": (-21.76, -43.34),
    "CAMPOS DOS GOYTACAZES": (-21.75, -41.30), "RIO BRANCO": (-9.97, -67.81),
    "LUCAS DO RIO VERDE": (-13.06, -55.90), "SORRISO": (-12.54, -55.72), "SINOP": (-11.86, -55.50),
    "PRIMAVERA DO LESTE": (-15.25, -54.29), "RONDONOPOLIS": (-16.46, -54.63), "VILA BELA DA SANTISSIMA TRINDADE": (-15.00, -59.95),
    "BELEM": (-1.45, -48.50), "PEDREIRAS": (-4.57, -44.60), "VILA BELA DA SANT": (-15.00, -59.95),
    "NOVA ALVORADA": (-21.46, -52.0), "AGUA BOA": (-14.05, -52.16)
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def get_coord(cidade):
    cidade = str(cidade).strip().upper()
    if cidade in CITY_COORDS:
        return CITY_COORDS[cidade]
    # tenta achar parcial
    for k,v in CITY_COORDS.items():
        if k in cidade or cidade in k:
            return v
    return None

# --- GOOGLE SHEETS CONEXÃO (igual antes) ---
def conectar_sheets():
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("SUBLIME Agro - Base")
        return sheet
    except: return None

sheet = conectar_sheets()
usando_sheets = sheet is not None

def load_forn():
    if usando_sheets:
        try: return pd.DataFrame(sheet.worksheet("fornecedores").get_all_records())
        except: return pd.DataFrame(columns=["Fornecedor","CNPJ","Cidade","UF","Contato","WhatsApp","Categoria"])
    else: return pd.DataFrame(columns=["Fornecedor","CNPJ","Cidade","UF","Contato","WhatsApp","Categoria"])

def load_prod():
    if usando_sheets:
        try: return pd.DataFrame(sheet.worksheet("produtos").get_all_records())
        except: return pd.DataFrame(columns=["Fornecedor","Produto","Categoria_Produto","Preco","Estoque","Obs"])
    else: return pd.DataFrame(columns=["Fornecedor","Produto","Categoria_Produto","Preco","Estoque","Obs"])

def save_forn(df):
    if usando_sheets:
        ws = sheet.worksheet("fornecedores"); ws.clear(); ws.update([df.columns.tolist()]+df.values.tolist())
def save_prod(df):
    if usando_sheets:
        ws = sheet.worksheet("produtos"); ws.clear(); ws.update([df.columns.tolist()]+df.values.tolist())

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["🎯 Prospecção por Raio + Ouro/Prata", "🏭 Fornecedores", "📦 Produtos"])

with tab1:
    st.header("Filtragem Inteligente")
    uploaded = st.file_uploader("Arraste sua Base Protheus.xlsx", type=["xlsx","csv"])

    if uploaded:
        df = pd.read_excel(uploaded, engine='openpyxl') if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Colunas Protheus
        col_nome = "A1_NOME" if "A1_NOME" in df.columns else df.columns[0]
        col_cidade = "A1_MUNC" if "A1_MUNC" in df.columns else None
        col_uf = "A1_ESTC" if "A1_ESTC" in df.columns else None

        # --- FILTRO OURO/PRATA ---
        # Procura se tem alguma coluna que seja categoria
        col_cat = None
        for c in df.columns:
            if 'OURO' in c or 'PRATA' in c or 'CATEG' in c or 'CLASS' in c or 'SEGMENT' in c:
                col_cat = c
                break

        st.sidebar.header("Filtros de Prospecção")

        # Se não tem coluna Ouro/Prata na base, cria um filtro manual por nome/cidade
        if col_cat:
            cats = df[col_cat].astype(str).str.upper().unique().tolist()
            sel = st.sidebar.multiselect(f"Categoria ({col_cat})", cats, default=cats)
            df_f = df[df[col_cat].astype(str).str.upper().isin(sel)]
        else:
            st.sidebar.info("Sua base Protheus não tem coluna OURO/PRATA. Vou filtrar por cidade/raio. Se você tem essa coluna, me fale o nome dela.")
            # Filtro extra: por nome
            busca = st.sidebar.text_input("Buscar por nome (opcional)")
            if busca:
                df_f = df[df[col_nome].astype(str).str.upper().str.contains(busca.upper())]
            else:
                df_f = df.copy()
            # Checkbox para simular Ouro/Prata
            st.sidebar.markdown("**Classificação manual:**")
            df_f["CLASSIFICACAO"] = "PRATA" # por padrão
            # Aqui você pode marcar os maiores como OURO depois

        # --- FILTRO POR RAIO DE CIDADE ---
        if col_cidade:
            todas_cidades = sorted(df_f[col_cidade].dropna().astype(str).str.upper().unique().tolist())
            cidade_base = st.sidebar.selectbox("📍 Cidade Base (onde você está)", todas_cidades)
            raio = st.sidebar.slider("📏 Raio em KM", 10, 1000, 300, step=10)

            if cidade_base:
                coord_base = get_coord(cidade_base)
                if not coord_base:
                    st.warning(f"Não tenho coordenada de {cidade_base}, adicione manualmente no código CITY_COORDS. Por enquanto mostrando só a cidade base.")
                    df_final = df_f[df_f[col_cidade].astype(str).str.upper() == cidade_base]
                else:
                    # Calcula distância de cada cidade da base até a base
                    cidades_dist = []
                    for cid in todas_cidades:
                        coord = get_coord(cid)
                        if coord:
                            d = haversine(coord_base[0], coord_base[1], coord[0], coord[1])
                            cidades_dist.append((cid, d))

                    cidades_no_raio = [c for c,d in cidades_dist if d <= raio]

                    st.sidebar.success(f"{len(cidades_no_raio)} cidades dentro de {raio}km de {cidade_base}")
                    df_final = df_f[df_f[col_cidade].astype(str).str.upper().isin(cidades_no_raio)]
                    df_final["DIST_CIDADE_BASE_KM"] = df_final[col_cidade].apply(lambda x: next((d for c,d in cidades_dist if c==str(x).upper()), 0))
        else:
            df_final = df_f

        # --- DASHBOARD ---
        st.divider()
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Clientes no Raio", len(df_final))
        c2.metric("Cidades no Raio", df_final[col_cidade].nunique() if col_cidade else 0)
        c3.metric("UFs", df_final[col_uf].nunique() if col_uf else 0)
        c4.metric("Raio Selecionado", f"{raio} km" if 'raio' in locals() else "-")

        col1, col2 = st.columns(2)
        if col_cidade:
            top = df_final[col_cidade].value_counts().head(15).reset_index()
            top.columns = ['Cidade','Qtd']
            fig = px.bar(top, x='Cidade', y='Qtd', title=f"Top Cidades dentro de {raio}km de {cidade_base}")
            col1.plotly_chart(fig, use_container_width=True)

        # Mapa por CIDADE
        if col_cidade:
            # Cria df de cidades para mapa
            map_data = []
            for cid in df_final[col_cidade].unique():
                coord = get_coord(cid)
                if coord:
                    qtd = len(df_final[df_final[col_cidade]==cid])
                    map_data.append({"Cidade": cid, "lat": coord[0], "lon": coord[1], "Qtd": qtd})
            if map_data:
                df_map = pd.DataFrame(map_data)
                fig_map = px.scatter_mapbox(df_map, lat="lat", lon="lon", size="Qtd", hover_name="Cidade", zoom=4, height=500, title="Mapa de Clientes por Cidade no Raio")
                fig_map.update_layout(mapbox_style="open-street-map")
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.map(pd.DataFrame([{"lat": coord_base[0], "lon": coord_base[1]}]) if 'coord_base' in locals() and coord_base else pd.DataFrame())

        st.subheader(f"Lista de clientes - {len(df_final)} encontrados")
        st.dataframe(df_final, use_container_width=True, height=600)

        st.download_button("📥 Baixar CSV filtrado por Raio", df_final.to_csv(index=False).encode('utf-8'), f"clientes_{cidade_base}_{raio}km.csv")
    else:
        st.info("Faça upload da base Protheus para usar o filtro de raio por cidade")

with tab2:
    st.header("Fornecedores")
    df_forn = load_forn()
    with st.form("forn", clear_on_submit=True):
        nome = st.text_input("Nome*"); cidade = st.text_input("Cidade"); whats = st.text_input("WhatsApp")
        if st.form_submit_button("Salvar"):
            novo = pd.DataFrame([[nome,"",cidade,"","",whats,""]], columns=["Fornecedor","CNPJ","Cidade","UF","Contato","WhatsApp","Categoria"])
            df_forn = pd.concat([df_forn,novo], ignore_index=True); save_forn(df_forn); st.rerun()
    st.dataframe(df_forn, use_container_width=True)

with tab3:
    st.header("Produtos por Fornecedor")
    df_forn = load_forn(); df_prod = load_prod()
    if len(df_forn)>0:
        with st.form("prod", clear_on_submit=True):
            forn = st.selectbox("Fornecedor", df_forn["Fornecedor"].unique()); prod = st.text_input("Produto*")
            if st.form_submit_button("Vincular"):
                novo = pd.DataFrame([[forn,prod,"","", "", ""]], columns=["Fornecedor","Produto","Categoria_Produto","Preco","Estoque","Obs"])
                df_prod = pd.concat([df_prod,novo], ignore_index=True); save_prod(df_prod); st.rerun()
        st.dataframe(df_prod, use_container_width=True)
