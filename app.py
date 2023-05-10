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
from datetime import datetime
from datetime import date

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
df_jf=pd.read_csv('https://etalab.github.io/jours-feries-france-data/csv/jours_feries_metropole.csv', usecols=['date', 'nom_jour_ferie'])
df_vacances=pd.read_csv('https://raw.githubusercontent.com/AntoineAugusti/vacances-scolaires/master/data.csv', usecols=['date', 'vacances_zone_b', 'nom_vacances'])


df_comptage['Date et heure de comptage']=pd.to_datetime(df_comptage['Date et heure de comptage'], utc=True)
df_comptage['Date et heure de comptage']=df_comptage['Date et heure de comptage']+pd.Timedelta(days=1)
df_comptage['date']=pd.to_datetime(df_comptage['Date et heure de comptage']).dt.date
df_jf['date']=pd.to_datetime(df_jf['date']).dt.date
df_vacances['date']=df_vacances['date']=pd.to_datetime(df_vacances['date']).dt.date


# Ajout des colonnes vacances et jours feriés
df_comptage=df_comptage.merge(df_jf, how='left', left_on='date', right_on='date') # Ajout des jours fériés
df_comptage=df_comptage.merge(df_vacances, how='left', left_on='date', right_on='date') # Ajout des vacances

# On réordonne les colonnes:
df_comptage=df_comptage[['date',
 'Nom du compteur',
 'Comptage quotidien',
 'Status',
'Identifiant du site de comptage',
 'Numéro de série du compteur actuellement lié au site de comptage',
 'Coordonnées géographiques',
 "Date d'installation du site de comptage",
 'Informations de direction',
 "Intervalle d'enregistrement des données",
 'User Type',
 'TimeZone',
 'photourl',
 'photo',
 'nom_jour_ferie', 'vacances_zone_b','nom_vacances']]



# Nettoyage des données
values = {"Numéro de série du compteur actuellement lié au site de comptage": 0, "photourl":'missing', "photo": 'missing'}
df_comptage=df_comptage.fillna(value=values)
df_comptage=df_comptage.dropna(subset=['Nom du compteur'])

df_compteurs=df_compteurs.fillna(value=values)

#création d'un liste des compteurs
l=df_comptage['Nom du compteur'].unique().tolist()
compteurs=l.copy()

# Nettoyage de la liste de compteurs: on enlève tous ceux qui ont moins de 30 comptages
for c in l:
    if (type(c)!= str) or (len(df_comptage[df_comptage['Nom du compteur']==c])<30) or (c not in df_compteurs['Nom du compteur'].unique()):
        compteurs.remove(c)

# Ajout de colonnes pour faciliter la visualisation par date dans df_comptage

df_comptage["Num Jour"]=pd.to_datetime(df_comptage["date"]).dt.dayofweek.astype(int)
df_comptage["Jour"]=df_comptage["Num Jour"].map(dict_jours)

df_comptage["Num Mois"]=pd.to_datetime(df_comptage["date"]).dt.month.astype(int)
df_comptage["Mois"]=df_comptage["Num Mois"].map(dict_mois)

df_comptage["Année"]=pd.to_datetime(df_comptage["date"]).dt.year

# Création d'un tableau "df_info_compteurs" contenant des informations détaillées par compteur
    
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
df_infos_compteurs['Moyenne Lun-Ven, hors jf']=''
df_infos_compteurs['Moyenne Samedi, hors jf']=''
df_infos_compteurs['Moyenne Dimanche, hors jf']=''
df_infos_compteurs['Moyenne jours feriés']=''
df_infos_compteurs['Moyenne vacances']=''


