import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import io

st.set_page_config(page_title="SUBLIME Agro", layout="wide")
st.title("SUBLIME Agro - Prospecção Inteligente")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

arquivo = st.file_uploader("Arraste sua base .xlsx", type=["xlsx","csv"])

if arquivo:
    df = pd.read_excel(arquivo) if arquivo.name.endswith('.xlsx') else pd.read_csv(arquivo)
    st.success(f"Base carregada: {len(df)} clientes")
    
    if 'CLASSIFICACAO' in df.columns:
        df_f = df[df['CLASSIFICACAO'].isin(['OURO','PRATA'])].copy()
    else:
        df_f = df.copy()
    st.info(f"Filtrados OURO+PRATA: {len(df_f)}")

    c1, c2 = st.columns(2)
    with c1:
        cidade = st.text_input("Cidade base", "Lucas do Rio Verde")
        raio = st.slider("Raio km", 50, 500, 300)
    with c2:
        lat_c = st.number_input("Lat centro", value=-13.06, format="%.4f")
        lon_c = st.number_input("Lon centro", value=-55.90, format="%.4f")

    if st.button("Gerar Mapa e CSV"):
        lat_col = next((c for c in df_f.columns if 'LAT' in c.upper()), None)
        lon_col = next((c for c in df_f.columns if 'LON' in c.upper()), None)
        if lat_col and lon_col:
            df_f.rename(columns={lat_col:'LAT', lon_col:'LON'}, inplace=True)
        
        def no_raio(r):
            try:
                if pd.isna(r['LAT']) or pd.isna(r['LON']): return False
                return haversine(lat_c, lon_c, float(r['LAT']), float(r['LON'])) <= raio
            except: return False
        
        df_r = df_f[df_f.apply(no_raio, axis=1)].copy()
        
        if len(df_r) == 0:
            st.warning("Nenhum cliente no raio, aumente para 500km")
        else:
            st.success(f"Achei {len(df_r)} clientes em {raio}km de {cidade}")
            
            # Telefone automatico
            col_fone = next((c for c in df_r.columns if 'FONE' in c.upper() or 'TEL' in c.upper() or 'CEL' in c.upper() or 'WHATS' in c.upper()), None)
            if col_fone:
                df_r['WHATSAPP'] = df_r[col_fone].astype(str).str.replace(r'\D','', regex=True)
            
            # Mapa limitado a 500 pontos
            df_mapa = df_r.head(500)
            m = folium.Map(location=[lat_c, lon_c], zoom_start=8)
            folium.Circle([lat_c, lon_c], radius=raio*1000, color='red', fill=True, fill_opacity=0.1).add_to(m)
            for _, r in df_mapa.iterrows():
                try:
                    cor = 'green' if 'OURO' in str(r.get('CLASSIFICACAO','')).upper() else 'blue'
                    folium.CircleMarker([float(r['LAT']), float(r['LON'])], radius=4, color=cor, fill=True, popup=str(r.get('NOME',''))).add_to(m)
                except: pass
            
            st_folium(m, width=1100, height=500)
            
            csv = df_r.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV Completo", csv, file_name=f"Lista_{cidade}_{raio}km.csv", mime="text/csv")