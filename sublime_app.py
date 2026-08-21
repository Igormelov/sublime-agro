import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="SUBLIME Agro - Dashboard Completo", layout="wide")
st.title("🌱 SUBLIME Agro - Gestão Completa")

# --- BANCO DE DADOS SIMPLES (salva em CSV no servidor) ---
FILE_FORN = "fornecedores.csv"
FILE_PROD = "produtos.csv"

def load_forn():
    if os.path.exists(FILE_FORN):
        return pd.read_csv(FILE_FORN)
    else:
        return pd.DataFrame(columns=["Fornecedor","CNPJ","Cidade","UF","Contato","WhatsApp","Categoria"])

def load_prod():
    if os.path.exists(FILE_PROD):
        return pd.read_csv(FILE_PROD)
    else:
        return pd.DataFrame(columns=["Fornecedor","Produto","Categoria_Produto","Preco","Estoque","Obs"])

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Clientes", "🏭 Fornecedores", "📦 Produtos por Fornecedor"])

with tab1:
    uploaded = st.file_uploader("Arraste sua Base de clientes.xlsx", type=["xlsx","csv"], key="cli")
    if uploaded:
        df = pd.read_excel(uploaded) if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)
        df.columns = [c.strip().upper() for c in df.columns]
        st.success(f"Base: {len(df)} clientes")
        
        # Procura colunas
        col_cidade = next((c for c in df.columns if 'CIDADE' in c or 'MUNIC' in c), None)
        col_cat = next((c for c in df.columns if 'CATEG' in c), None)
        
        if col_cidade:
            top = df[col_cidade].value_counts().head(20).reset_index()
            top.columns = ['Cidade','Qtd']
            fig = px.bar(top, x='Cidade', y='Qtd', title="Top Cidades")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.head(500), use_container_width=True)
    else:
        st.info("Suba a base de 88k aqui para ver o dashboard")

with tab2:
    st.header("Cadastro de Fornecedores")
    df_forn = load_forn()
    
    with st.form("form_forn", clear_on_submit=True):
        c1,c2 = st.columns(2)
        nome = c1.text_input("Nome Fornecedor*")
        cnpj = c2.text_input("CNPJ")
        cidade = c1.text_input("Cidade")
        uf = c2.text_input("UF", max_chars=2)
        contato = c1.text_input("Contato")
        zap = c2.text_input("WhatsApp")
        categ = st.selectbox("O que fornece?", ["Sementes","Fertilizantes","Defensivos","Máquinas","Outros"])
        if st.form_submit_button("💾 Salvar Fornecedor"):
            if nome:
                novo = pd.DataFrame([[nome,cnpj,cidade,uf,contato,zap,categ]], columns=df_forn.columns)
                df_forn = pd.concat([df_forn, novo], ignore_index=True)
                df_forn.to_csv(FILE_FORN, index=False)
                st.success(f"Fornecedor {nome} salvo!")
                st.rerun()
            else:
                st.error("Nome é obrigatório")

    st.divider()
    st.subheader(f"Fornecedores Cadastrados: {len(df_forn)}")
    edited_forn = st.data_editor(df_forn, num_rows="dynamic", use_container_width=True, key="edit_forn")
    if st.button("Salvar alterações na tabela de Fornecedores"):
        edited_forn.to_csv(FILE_FORN, index=False)
        st.success("Alterações salvas!")

with tab3:
    st.header("Quais produtos cada fornecedor fornece")
    df_forn = load_forn()
    df_prod = load_prod()
    
    if len(df_forn)==0:
        st.warning("Cadastre primeiro um fornecedor na Aba 2")
    else:
        with st.form("form_prod", clear_on_submit=True):
            forn_sel = st.selectbox("Selecione o Fornecedor", df_forn["Fornecedor"].unique())
            c1,c2 = st.columns(2)
            prod = c1.text_input("Produto* (ex: Soja 8473, Ureia 45%)")
            cat_prod = c2.selectbox("Categoria", ["Semente","Fertilizante","Defensivo","Foliar","Biológico"])
            preco = c1.text_input("Preço")
            estoque = c2.text_input("Estoque")
            obs = st.text_input("Obs")
            if st.form_submit_button("➕ Vincular Produto ao Fornecedor"):
                if prod:
                    novo = pd.DataFrame([[forn_sel,prod,cat_prod,preco,estoque,obs]], columns=df_prod.columns)
                    df_prod = pd.concat([df_prod, novo], ignore_index=True)
                    df_prod.to_csv(FILE_PROD, index=False)
                    st.success(f"{prod} vinculado a {forn_sel}!")
                    st.rerun()

        st.divider()
        # Filtro por fornecedor
        filtro_forn = st.selectbox("Filtrar por fornecedor", ["Todos"] + df_forn["Fornecedor"].tolist())
        if filtro_forn!="Todos":
            df_show = df_prod[df_prod["Fornecedor"]==filtro_forn]
        else:
            df_show = df_prod
            
        st.dataframe(df_show, use_container_width=True)
        
        # Gráfico
        if len(df_show)>0:
            fig = px.treemap(df_show, path=['Fornecedor','Produto'], title="Produtos por Fornecedor")
            st.plotly_chart(fig, use_container_width=True)
        
        # Baixar
        st.download_button("📥 Baixar lista de produtos", df_prod.to_csv(index=False).encode('utf-8'), "produtos_fornecedores.csv")