for c in compteurs:
    min10= df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Comptage quotidien']>0).nsmallest(10,'Comptage quotidien')['date'].tolist()
    max10 =df_comptage.where(df_comptage['Nom du compteur']==c).nlargest(10,'Comptage quotidien')['date'].tolist()
    
    moyluven=df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Num Jour']<=4).where(df_comptage['nom_jour_ferie'].isna())['Comptage quotidien'].mean()
    moysam=df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Num Jour']==5).where(df_comptage['nom_jour_ferie'].isna())['Comptage quotidien'].mean()
    moydim=df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['Num Jour']==6).where(df_comptage['nom_jour_ferie'].isna())['Comptage quotidien'].mean()
    moy=df_comptage.where(df_comptage['Nom du compteur']==c)['Comptage quotidien'].mean()
    moyenne_jf= df_comptage.where(df_comptage['Nom du compteur']==c).where(df_comptage['nom_jour_ferie'].notnull())['Comptage quotidien'].mean()
    moyenne_vacances = df_comptage[(df_comptage['Nom du compteur']==c) & (df_comptage['vacances_zone_b']==True)]['Comptage quotidien'].mean()
    
    df_infos_compteurs.at[c, 'Top_10_jours_moins_frequentes']=min10
    df_infos_compteurs.at[c, 'Top_10_jours_plus_frequentes']=max10
    df_infos_compteurs.at[c,'Moyenne Lun-Ven, hors jf']=moyluven
    df_infos_compteurs.at[c,'Moyenne Samedi, hors jf']=moysam
    df_infos_compteurs.at[c,'Moyenne Dimanche, hors jf']=moydim
    df_infos_compteurs.at[c,'Moyenne quotidienne']=moy
    df_infos_compteurs.at[c, 'Moyenne jours feriés']= moyenne_jf
    df_infos_compteurs.at[c, 'Moyenne vacances']=moyenne_vacances

#Séparation des colonnes latitude et longitude
df_infos_compteurs[['lat', 'long']] = df_infos_compteurs["Coordonnées géographiques"].str.split(",", expand = True)
df_infos_compteurs[["lat", "long"]] = df_infos_compteurs[["lat", "long"]].apply(pd.to_numeric)
df_infos_compteurs=df_infos_compteurs.reset_index()

df_infos_compteurs['''Date d'installation du site de comptage'''] = pd.to_datetime(df_infos_compteurs['''Date d'installation du site de comptage'''])


df_info_tr=df_infos_compteurs.copy().reset_index()

#tableau de tous les compteurs, sans les colonnes top 10 et min 10

df_info_tr.drop(['Top_10_jours_plus_frequentes','Top_10_jours_moins_frequentes'], axis=1, inplace=True)
df_info_tr=df_info_tr.transpose()
df_info_tr=df_info_tr.drop('index')
df_info_tr=df_info_tr.reset_index()
df_info_tr=df_info_tr.fillna(0)
df_info_tr.columns=df_info_tr.iloc[0]
df_info_tr=df_info_tr.drop([0])
df_info_tr=df_info_tr.set_index('Nom du compteur')


# liste des compteurs actifs
df=df_infos_compteurs.copy()
df=df.fillna(0)
df['Moyenne quotidienne']=pd.to_numeric(df_infos_compteurs['Moyenne quotidienne'])
compteurs=df.sort_values('Moyenne quotidienne', ascending=False)['Nom du compteur'].unique().tolist()

# Fonction permettant de créer des graphiques en barre selon la granularité temporelle souhaitée

def plot_average_by(compteur, column_name, start=df_comptage['date'].min(), end=df_comptage['date'].max(), moyenne=True):
    df_comptage.set_index(column_name)
    df_filtered= df_comptage.loc[(df_comptage['Nom du compteur']==compteur)&(df_comptage['date']>=start) & (df_comptage['date'] <= end)]
    if moyenne:
     df_res=df_filtered.groupby(column_name)[['Comptage quotidien']].mean()
    else:
        df_res=df_filtered.groupby(column_name)[['Comptage quotidien']].sum()
    return(df_res)

  

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


