# -*- coding: utf-8 -*-
"""
Created on Fri Apr 21 13:46:20 2023

@author: camil
"""

# Import de toutes les librairies nécessaires

import pandas as pd
import plotly.express as px
import numpy as np
from dash import Dash, dcc, html, Input, Output, dash_table

import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default='browser'
mapbox_access_token = "pk.eyJ1IjoiY3JvdXNzIiwiYSI6ImNrbmxpNTI2ejA3YmoydWt4MGQ0aGJxOTcifQ.aVndCa8vOi9Ycnrf-sDVZA"  # a renseigner

dict_jours={0:'Lundi', 1:'Mardi',2:'Mercredi',3:'Jeudi',4:'Vendredi',5:'Samedi',6:'Dimanche'}
dict_mois = {
    1: 'Janvier',
    2: 'Février',
    3: 'Mars',
    4: 'Avril',
    5: 'Mai',
    6: 'Juin',
    7: 'Juillet',
    8: 'Août',
    9: 'Septembre',
    10: 'Octobre',
    11: 'Novembre',
    12: 'Décembre'
}




# Ouverture des fichiers
df_compteurs=pd.read_csv('https://data.tours-metropole.fr/api/explore/v2.1/catalog/datasets/comptage-velo-compteurs-syndicat-des-mobilites-de-touraine/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B', delimiter=";",decimal=',')
df_comptage= pd.read_csv('https://data.tours-metropole.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs-syndicat-des-mobilites-de-touraine/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B',delimiter=";",decimal=',')

# Nettoyage des données
values = {"Numéro de série du compteur actuellement lié au site de comptage": 0, "photourl":'missing', "photo": 'missing'}
df_comptage=df_comptage.fillna(value=values)
df_comptage=df_comptage.dropna(subset=['Nom du compteur'])

df_compteurs=df_compteurs.fillna(value=values)
compteurs=df_comptage['Nom du compteur'].unique().tolist()

for c in compteurs:
    if (type(c)!= str):
        compteurs.remove(c)
    

# Ajout de colonnes pour faciliter la visualisation par date dans df_comptage
df_comptage['Date et heure de comptage']=pd.to_datetime(df_comptage['Date et heure de comptage'], utc=True)

df_comptage["Num Jour"]=df_comptage["Date et heure de comptage"].dt.dayofweek.astype(int)
df_comptage["Jour"]=df_comptage["Num Jour"].map(dict_jours)
df_comptage["Num Mois"]=df_comptage["Date et heure de comptage"].dt.month.astype(int)
df_comptage["Mois"]=df_comptage["Num Mois"].map(dict_mois)
df_comptage["Année"]=df_comptage["Date et heure de comptage"].dt.year


# Création d'un df df_info_compteurs contenant des informations détaillées par compteur
    
df_infos_compteurs = df_compteurs.copy()
df_infos_compteurs=df_infos_compteurs.sort_values('Nom du compteur')
df_infos_compteurs=df_infos_compteurs.set_index('Nom du compteur')

# ajout de colonnes moyenne quotidienne annuelle
for yr in list(range(2016,2024)):
    df = df_comptage.where(df_comptage['Année']==yr).groupby('Nom du compteur')[['Comptage quotidien']].mean()
    df.columns=['Moyenne quotidienne '+str(yr)]
    df_infos_compteurs=df_infos_compteurs.join(df)
    
# ajout de colonne min, max, jour min, jour max
df=df_comptage.groupby('Nom du compteur')[['Comptage quotidien']].min()
df.columns=['Passage quotidien minimum']
df_infos_compteurs=df_infos_compteurs.join(df)

df=df_comptage.groupby('Nom du compteur')[['Comptage quotidien']].max()
df.columns=['Passage quotidien maximum']
df_infos_compteurs=df_infos_compteurs.join(df)

