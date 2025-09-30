import streamlit as st
import pandas as pd
from datetime import date, datetime
import plotly.express as px
import gspread
from gsheet_sync import (
    read_sheet_to_df,
    add_restaurant_to_sheet,
    update_restaurant_in_sheet,
    delete_restaurant_from_sheet,
    restaurant_exists
)
import numpy as np
import time
import streamlit as st



def refresh_page():
    st.session_state['refresh_flag'] = not st.session_state.get('refresh_flag', False)

st.set_page_config(layout='wide', page_title='Dashboard Restaurants')

# Sidebar
st.sidebar.title('🍽️ Navigation')
page = st.sidebar.selectbox('Aller à', ['📋 Tableau','📊 Graphiques', '📅 Choix aléatoire', '⚙️ Admin'])
st.sidebar.button('Bouton magique 🎉', on_click=st.balloons)
# st.sidebar.button('🔄 Rafraîchir', on_click=refresh_page)
# ------------------------
# Page Graphiques
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
        # Calculer la moyenne
        df['moyenne'] = df[numeric_cols].mean(axis=1)

        # -------------------------
        # Graphique 1: Moyenne et notes individuelles par restaurant (ligne)
        # -------------------------
        st.subheader('🏆 Moyennes et notes individuelles par restaurant')
        df_sorted = df.sort_values('moyenne', ascending=False).dropna(subset=['moyenne'])
        if not df_sorted.empty:
            import plotly.graph_objects as go

            fig = go.Figure()

            # Ligne moyenne générale
            fig.add_trace(go.Scatter(
                x=df_sorted['nom'],
                y=df_sorted['moyenne'],
                mode='lines+markers',
                name='Moyenne',
                line=dict(color='lightgreen', width=3, dash='dot')
            ))

            # Lignes individuelles
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
            st.plotly_chart(fig, use_container_width=True)

        # -------------------------
        # Graphique 2: Notes par personne (bar) avec couleurs du graphique ligne et barres plus larges
        # -------------------------
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
                import plotly.express as px
                
                # Couleurs identiques au graphique ligne
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
                
                # Barres plus larges
                fig2.update_layout(
                    xaxis_tickangle=-30,
                    height=500,
                    bargap=0.15,       # écart entre les groupes
                    bargroupgap=0.02   # écart entre les barres d'un même groupe
                )
                
                st.plotly_chart(fig2, use_container_width=True)

        # -------------------------
        # Graphique 3: Nombre de visites (camembert avec valeurs)
        # -------------------------
        st.subheader("🔢 Nombre de fois mangé par restaurant")
        if 'combien de fois on a mangé' in df.columns:
            df['visites'] = pd.to_numeric(df['combien de fois on a mangé'], errors='coerce').fillna(0)
            df_visites = df[['nom', 'visites']].copy()
            
            fig3 = px.pie(
                df_visites,
                names='nom',
                values='visites',
                title='Répartition des visites par restaurant',
                hole=0.3,  # donut
                labels={'visites': 'Nombre de visites'},
                width=650, height=650,
            )
            fig3.update_traces(texttemplate='%{value}',
                               textfont_size=20)  # affiche les valeurs exactes
            

                        # Agrandir la légende
            fig3.update_layout(
                legend=dict(
                    font=dict(size=18),  # taille des labels de la légende
                    title=dict(text='Restaurants', font=dict(size=20)),  # optionnel : titre légende
                    orientation="v",  # vertical
                    x=1,  # position à droite
                    y=0.5
                ),
                title_font_size=24  # taille du titre
            )

            st.plotly_chart(fig3, use_container_width=True)

           