# renvoie deux graphiques en barres, pour une liste de compteurs, donnant les top10 jours les plus fréquentés et top10 jours les moins fréquentés
def get_fig_jours_plus_moins(chosen, start=df_comptage['date'].min(), end=df_comptage['date'].max()):

    if type(chosen)!=list:
        chosen=list(chosen)
    c=chosen[0]
    print(c)
    
    df_min10= df_comptage.loc[(df_comptage['Nom du compteur']==c) & (df_comptage['date']>=start) & (df_comptage['date'] <= end) & (df_comptage['Comptage quotidien']>0)].nsmallest(10,'Comptage quotidien')[['Nom du compteur','date', 'Comptage quotidien', 'nom_jour_ferie', 'vacances_zone_b']].sort_values('Comptage quotidien', ascending=True)
    df_max10= df_comptage.loc[(df_comptage['Nom du compteur']==c) & (df_comptage['date']>=start) & (df_comptage['date'] <= end) & (df_comptage['Comptage quotidien']>0)].nlargest(10,'Comptage quotidien')[['Nom du compteur','date', 'Comptage quotidien', 'nom_jour_ferie', 'vacances_zone_b']].sort_values('Comptage quotidien', ascending=False)

    
    for c in chosen[1:]:
        df_temp_min= df_comptage.loc[(df_comptage['Nom du compteur']==c) & (df_comptage['date']>=start) & (df_comptage['date'] <= end) & (df_comptage['Comptage quotidien']>0)].nsmallest(10,'Comptage quotidien')[['Nom du compteur','date', 'Jour', 'Comptage quotidien', 'nom_jour_ferie', 'vacances_zone_b']].sort_values('Comptage quotidien', ascending=True)
        df_temp_max=df_comptage.loc[(df_comptage['Nom du compteur']==c) & (df_comptage['date']>=start) & (df_comptage['date'] <= end) & (df_comptage['Comptage quotidien']>0)].nlargest(10,'Comptage quotidien')[['Nom du compteur','date', 'Jour', 'Comptage quotidien', 'nom_jour_ferie', 'vacances_zone_b']].sort_values('Comptage quotidien', ascending=False)

        df_min10=pd.concat([df_min10, df_temp_min])
        df_max10= pd.concat([df_max10, df_temp_max])
        
    df_min10['date']=df_min10['date'].apply(lambda k: dict_jours[(k.weekday())]+' '+str(k.day)+' '+dict_mois[(k.month)]+' '+str(k.year))
    df_max10['date']=df_max10['date'].apply(lambda k: dict_jours[(k.weekday())]+' '+str(k.day)+' '+dict_mois[(k.month)]+' '+str(k.year))

        
    df_min10['Pattern'] = np.nan
    df_min10.loc[(df_min10['nom_jour_ferie'].notna()) & (df_min10['vacances_zone_b']==True), 'Pattern'] = 'Ferié et Vacances'
    df_min10.loc[(df_min10['nom_jour_ferie'].notna()) & (df_min10['vacances_zone_b']==False), 'Pattern'] = 'Ferié'
    df_min10.loc[(df_min10['nom_jour_ferie'].isna()) & (df_min10['vacances_zone_b']==True), 'Pattern'] = 'Vacances'
    df_min10.loc[(df_min10['nom_jour_ferie'].isna()) & (df_min10['vacances_zone_b']==False), 'Pattern'] = 'Jour quelconque'
    
    
    df_max10['Pattern'] = np.nan
    df_max10.loc[(df_max10['nom_jour_ferie'].notna()) & (df_max10['vacances_zone_b']==True), 'Pattern'] = 'Ferié et Vacances'
    df_max10.loc[(df_max10['nom_jour_ferie'].notna()) & (df_max10['vacances_zone_b']==False), 'Pattern'] = 'Ferié'
    df_max10.loc[(df_max10['nom_jour_ferie'].isna()) & (df_max10['vacances_zone_b']==True), 'Pattern'] = 'Vacances'
    df_max10.loc[(df_max10['nom_jour_ferie'].isna()) & (df_max10['vacances_zone_b']==False), 'Pattern'] = 'Jour quelconque'
    
    df_max10=df_max10.sort_values('Comptage quotidien', ascending=False)
    df_min10=df_min10.sort_values('Comptage quotidien', ascending= True)
    
    pattern_shapes = {
    'Ferié et Vacances': 'x',
    'Vacances': '/',
    'Ferié': '\\', 'Jour quelconque':''}
    
    fig_top10moins=px.bar(df_min10,  y='date', x='Comptage quotidien', orientation='h', title ='Top 10 des jours les moins fréquentés', color='Nom du compteur', pattern_shape='Pattern', pattern_shape_map=pattern_shapes, barmode='group')   
    fig_top10plus=px.bar(df_max10,  y='date', x='Comptage quotidien', orientation='h', title ='Top 10 des jours les plus fréquentés', color='Nom du compteur', pattern_shape='Pattern', pattern_shape_map=pattern_shapes, barmode='group') 
    
    return(fig_top10moins, fig_top10plus) 