#colonne top 10 jours min et top 10 jours max sur toute la période
df_infos_compteurs['Top_10_jours_moins_frequentes']=''
df_infos_compteurs['Top_10_jours_plus_frequentes'   ]=''
df_infos_compteurs['Moyenne Lun-Ven']=''
df_infos_compteurs['Moyenne Samedi']=''
df_infos_compteurs['Moyenne Dimanche']=''
df_infos_compteurs['Moyenne quotidienne']=''

for c in compteurs:
    min10= df_comptage.where(df_comptage['Nom du compteur']==c).nsmallest(10,'Comptage quotidien')['Date et heure de comptage'].tolist()
    max10 =df_comptage.where(df_comptage['Nom du compteur']==c).nlargest(10,'Comptage quotidien')['Date et heure de comptage'].tolist()
    moyluven=df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Num Jour']<=4)['Comptage quotidien'].mean()
    moysam=df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Num Jour']==5)['Comptage quotidien'].mean()
    moydim=df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Num Jour']==6)['Comptage quotidien'].mean()
    moy=df_comptage.where(df_comptage['Nom du compteur']==c)['Comptage quotidien'].mean()
    
    df_infos_compteurs.at[c, 'Top_10_jours_moins_frequentes']=min10
    df_infos_compteurs.at[c, 'Top_10_jours_plus_frequentes']=max10
    df_infos_compteurs.at[c,'Moyenne Lun-Ven']=moyluven
    df_infos_compteurs.at[c,'Moyenne Samedi']=moysam
    df_infos_compteurs.at[c,'Moyenne Dimanche']=moydim
    df_infos_compteurs.at[c,'Moyenne quotidienne']=moy

#Séparation des colonnes latitude et longitude
df_infos_compteurs[['lat', 'long']] = df_infos_compteurs["Coordonnées géographiques"].str.split(",", expand = True)
df_infos_compteurs[["lat", "long"]] = df_infos_compteurs[["lat", "long"]].apply(pd.to_numeric)
df_infos_compteurs=df_infos_compteurs.reset_index()

df_infos_compteurs['''Date d'installation du site de comptage'''] = pd.to_datetime(df_infos_compteurs['''Date d'installation du site de comptage'''])

df_info_tr=df_infos_compteurs.copy().reset_index()

df_info_tr.drop(['Top_10_jours_plus_frequentes','Top_10_jours_moins_frequentes'], axis=1, inplace=True)
df_info_tr=df_info_tr.transpose()
df_info_tr=df_info_tr.drop('index')
df_info_tr=df_info_tr.reset_index()
df_info_tr=df_info_tr.fillna(0)
df_info_tr.columns=df_info_tr.iloc[0]
df_info_tr=df_info_tr.drop([0])
df_info_tr=df_info_tr.set_index('Nom du compteur')

df=df_infos_compteurs.copy()
df=df.fillna(0)
df['Moyenne quotidienne']=pd.to_numeric(df_infos_compteurs['Moyenne quotidienne'])
compteurs=df.sort_values('Moyenne quotidienne', ascending=False)['Nom du compteur'].unique().tolist()

# Fonction permettant de créer des graphiques en barre selon la granularité temporelle souhaitée

def plot_average_by(compteur, column_name):
    df_comptage.set_index(column_name)
    df_filtered= df_comptage.where(df_comptage['Nom du compteur']==compteur )
    df_filtered=df_filtered.dropna()
    df_res=df_filtered.groupby(column_name)[['Comptage quotidien']].mean()
    return(df_res)
    #fig=px.bar(df_res, title="Passage sur "+compteur+" : évolution de la moyenne quotidienne, par "+column_name )
    #fig.show()
  