# ------------------------
# Page Tableau
# ------------------------
elif page == '📋 Tableau':
    st.title('📋 Gestion des Restaurants')

    # Initialisation session_state pour le refresh
    if 'refresh' not in st.session_state:
        st.session_state['refresh'] = False

    # Lecture du DataFrame
    df = read_sheet_to_df()

    # Rafraîchir si nécessaire
    if st.session_state['refresh']:
        df = read_sheet_to_df()
        st.session_state['refresh'] = False

    # Affichage du tableau
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=400)
        st.caption(f'Total: {len(df)} restaurants')
    else:
        st.info('📭 Aucune donnée. Ajoutez des restaurants dans Google Sheets.')

    st.divider()

    # Formulaire d'ajout / modification
    st.subheader('➕ Ajouter / Modifier un restaurant')
    with st.form('entry_form'):
        nom = st.text_input('Nom du restaurant *', placeholder='Ex: McDo')
        marine = st.number_input('Note Marine (0-10)', min_value=0, max_value=10, step=1, value=5)
        corentin = st.number_input('Note Corentin (0-10)', min_value=0, max_value=10, step=1, value=5)
        quentin = st.number_input('Note Quentin (0-10)', min_value=0, max_value=10, step=1, value=5)
        visites = st.number_input('Combien de fois mangé', min_value=1, step=1, value=1)
        
        submit = st.form_submit_button('💾 Enregistrer', type='primary')
        
        if submit:
            if not nom.strip():
                st.error('❌ Le nom du restaurant est obligatoire!')
            else:
                if restaurant_exists(nom.strip()):
                    update_restaurant_in_sheet(nom.strip(), marine, corentin, quentin, visites)
                    st.success(f'✅ {nom} mis à jour dans Google Sheets!')
                    st.session_state['refresh'] = True
                    st.rerun()  # Pour rafraîchir le tableau
                else:
                    add_restaurant_to_sheet(nom.strip(), marine, corentin, quentin, visites)
                    st.success(f'✅ {nom} ajouté dans Google Sheets!')
                    st.session_state['refresh'] = True
                    st.rerun()  # Pour rafraîchir le tableau
                
                st.session_state['refresh'] = True
                st.rerun()  # Pour rafraîchir le tableau

    st.divider()

    # Formulaire de suppression
    st.subheader('🗑️ Supprimer un restaurant')
    if not df.empty:
        to_delete = st.selectbox('Sélectionner un restaurant', [''] + df['nom'].tolist())
        if st.button('🗑️ Supprimer', type='secondary'):
            if to_delete:
                delete_restaurant_from_sheet(to_delete)
                st.success(f'✅ {to_delete} supprimé de Google Sheets!')
                st.session_state['refresh'] = True
                st.rerun()  # Pour rafraîchir le tableau
                
            else:
                st.warning('⚠️ Veuillez sélectionner un restaurant')


# ------------------------
# Pages Calendrier / Admin
# ------------------------
elif page == '📅 Choix aléatoire':
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

                # Conteneur pour l'effet roulette
                placeholder = st.empty()

                # Faire “tourner la roulette”
                for _ in range(20):  # nombre de tours
                    chosen = np.random.choice(df['nom'], p=probabilities)
                    placeholder.markdown(f"🎲 Choix en cours… **{chosen}**")
                    time.sleep(0.1)  # vitesse du tour

                # Résultat final
                chosen_final = np.random.choice(df['nom'], p=probabilities)
                placeholder.success(f'🎉 Aujourd\'hui, on mange chez **{chosen_final}** !')
                st.video('https://youtu.be/xvFZjo5PgG0', autoplay=True,end_time="15s",width=550)  # Rickroll
                st.write("Bon appétit ! 🍽️",)
                
                

                # Optionnel : afficher les probabilités
                st.subheader("Probabilités de chaque restaurant")
                df_probs = df[['nom', 'moyenne']].copy()
                df_probs['Probabilité'] = probabilities
                st.dataframe(df_probs.sort_values('Probabilité', ascending=False))

# ------------------------
# Page Admin
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
        
        # Nettoyage des colonnes incorrectes
        st.subheader('🧹 Nettoyage des colonnes')
        if st.button('🧹 Supprimer colonnes incorrectes', type='secondary'):
            # Conserver uniquement les colonnes nécessaires
            required_cols = ['nom', 'Marine', 'Corentin', 'Quentin', 'combien de fois on a mangé']
            cleaned = df[required_cols].copy()
            
            # Réécrire les données dans Google Sheets (supprimer toutes les lignes puis ajouter)
            from gsheet_sync import get_gsheet_client, SHEET_ID, WORKSHEET_NAME
            client = get_gsheet_client()
            sh = client.open_by_key(SHEET_ID)
            ws = sh.worksheet(WORKSHEET_NAME)

            ws.clear()  # vide la feuille
            ws.append_row(list(cleaned.columns))  # ajouter les entêtes
            for row in cleaned.itertuples(index=False):
                row_formatted = [str(x).replace('.', ',') if isinstance(x, (float, int)) else x for x in row]
                ws.append_row(row_formatted)