# fonction qui renvoie un dict avec l'évolution d'un certain compteur    
def get_evolution(compteur):
    df=df_infos_compteurs.copy().reset_index()
    df_compteur=df_comptage[df_comptage['Nom du compteur']==compteur].sort_values('date', ascending=False).reset_index()

    most_recent_line=df_compteur.iloc[0][['date', 'Comptage quotidien', 'Jour','Mois','Année']]
    most_recent_date=most_recent_line['date']
    
    date_install=df[df['Nom du compteur']== compteur]['''Date d'installation du site de comptage'''].iloc[0]
    
    j=most_recent_line['Jour']
    n=most_recent_date.day
    m=most_recent_line['Mois']
    a= most_recent_line['Année']
    str_date=str(j)+' '+str(n)+' '+str(m)+' '+str(a)
    derniere_date=most_recent_line['date']
    dernier_comptage=int(most_recent_line['Comptage quotidien'])    
    same_day_last_week = derniere_date-pd.Timedelta(weeks=1)
    date_last_year=(derniere_date-pd.DateOffset(years=1)).date()
    
    s_evo_sem, s_evo_mois, s_evo_an='-','-','-'
    
    if same_day_last_week >= date_install:
            val_last_week = int(df_compteur[df_compteur['date']==same_day_last_week]['Comptage quotidien'])
            evol_j_semaine= int(100*(dernier_comptage-val_last_week)/val_last_week)
            if np.sign(evol_j_semaine)>0:
                s_evo_sem='+'
            e_s = s_evo_sem+' '+ str(abs(evol_j_semaine))+'%'
            e_s= e_s+ ''' par rapport au '''+j+''' précédent'''
    else: 
        e_s='Indisponible, compteur installé le '+str(date_install)
                

    if date_last_year >= date_install:
        val_last_year = int(df_compteur[df_compteur['date']==date_last_year]['Comptage quotidien'])
        evol_an=int(100*(dernier_comptage-val_last_year)/val_last_year)
        if np.sign(evol_an)>0:
            s_evo_an='+'
        e_a = s_evo_an+' '+ str(abs(evol_an))+'%'
        e_a=e_a+''' par rapport au '''+str(n)+' '+str(m)+' '+str(a-1)

    else:
        e_a='Indisponible, compteur installé le '+str(date_install)
            
    
    comptage_30_derniers_jours=int(df_compteur.iloc[0:30][ 'Comptage quotidien'].sum())
    comptage_mois_precedent=int(df_compteur.iloc[31:61]['Comptage quotidien'].sum())
    
    if len(df_compteur)>60:
        evol_mois=int(100*(comptage_30_derniers_jours-comptage_mois_precedent)/comptage_mois_precedent)
        if np.sign(evol_mois)>0:
            s_evo_mois='+'
        e_m = s_evo_mois +' '+ str(abs(evol_mois))+'%'
        e_m=e_m+''' sur les 30 derniers jours par rapport aux 30 jours précédents'''
        
    else: 
        e_m='Indisponible, compteur installé le '+str(date_install)
            
    
    return  ({'Compteur':compteur, 'Dernier enregistrement': str_date, 'Par rapport à la semaine précédente': e_s,
             'Evolution de la moyenne mensuelle': e_m,
            '''Evolution par rapport à l'année dernière''':e_a})
            