def plot_all_locations( title='Carte des compteurs de la métropole'):
    df=df_infos_compteurs.copy().reset_index()
   
    df['Moyenne quotidienne']=pd.to_numeric(df['Moyenne quotidienne'])
    df['Moyenne quotidienne']=df['Moyenne quotidienne'].fillna(0)
    px.set_mapbox_access_token(mapbox_access_token)
    fig = px.scatter_mapbox(df, lat="lat", lon="long",
                    color_discrete_sequence=['red'] ,  zoom=5, hover_name="Nom du compteur", size='Moyenne quotidienne')

    fig.update_layout( mapbox_style="basic",
    title=title,
    autosize=True,
    hovermode='closest',
    showlegend=True,
    mapbox=dict(
      accesstoken=mapbox_access_token,
      bearing=0,
      center=dict(
          lat=df_infos_compteurs.lat.mean(),
          lon=df_infos_compteurs.long.mean(),
      ),
      pitch=0,
      zoom=12,
      style='satellite-streets'
    ),

    )
    return(fig)



def get_fig_jours_plus_moins(chosen):
    if type(chosen)!=list:
        chosen=list(chosen)
    dff=df_infos_compteurs.copy().reset_index()
    # Creation des graphiques en barres top10 jours moins fréquentés
    df_plus=pd.DataFrame(columns=['Dt','Date', 'Passages', 'Nom'])
    df_moins=pd.DataFrame(columns=['Dt','Date', 'Passages', 'Nom'])
    for c in chosen:
        dfff=dff.loc[dff['Nom du compteur']==c]
        top10moins=dfff['Top_10_jours_moins_frequentes'].values[0]
        top10plus=dfff['Top_10_jours_plus_frequentes'].values[0]

        list_topmoins=[dict_jours[(k.date().weekday())]+' '+str(k.date().day)+' '+dict_mois[(k.date().month)]+' '+str(k.date().year) for k in top10moins]
        values_top10moins=[df_comptage.loc[(df_comptage['Nom du compteur']==c) & (df_comptage['Date et heure de comptage']==d)]['Comptage quotidien'].iloc[0] for d in top10moins]
        list_topplus=[dict_jours[(k.date().weekday())]+' '+str(k.date().day)+' '+dict_mois[(k.date().month)]+' '+str(k.date().year) for k in top10plus]
        values_top10plus=[df_comptage.loc[(df_comptage['Nom du compteur']==c) & (df_comptage['Date et heure de comptage']==d)]['Comptage quotidien'].iloc[0] for d in top10plus]

        df_moins=pd.concat([df_moins, 
                            pd.DataFrame({'Date':list_topmoins,'Passages':values_top10moins, 'Nom':c})])
        df_plus=pd.concat([df_plus, 
                           pd.DataFrame({'Date':list_topplus,'Passages':values_top10plus, 'Nom':c})])
    df_plus=df_plus.sort_values('Passages')
    df_moins=df_moins.sort_values('Passages',ascending=False)
    fig_top10moins=px.bar(df_moins,  y='Date', x='Passages', orientation='h', title ='Top 10 des jours les moins fréquentés', color='Nom', barmode='group')   
    fig_top10moins.update_layout(yaxis_title=None)

    fig_top10plus=px.bar(df_plus,  y='Date', x='Passages', orientation='h', title ='Top 10 des jours les plus fréquentés', color='Nom', barmode='group') 
    fig_top10plus.update_layout(yaxis_title=None)
    return(fig_top10moins,fig_top10plus)   
    
