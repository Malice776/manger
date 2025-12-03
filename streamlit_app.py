import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go
import folium
from gsheet_sync import (
    read_sheet_to_df,
    add_restaurant_to_sheet,
    update_restaurant_in_sheet,
    delete_restaurant_from_sheet,
    restaurant_exists,
    get_gsheet_client,
    SHEET_ID,
    WORKSHEET_NAME
)

# ------------------------
# Fonctions utilitaires
# ------------------------
def refresh_page():
    st.session_state['refresh_flag'] = not st.session_state.get('refresh_flag', False)

# ------------------------
# Configuration Streamlit
# ------------------------
st.set_page_config(layout='wide', page_title='Dashboard Restaurants')

# ------------------------
# Sidebar
# ------------------------
st.sidebar.title('🍽️ Navigation')
page = st.sidebar.selectbox(
    'Aller à', 
    [
        '📋 Tableau',
        '📊 Graphiques',
        '📅 Choix aléatoire',
        '📅 Choix aléatoire connu',
        '🗺️ Carte',
        '⚙️ Admin'
    ]
)
st.sidebar.button('Bouton magique 🎉', on_click=st.balloons)

# ------------------------
# PAGE GRAPHIQUES
# ------------------------
if page == '📊 Graphiques':
    st.title('📊 Graphiques des Restaurants')
    
    df = read_sheet_to_df()
    if df.empty:
        st.info('ℹ️ Aucune donnée – ajoutez des restaurants dans Google Sheets')
    else:
        numeric_cols = ['Marine', 'Corentin', 'Quentin']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df['moyenne'] = df[numeric_cols].mean(axis=1)

        # Graphique 1 : Moyennes et notes individuelles
        st.subheader('🏆 Moyennes et notes individuelles par restaurant')
        df_sorted = df.sort_values('moyenne', ascending=False).dropna(subset=['moyenne'])
        if not df_sorted.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_sorted['nom'],
                y=df_sorted['moyenne'],
                mode='lines+markers',
                name='Moyenne',
                line=dict(color='lightgreen', width=3, dash='dot')
            ))
            colors = ['lightgoldenrodyellow', 'lightcoral', 'powderblue']
            for i, col in enumerate(numeric_cols):
                if col in df_sorted.columns:
                    fig.add_trace(go.Scatter(
                        x=df_sorted['nom'],
                        y=df_sorted[col],
                        mode='lines+markers',
                        name=col,
                        line=dict(color=colors[i], width=2)
                    ))
            fig.update_layout(
                xaxis_tickangle=-45,
                yaxis_range=[0, 10],
                height=500,
                title='Notes individuelles et moyenne par restaurant',
                xaxis_title='Restaurant',
                yaxis_title='Note', 
                xaxis=dict(showgrid=True, gridcolor='Gray', gridwidth=1),
                yaxis=dict(showgrid=True, gridcolor='Gray', gridwidth=1)
            )
            st.plotly_chart(fig, width='stretch')

        # Graphique 2 : Notes par personne
        st.subheader("👥 Notes par personne")
        cols_to_plot = [c for c in numeric_cols if c in df.columns]
        if cols_to_plot:
            df_melted = df.melt(
                id_vars=['nom'],
                value_vars=cols_to_plot,
                var_name='Personne',
                value_name='Note'
            ).dropna(subset=['Note'])
            
            if not df_melted.empty:
                color_map = {'Marine':'lightgoldenrodyellow', 'Corentin':'lightsalmon', 'Quentin':'lightseagreen'}
                fig2 = px.bar(
                    df_melted,
                    x='nom',
                    y='Note',
                    color='Personne',
                    color_discrete_map=color_map,
                    barmode='group',
                    title='Notes par restaurant et par personne',
                    labels={'nom':'Restaurant', 'Note':'Note'}
                )
                fig2.update_layout(
                    xaxis_tickangle=-30,
                    height=500,
                    bargap=0.15,
                    bargroupgap=0.02
                )
                st.plotly_chart(fig2, width='stretch')

        # Graphique 3 : Nombre de visites
        st.subheader("🔢 Nombre de fois mangé par restaurant")
        if 'combien de fois on a mangé' in df.columns:
            df['visites'] = pd.to_numeric(df['combien de fois on a mangé'], errors='coerce').fillna(0)
            df_visites = df[['nom', 'visites']].copy()
            fig3 = px.pie(
                df_visites,
                names='nom',
                values='visites',
                title='Répartition des visites par restaurant',
                hole=0.3,
                labels={'visites': 'Nombre de visites'},
                width=650, height=650,
            )
            fig3.update_traces(texttemplate='%{value}', textfont_size=20)
            fig3.update_layout(
                legend=dict(
                    font=dict(size=18),
                    title=dict(text='Restaurants', font=dict(size=20)),
                    orientation="v",
                    x=1,
                    y=0.5
                ),
                title_font_size=24
            )
            st.plotly_chart(fig3, width='stretch')