# Fonction qui prend un nom de compteur et renvoie un DF de passages quotidiens par mois 
def df_moyenne_mensuelle(compteur, start=df_comptage['date'].min(), end=df_comptage['date'].max()):
    df=df_comptage[(df_comptage['Nom du compteur']==compteur) & (df_comptage['date']>= start) & (df_comptage['date']<=end)][['date', 'Comptage quotidien']]
    df['date']=pd.to_datetime(df['date'])
    df=df.set_index('date')                                        
    df= df.resample('M').mean()
    df=df.reset_index()
    df['Comptage quotidien']=df['Comptage quotidien'].fillna(0)
    df['Comptage quotidien']=df['Comptage quotidien'].astype(int)
    df['Num Mois']=df['date'].dt.month.astype(int)
    df['Mois']=df['Num Mois'].map(dict_mois)
    df['Année']=df['date'].dt.year.astype(int)
    df['date']=df['date'].dt.date
    df.columns=['date', 'Moyenne quotidienne', 'Numéro de mois', 'Mois', 'Année']
    df['Période']=df['Mois'].astype(str)+' '+df['Année'].astype(str)
    
    return(df)

        
# fonction qui prend une liste de noms de compteurs
# et renvoie un graphique ligne de moyenne mensuelle + les paramèetres de la régression linéaire associée

def plot_moyennes_mensuelles(chosen,start=df_comptage['date'].min(), end=df_comptage['date'].max()):
    df=df_moyenne_mensuelle(chosen[0], start, end)
    df['Nom']=chosen[0]
    df['date_delta'] = (df['date'] - df['date'].min())  / np.timedelta64(1,'D')
    date_install_min= df_infos_compteurs[df_infos_compteurs['Nom du compteur'].isin(chosen)]['''Date d'installation du site de comptage'''].min()
    
    for c in chosen[1:] :
        df_temp= df_moyenne_mensuelle(c, start, end)
        df_temp['Nom']=c
        df_temp['date_delta'] = df_temp['date'].apply(lambda x: (pd.to_datetime(x) - pd.to_datetime(date_install_min) )/ np.timedelta64(1,'D'))
        df=pd.concat([df, df_temp])


    fig=px.line(df, x=df['date'], y=df['Moyenne quotidienne'], color='Nom', hover_name='Nom', hover_data={'Nom':False, "date":False, 'Période':True,'Moyenne quotidienne': True},  line_shape='linear')
    fig.update_traces(marker={'size': 5})

    fig2=px.scatter(data_frame=df, x='date_delta', y='Moyenne quotidienne', color='Nom', trendline='ols').update_traces(mode='lines')
    
    results = px.get_trendline_results(fig2)
    #print(results)
    results=results.set_index('Nom')
    
    dict_param={}
    df['pente']=''
    df['y intercept']=''
    for c in chosen:
        if c in results.index:
            dict_param[c]=results.loc[c]['px_fit_results'].params.tolist()
            df.loc[df['Nom']==c,['pente']]= round(dict_param[c][1],3)
            df.loc[df['Nom']==c,['y intercept']]= round(dict_param[c][0],3)


        
    df['valeur tendance']= pd.to_numeric(df['pente'])*df['date_delta']+pd.to_numeric(df['y intercept'])
    
    fig2=px.line(df, x=df['date'], y=df['valeur tendance'], hover_name='Nom',hover_data={'Nom':False, 'pente':True}, color='Nom',line_dash='Nom', line_dash_sequence=['dot'] )
    
    

    fig_res=go.Figure(data=fig.data+fig2.data)
    fig_res.update_yaxes(title='Passages quotidiens moyens')
    fig_res.update_xaxes(title='Mois')
    fig_res.update_layout(title="Evolution de la moyenne quotidienne, par mois <br><sup>La ligne en pointillé représente une modélisation linéaire des passages observés. <br> Sa pente représente le nombre supplémentaire de cyclistes observés, en moyenne, par rapport au jour précédent.</sup>")

    
    
    return fig_res, dict_param