def get_evolution(compteur):
    df=df_infos_compteurs.copy().reset_index()
    df_compteur=df_comptage[df_comptage['Nom du compteur']==compteur].sort_values('Date et heure de comptage', ascending=False).reset_index()

    most_recent_line=df_compteur.iloc[0][['Date et heure de comptage', 'Comptage quotidien', 'Jour','Mois','Année']]
    most_recent_date=most_recent_line['Date et heure de comptage']
    
    j=most_recent_line['Jour']
    n=most_recent_date.day
    m=most_recent_line['Mois']
    a= most_recent_line['Année']
    str_date=str(j)+' '+str(n)+' '+str(m)+' '+str(a)
    derniere_date=most_recent_line['Date et heure de comptage']
    dernier_comptage=int(most_recent_line['Comptage quotidien'])
    
    comptage_30_derniers_jours=int(df_compteur.iloc[0:30][ 'Comptage quotidien'].sum())
    comptage_mois_precedent=int(df_compteur.iloc[31:61]['Comptage quotidien'].sum())

    same_day_last_week = derniere_date-pd.Timedelta(weeks=1)
    date_last_year=derniere_date-pd.DateOffset(years=1)
    
    val_last_week = int(df_compteur[df_compteur['Date et heure de comptage']==same_day_last_week]['Comptage quotidien'])
    val_last_year = int(df_compteur[df_compteur['Date et heure de comptage']==date_last_year]['Comptage quotidien'])
    
    s_evo_sem, s_evo_mois, s_evo_an='-','-','-'
    
    evol_j_semaine= int(100*(dernier_comptage-val_last_week)/val_last_week)  
    evol_mois=int(100*(comptage_30_derniers_jours-comptage_mois_precedent)/comptage_mois_precedent)    
    evol_an=int(100*(dernier_comptage-val_last_year)/val_last_year)
    
    if np.sign(evol_j_semaine)>0:
        s_evo_sem='+'       
    if np.sign(evol_mois)>0:
        s_evo_mois='+'
    if np.sign(evol_an)>0:
        s_evo_an='+'
    
    e_s = s_evo_sem+' '+ str(abs(evol_j_semaine))+'%'
    e_m = s_evo_mois +' '+ str(abs(evol_mois))+'%'
    e_a = s_evo_an+' '+ str(abs(evol_an))+'%'
    
    #print(len(df_compteur.iloc[31:61]['Comptage quotidien']), len(df_compteur.iloc[0:30][ 'Comptage quotidien']))
    
    return  ([compteur+' '+str_date,e_s+''' par rapport au '''+j+''' précédent''',
             e_m+''' sur les 30 derniers jours par rapport aux 30 jours précédents''',
            e_a+''' par rapport au '''+str(n)+' '+str(m)+' '+str(a-1)])

 # initialize app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server=app.server

# set app layout
app.layout = html.Div(children=[
    html.H1('Visualisation des passages de vélo : Métropole de Tours', style={'textAlign':'center'}),
    html.Br(),
    
    dcc.Graph(figure=plot_all_locations()),
    html.Div([
        html.H3(''' Sélectionnez les compteurs dont vous souhaitez visualiser l'évolution.''', style={'textAlign': 'center'}),
        dcc.Dropdown(
        options=compteurs,
        value=['Pont Wilson'],
        id='compteurs_choisis',
        style={"width": "50%", "offset":1,},
        clearable=False,
        multi=True
    ),
    dcc.Dropdown(
        options=['Evolution de la moyenne quotidienne sur toute la période',
                 'Evolution de la moyenne quotidienne par jour de la semaine',
                 'Evolution de la moyenne quotidienne par mois de l''année',
                 'Evolution de la moyenne quotidienne par année'],
        value='Evolution de la moyenne quotidienne sur toute la période',
        id='periodicite',
        style={"width": "50%", "offset":1,},
        clearable=False,
        multi=False
    )]),
    dcc.Graph(id='bar'),
    html.Div(id='texte_infos_evolution'),
    html.Div(html.Table(
        html.Tr([
            html.Td([
                dcc.Graph(id='top10plus')
            ]),
            html.Td([
                dcc.Graph(id='top10moins')
            ])
        ])
    )),    
    html.H3(''' Comparaison par jour de la semaine''', style={'textAlign': 'center'}),    
    dcc.Graph(id='bar2'),
    html.Div(
           id='table'
       )
    
    
])

# callbacks
@app.callback(
    Output(component_id='bar', component_property='figure'),
    Output('table', 'children' ),
    Output('top10plus', 'figure'),
    Output('top10moins', 'figure'),
    Output('bar2', 'figure'),
    Output('texte_infos_evolution','children'),
    Input('compteurs_choisis', 'value'),
    Input('periodicite', 'value')
)