# ------------------------
# PAGE TABLEAU
# ------------------------
elif page == '📋 Tableau':
    st.title('📋 Gestion des Restaurants')
    if 'refresh' not in st.session_state:
        st.session_state['refresh'] = False

    df = read_sheet_to_df()
    if st.session_state['refresh']:
        df = read_sheet_to_df()
        st.session_state['refresh'] = False

    if not df.empty:
        st.dataframe(df, width='stretch', height=400)
        st.caption(f'Total: {len(df)} restaurants')
    else:
        st.info('📭 Aucune donnée. Ajoutez des restaurants dans Google Sheets.')

    st.divider()
    st.subheader('➕ Ajouter / Modifier un restaurant')
    with st.form('entry_form'):
        nom = st.text_input('Nom du restaurant *', placeholder='Ex: McDo')
        marine = st.number_input('Note Marine (0-10)', min_value=0, max_value=10, step=1, value=5)
        corentin = st.number_input('Note Corentin (0-10)', min_value=0, max_value=10, step=1, value=5)
        quentin = st.number_input('Note Quentin (0-10)', min_value=0, max_value=10, step=1, value=5)
        visites = st.number_input('Combien de fois mangé', min_value=1, step=1, value=1)
        latitude = st.number_input('Latitude', value=48.8566, format="%.6f")
        longitude = st.number_input('Longitude', value=2.3522, format="%.6f")
        lien = st.text_input('Lien du restaurant', placeholder='https://...')

        submit = st.form_submit_button('💾 Enregistrer', type='primary')
        if submit:
            if not nom.strip():
                st.error('❌ Le nom du restaurant est obligatoire!')
            else:
                if restaurant_exists(nom.strip()):
                    update_restaurant_in_sheet(nom.strip(), marine, corentin, quentin, visites, latitude, longitude, lien)
                    st.success(f'✅ {nom} mis à jour dans Google Sheets!')
                    st.session_state['refresh'] = True
                    st.rerun()
                else:
                    add_restaurant_to_sheet(nom.strip(), marine, corentin, quentin, visites, latitude, longitude, lien)
                    st.success(f'✅ {nom} ajouté dans Google Sheets!')
                    st.session_state['refresh'] = True
                    st.rerun()

    st.divider()
    st.subheader('🗑️ Supprimer un restaurant')
    if not df.empty:
        to_delete = st.selectbox('Sélectionner un restaurant', [''] + df['nom'].tolist())
        if st.button('🗑️ Supprimer', type='secondary'):
            if to_delete:
                delete_restaurant_from_sheet(to_delete)
                st.success(f'✅ {to_delete} supprimé de Google Sheets!')
                st.session_state['refresh'] = True
                st.rerun()
            else:
                st.warning('⚠️ Veuillez sélectionner un restaurant')

# ------------------------
# PAGE CHOIX ALEATOIRE CONNU (notes)
# ------------------------
elif page == '📅 Choix aléatoire connu':
    st.title('🎰 Roulette du restaurant')
    df = read_sheet_to_df()
    if df.empty:
        st.info('ℹ️ Aucune donnée – ajoutez des restaurants dans Google Sheets')
    else:
        numeric_cols = ['Marine', 'Corentin', 'Quentin']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df['moyenne'] = df[numeric_cols].mean(axis=1)
        df = df.dropna(subset=['moyenne'])
        if df.empty:
            st.warning('⚠️ Les restaurants n’ont pas de notes valides')
        else:
            st.subheader("🎯 Tourner la roulette !")
            st.write("Plus la note moyenne est haute, plus le restaurant a de chance d'être choisi.")
            if st.button('🔄 Lancer la roulette'):
                probabilities = df['moyenne'].values + 0.1
                probabilities = probabilities / probabilities.sum()
                placeholder = st.empty()
                for _ in range(20):
                    chosen = np.random.choice(df['nom'], p=probabilities)
                    placeholder.markdown(f"🎲 Choix en cours… **{chosen}**")
                    time.sleep(0.1)
                chosen_final = np.random.choice(df['nom'], p=probabilities)
                placeholder.success(f'🎉 Aujourd\'hui, on mange chez **{chosen_final}** !')
                st.write("Bon appétit ! 🍽️")
                st.subheader("Probabilités de chaque restaurant")
                df_probs = df[['nom', 'moyenne']].copy()
                df_probs['Probabilité'] = probabilities
                st.dataframe(df_probs.sort_values('Probabilité', ascending=False))