def get_evolution_annuelle(compteur, start=df_comptage['date'].min(), end=df_comptage['date'].max()):
    l=[compteur]
    fig, params= plot_moyennes_mensuelles(l, start, end)
    dict_res={'Nom du compteur':compteur, 'Tendance évolution journalière, sur toute la vie du compteur':round(params[compteur][1],3)}
    dff=plot_average_by(compteur, 'Année', start, end).reset_index()
    yrs=dff['Année'].tolist()
    for k in range(len(yrs)-2):
   
        yi=yrs[k]
        yf=yrs[k+1]
        vi= dff[dff['Année']==yi]['Comptage quotidien'].iloc[0]
        vf=dff[dff['Année']==yf]['Comptage quotidien'].iloc[0]

        if vi>0:
            key='Evolution '+str(int(yi))+' - '+str(int(yf))
            value=round(100*(vf-vi)/vf,2)
            value=str(value)+'%'
            dict_res[key]=value
        
    
    return dict_res
    

 # initialize app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server=app.server

# set app layout
app.layout = html.Div(children=[
    html.H1('Visualisation des passages de vélo : Métropole de Tours', style={'textAlign':'center'}),
    html.Br(),
    
    dcc.Graph(figure=plot_all_locations()),
    html.Div(id='photos', style= {'textAlign': 'center'}),
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
        options=['Evolution des comptages quotidiens sur toute la période',
                 'Evolution de la moyenne quotidienne, moyenne par mois',
                 'Evolution de la moyenne quotidienne par jour de la semaine',
                 'Evolution de la moyenne quotidienne par mois de l''année',
                 'Evolution de la moyenne quotidienne par année'],
        value='Evolution de la moyenne quotidienne, moyenne par mois',
        id='periodicite',
        style={"width": "50%", "offset":1,},
        clearable=False,
        multi=False
    ),
    dcc.DatePickerRange(
        id='date-picker',
        min_date_allowed=df_comptage['date'].min(),
        max_date_allowed=df_comptage['date'].max(),
        initial_visible_month=df_comptage['date'].min(),
        end_date=df_comptage['date'].max(), 
        start_date=df_comptage['date'].min()
    ),
    html.Br(),
    dcc.Markdown('''Vous pouvez zoomer sur la période qui vous intéresse, en la sélectionnant. Attention, les compteurs 'Pont de Fil' et 'Passerelle Ile Balzac sont des compteurs mixtes piétons + vélos !''')
    ]),
    
    dcc.Graph(id='bar'),
    html.Div(id='texte_infos_evolution'),
    dcc.Clipboard(
        target_id='texte_infos_evolution',
        title="copy",
        style={
            "display": "inline-block",
            "fontSize": 20,
            "verticalAlign": "top",
        },
    ),
    
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
    html.H3(''' Croissance annuelle''', style={'textAlign': 'center'}) ,
    html.Div(id='evol_annuelle'),
    dcc.Clipboard(
        target_id='evol_annuelle',
        title="copy",
        style={
            "display": "inline-block",
            "fontSize": 20,
            "verticalAlign": "top",
        },
    ),
    
    html.Div([
    html.H3(''' Comparaison par jour de la semaine''', style={'textAlign': 'center'}),    
    dcc.Graph(id='bar2')]),
    html.Div(
           id='table'
       ),
    dcc.Clipboard(
        target_id='table',
        title="copy",
        style={
            "display": "inline-block",
            "fontSize": 20,
            "verticalAlign": "top",
        }),
    
    
])