def update_hist(chosen,periodicite):
    dict_period={'Evolution de la moyenne quotidienne sur toute la période':'Date et heure de comptage','Evolution de la moyenne quotidienne par jour de la semaine':'Num Jour',  'Evolution de la moyenne quotidienne par mois de l''année':'Num Mois', 'Evolution de la moyenne quotidienne par année': 'Année'}
    compteur_0=chosen[0]
# Creation des graphiques en barres top10 jours moins fréquentés
    fig_moins, fig_plus=get_fig_jours_plus_moins(chosen) 
    fig_moins.update_layout(showlegend=False)

    
#Graphique principal     
    df_evolution=plot_average_by(chosen[0], dict_period[periodicite])
    df_evolution['Nom']=chosen[0]
    
    for c in chosen[1:] :
        df_temp=plot_average_by(c, dict_period[periodicite])
        df_temp['Nom']=c
        df_evolution=pd.concat([df_evolution, df_temp])
    df_evolution=df_evolution.reset_index()
       
    fig=px.bar(df_evolution, y='Comptage quotidien', x=dict_period[periodicite], color='Nom',barmode='group')
    fig.update_yaxes(title_text='Comptage quotidien moyen')

    
    if periodicite == 'Evolution de la moyenne quotidienne sur toute la période':
        df_evolution=df_evolution.reset_index()
        df_evolution['Date']=df_evolution['Date et heure de comptage'].apply(lambda k: dict_jours[(k.date().weekday())]+' '+str(k.date().day)+' '+dict_mois[(k.date().month)]+' '+str(k.date().year))
        df_evolution['Date et heure de comptage']=pd.to_datetime(df_evolution['Date et heure de comptage']).dt.date
        fig=px.bar(df_evolution, x='Date et heure de comptage', y='Comptage quotidien', color='Nom', barmode='group',hover_name='Date', hover_data={'Nom': True,'Comptage quotidien':True,'Date et heure de comptage':False,'Date':False})
        fig.update_yaxes(title_text='Comptage quotidien')

    if periodicite =='Evolution de la moyenne quotidienne par jour de la semaine':
        fig.update_xaxes(labelalias=dict_jours)
        fig.update_xaxes(title_text='Jour')

        
    if periodicite == 'Evolution de la moyenne quotidienne par mois de l''année':
       fig.update_xaxes(labelalias=dict_mois)
       fig.update_xaxes(title_text='Mois')
       
    fig.update_layout(hovermode="x unified")
       
 #creation de la visualisation par jour de la semaine      
    dff=df_infos_compteurs[df_infos_compteurs['Nom du compteur']==compteur_0][['Moyenne Lun-Ven','Moyenne Samedi','Moyenne Dimanche','Moyenne quotidienne']].transpose().reset_index()
    dff.columns = ['Donnée', 'Passages']
    dff['Nom']=compteur_0
    for c in chosen[1:] :
        df_temp=df_infos_compteurs[df_infos_compteurs['Nom du compteur']==c][['Moyenne Lun-Ven','Moyenne Samedi','Moyenne Dimanche','Moyenne quotidienne']].transpose().reset_index()
        df_temp.columns=['Donnée', 'Passages']
        df_temp['Nom']=c
        dff=pd.concat([dff, df_temp])
    
    fig_compteur=px.bar(dff, x='Donnée', y='Passages', color='Nom', barmode='group')    
    
    
    return(fig, 
           dash_table.DataTable(data=df_info_tr[chosen].reset_index().to_dict('records'),css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
    style_cell={
        'width': '{}%'.format(len(df.columns)),
        'textOverflow': 'ellipsis',
        'overflow': 'hidden' }),
        fig_plus,
        fig_moins,
        fig_compteur,
        dash_table.DataTable(data=([get_evolution(c) for c in chosen]),css=[{'selector': 'table', 'rule': 'table-layout: fixed'}]
        ))


if __name__ == "__main__":
    app.run_server(debug=True)     



    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