# ------------------------
# PAGE CHOIX ALEATOIRE FEUILLE 3 (nom + site)
# ------------------------
elif page == '📅 Choix aléatoire':
    st.title('🎰 Bingo !')

    # 📌 Initialisation client Google Sheets
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)

    try:
        ws3 = sh.get_worksheet(2)  # Feuille 3 (index 2)
        data = ws3.get_all_values()
        if not data or len(data) < 2:
            st.info("ℹ️ Aucune donnée dans la Feuille 3")
        else:
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df[['nom', 'site']].dropna(subset=['nom']).drop_duplicates(subset='nom', ignore_index=True)
            st.subheader("🎯 Tourner la roulette des restaurants (Feuille 3)")
            if st.button('🔄 Lancer la roulette'):
                placeholder = st.empty()
                for _ in range(20):
                    chosen = df.sample(1).iloc[0]
                    placeholder.markdown(f"🎲 Choix en cours… **{chosen['nom']}**")
                    time.sleep(0.1)
                chosen_final = df.sample(1).iloc[0]
                placeholder.success(f"🎉 Aujourd'hui, on mange chez **{chosen_final['nom']}** !")
                if chosen_final['site']:
                    st.markdown(f"🔗 **Site :** [{chosen_final['site']}]({chosen_final['site']})")
                st.write("Bon appétit ! 🍽️")
                st.video('https://youtu.be/xvFZjo5PgG0', autoplay=True, end_time="20s", width=550)
                st.subheader("Liste des restaurants disponibles")
                st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture de la Feuille 3 : {e}")

# ------------------------
# PAGE CARTE
# ------------------------
elif page == '🗺️ Carte':
    st.title('🗺️ Carte des Restaurants')
    df = read_sheet_to_df()
    if df.empty:
        st.info('ℹ️ Aucune donnée – ajoutez des restaurants dans Google Sheets')
    else:
        required_cols = ['nom', 'latitude', 'longitude', 'lien']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.warning(f'⚠️ Les colonnes suivantes sont manquantes dans la feuille : {missing_cols}')
        else:
            center_lat = 48.85531573532454
            center_lon = 2.7815402176658344
            m = folium.Map(location=[center_lat, center_lon], zoom_start=17)
            for _, row in df.iterrows():
                popup_html = f"""
                <b>{row['nom']}</b><br>
                <a href="{row['lien']}" target="_blank">Lien du restaurant</a>
                """
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=popup_html,
                    tooltip=row['nom']
                ).add_to(m)
            import streamlit.components.v1 as components
            m.save("map.html")
            with open("map.html", "r", encoding="utf-8") as f:
                components.html(f.read(), height=500)


# ------------------------
# PAGE ADMIN
# ------------------------
elif page == '⚙️ Admin':
    st.title('⚙️ Administration Google Sheets')
    st.write(' ')
    st.write('⚠️ Attention : Demander à Marine pour des changements !')
    st.write(' ')

    df = read_sheet_to_df()
    if df.empty:
        st.info('ℹ️ Aucune donnée – ajoutez des restaurants dans Google Sheets')
    else:
        st.subheader('📊 Statistiques rapides')
        st.write(f"- Total restaurants : {len(df)}")
        numeric_cols = ['Marine', 'Corentin', 'Quentin']
        for col in numeric_cols:
            if col in df.columns:
                st.write(f"- Moyenne {col} : {df[col].mean():.2f}")
        
        st.subheader('🧹 Nettoyage des colonnes')
        if st.button('🧹 Supprimer colonnes incorrectes', type='secondary'):
            required_cols = ['nom', 'Marine', 'Corentin', 'Quentin', 'combien de fois on a mangé', 'latitude', 'longitude', 'lien']
            cleaned = df[required_cols].copy()
            client = get_gsheet_client()
            sh = client.open_by_key(SHEET_ID)
            ws = sh.worksheet(WORKSHEET_NAME)
            ws.clear()
            ws.append_row(list(cleaned.columns))
            for row in cleaned.itertuples(index=False):
                row_formatted = [str(x).replace('.', ',') if isinstance(x, (float, int)) else x for x in row]
                ws.append_row(row_formatted)
            st.success('✅ Colonnes nettoyées dans Google Sheets!')
            refresh_page()