# callbacks
@app.callback(
    Output(component_id='bar', component_property='figure'),
    Output('table', 'children' ),
    Output('top10plus', 'figure'),
    Output('top10moins', 'figure'),
    Output('bar2', 'figure'),
    Output('texte_infos_evolution','children'),
    Output('evol_annuelle', 'children'),
    Output('photos', 'children'),
    Input('compteurs_choisis', 'value'),
    Input('periodicite', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)

def update_hist(chosen,periodicite, start, end):
    dict_period={'Evolution des comptages quotidiens sur toute la période':'date','Evolution de la moyenne quotidienne par jour de la semaine':'Jour',  'Evolution de la moyenne quotidienne par mois de l''année':'Mois', 'Evolution de la moyenne quotidienne par année': 'Année'}
    compteur_0=chosen[0]
    start=datetime.strptime(str(start), '%Y-%m-%d').date()
    end=datetime.strptime(str(end), '%Y-%m-%d').date()
    
# Photos des compteurs:
    df_filtered = df_compteurs[df_compteurs['Nom du compteur'].isin(chosen)]

    # create a list of html.Img components for each photo in the filtered DataFrame
    photo_components = []
    for index, row in df_filtered.iterrows():
        photo_components.append(
            html.Div([html.Img(src=row['photourl'], alt=row['Nom du compteur'], style={"width": '300px', 'height':'auto'}),html.P(row['Nom du compteur'])], style={"display": "inline-block", "margin": "10px"}))
 

# Creation des graphiques en barres top10 jours moins fréquentés
    fig_moins, fig_plus=get_fig_jours_plus_moins(chosen, start, end) 
    fig_moins.update_traces(width = 1/len(chosen))
    fig_plus.update_traces(width = 1/len(chosen))

    
#Graphique principal     
    if periodicite=='Evolution de la moyenne quotidienne, moyenne par mois' :
        df_evolution = df_moyenne_mensuelle(chosen[0], start, end)
        for c in chosen[1:] :
            df_temp=df_moyenne_mensuelle(c)
            df_temp['Nom']=c
            df_evolution=pd.concat([df_evolution, df_temp])
        df_evolution=df_evolution.reset_index()
    else:    
        df_evolution=plot_average_by(chosen[0], dict_period[periodicite], start, end)
        df_evolution['Nom']=chosen[0]
    
        for c in chosen[1:] :
            df_temp=plot_average_by(c, dict_period[periodicite], start, end)
            df_temp['Nom']=c
            df_evolution=pd.concat([df_evolution, df_temp])
        df_evolution=df_evolution.reset_index()
       
    if periodicite=='Evolution de la moyenne quotidienne par année':
        fig=px.bar(df_evolution, y='Comptage quotidien', x=dict_period[periodicite], color='Nom',barmode='group')
        fig.update_xaxes(title_text='Année')
        fig.update_layout(hovermode="x unified")
        fig.update_traces(width = 0.9/len(chosen))
        

    
    if periodicite == 'Evolution des comptages quotidiens sur toute la période':
        df_evolution=df_comptage.loc[(df_comptage['Nom du compteur'].isin(chosen)) & (df_comptage['date']>=start) & (df_comptage['date'] <= end)]
        df_evolution['Date']=df_evolution['date'].apply(lambda k: dict_jours[(k.weekday())]+' '+str(k.day)+' '+dict_mois[(k.month)]+' '+str(k.year))
        #df_evolution['date']=pd.to_datetime(df_evolution['date']).dt.date()
        df_evolution['jour ferié']=df_evolution['nom_jour_ferie'].notnull()
        
        df_evolution['Pattern'] = np.nan
        df_evolution.loc[(df_evolution['nom_jour_ferie'].notna()) & (df_evolution['vacances_zone_b']==True), 'Pattern'] = 'Ferié et Vacances'
        df_evolution.loc[(df_evolution['nom_jour_ferie'].notna()) & (df_evolution['vacances_zone_b']==False), 'Pattern'] = 'Ferié'
        df_evolution.loc[(df_evolution['nom_jour_ferie'].isna()) & (df_evolution['vacances_zone_b']==True), 'Pattern'] = 'Vacances'
        df_evolution.loc[(df_evolution['nom_jour_ferie'].isna()) & (df_evolution['vacances_zone_b']==False), 'Pattern'] = 'Jour quelconque'
        
        pattern_shapes = {'Ferié et Vacances': 'x','Vacances': '/','Ferié': '\\', 'Jour quelconque':''}
        
        fig=px.bar(df_evolution, x='date', y='Comptage quotidien', color='Nom du compteur', barmode='group',hover_name='Date', hover_data={'Nom du compteur': True,'Comptage quotidien':True,'date':False,'Date':False, 'jour ferié':False,'nom_jour_ferie':False},pattern_shape='Pattern', pattern_shape_map=pattern_shapes)
        fig.update_yaxes(title_text='Comptage quotidien')
        fig.update_traces(width = (1000 * 3600 * 24)/len(chosen))
        fig.update_layout(bargap=0, bargroupgap=0)
        #fig2=px.scatter( df_evolution[(df_evolution['Nom du compteur']==chosen[0]) & (df_evolution['jour ferié']==True)], x='date', y='Comptage quotidien', symbol='jour ferié', symbol_sequence=['cross'], color='jour ferié', color_discrete_sequence=['red'], hover_name='nom_jour_ferie')
        #fig=go.Figure(data=fig1.data+fig2.data)

    if periodicite =='Evolution de la moyenne quotidienne par jour de la semaine':
        fig=px.bar(df_evolution, y='Comptage quotidien', x=dict_period[periodicite], color='Nom',barmode='group')
        fig.update_xaxes(categoryorder='array', categoryarray=['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi','Samedi', 'Dimanche'])

        #fig.update_xaxes(labelalias=dict_jours)
        fig.update_xaxes(title_text='Jour')
        fig.update_layout(hovermode="x unified")


        
    if periodicite == 'Evolution de la moyenne quotidienne par mois de l''année':
       fig=px.bar(df_evolution, y='Comptage quotidien', x='Mois', color='Nom',barmode='group')
       fig.update_xaxes(categoryorder='array', categoryarray=['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'])

       fig.update_xaxes(labelalias=dict_mois)
       fig.update_xaxes(title_text='Mois')
       fig.update_layout(hovermode="x unified")

       
       
    
    if periodicite == 'Evolution de la moyenne quotidienne, moyenne par mois':
        fig, param=plot_moyennes_mensuelles(chosen, start, end)
        

        
 #creation de la visualisation par jour de la semaine      
    dff=df_infos_compteurs[df_infos_compteurs['Nom du compteur']==compteur_0][['Moyenne Lun-Ven, hors jf','Moyenne Samedi, hors jf','Moyenne Dimanche, hors jf','Moyenne quotidienne', 'Moyenne jours feriés', 'Moyenne vacances']].transpose().reset_index()
    dff.columns = ['Donnée', 'Passages']
    dff['Nom']=compteur_0
    for c in chosen[1:] :
        df_temp=df_infos_compteurs[df_infos_compteurs['Nom du compteur']==c][['Moyenne Lun-Ven, hors jf','Moyenne Samedi, hors jf','Moyenne Dimanche, hors jf','Moyenne quotidienne', 'Moyenne jours feriés', 'Moyenne vacances']].transpose().reset_index()
        df_temp.columns=['Donnée', 'Passages']
        df_temp['Nom']=c
        dff=pd.concat([dff, df_temp])
    
    fig_compteur=px.bar(dff, x='Donnée', y='Passages', color='Nom', barmode='group')    
    
    # Tableau evolution annuelle
    #dict_evo_an=[get_evolution_annuelle(c) for c in chosen]
    
    return(fig, 
           dash_table.DataTable(data=df_info_tr[chosen].reset_index().to_dict('records'),css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
    style_cell={
        'width': '{}%'.format(len(df.columns)),
        'textOverflow': 'ellipsis',
        'overflow': 'hidden' }),
        fig_plus,
        fig_moins,
        fig_compteur,
        dash_table.DataTable(data=([get_evolution(c) for c in chosen]),style_data={
        'whiteSpace': 'normal',
        'height': 'auto',
        }),
        dash_table.DataTable(data=[get_evolution_annuelle(c) for c in chosen],style_data={
        'whiteSpace': 'normal',
        'height': 'auto'}),
        photo_components)


if __name__ == "__main__":
    app.run_server(debug=False)     



    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    