#%%%
import streamlit as st
import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt


@st.cache_data
def load_csv(filepath):
    return pd.read_csv(filepath, sep=";")

@st.cache_data
def load_excel(filepath, sheet_name):
    return pd.read_excel(filepath, sheet_name=sheet_name)
################   READ FILE
code="sitex"
sitex2_occ_block=load_csv('tables/brat_releve.csv')
sp_miss_tot=load_csv('tables/sp_miss_tot_db'+code+'.csv')
diff_occ_fin=load_csv('tables/diff_releve_db'+code+'.csv')

# Transform string column into a list columnt
diff_occ_fin["miss_nomen_db"]=diff_occ_fin["miss_nomen_db"].apply(lambda x: ast.literal_eval(x))
diff_occ_fin["nomen_brat"]=diff_occ_fin["nomen_brat"].apply(lambda x: ast.literal_eval(x))
diff_occ_fin["nomen_db"]=diff_occ_fin["nomen_db"].apply(lambda x: ast.literal_eval(x))


st.write("SITEX2.0 - Comparaison BD et relevé du BRAT")
categ=st.radio("Quelle catégorie voulez-vous voir ?",
               ["Logement", "Hôtel", "Bureau","Industrie","Commerce","Ecole","Soin",
                "Culte","Transport","Ambassade","Aide à la pop","Divertissement",
                "Energie","Sport"])
column_txt=st.radio("Voulez voir le manque de notre DB selon :",
               ["Le nombre d'occupation", "La superficie plancher" ])


if categ == "Logement":
    nomen="01"
elif categ=="Hôtel":
    nomen="02"
elif categ=="Bureau":
    nomen="03"
elif categ=="Industrie":
    nomen="04"
elif categ=="Commerce":
    nomen="05"
elif categ=="Ecole":
    nomen="06"
elif categ=="Soin":
    nomen="07"
elif categ=="Culte":
    nomen="08"
elif categ=="Transport":
    nomen="09"
elif categ=="Ambassade":
    nomen="10"
elif categ=="Aide à la pop":
    nomen="11"
elif categ=="Divertissement":
    nomen="13"
elif categ=="Energie":
    nomen="14"
elif categ=="Sport":
    nomen="16"
if column_txt=="Le nombre d'occupation":
    column="count"
elif column_txt=="La superficie plancher":
    column="sum_area"


# Date de notre DB 
datum="2024_10_23"
#### Si on veut nomenclature sitex ou pras
code="sitex"
# Si on veut enlever burea acc = False
bur_acc=True

### Fonction pour grouper selon le niveau 2 pour au final sommer le nbre d'occupation et la superficie
def assign_group(code):
    niv1 = code[:2]  # Extraire le niveau 1
    # Boucler sur tous les sous-niveaux possibles
    for i in range(0, 51):  # Inclut 0 à 50
        suffix = f".{i:02}"  # Format des suffixes, ex : '.00', '.01', ..., '.50'
        if code.startswith(niv1 + suffix):
            return niv1 + suffix +".00.00"
    return "others"  # Si aucune correspondance

#### 
# Toutes les occup faites par le BRAT    
resultat = sitex2_occ_block.groupby("occupcode_").agg(
        count_all=("occupcode_", "size"),   # Compter les occurrences
        sum_area_all=("area", "sum")  # Somme des valeurs dans la colonne 'area'
    ).reset_index()   

sitex2_dico_affect = load_excel('tables/Traduction_nomenclature_SitEx_PRAS.xlsx',sheet_name=1)
code_sitex2=sitex2_dico_affect[["CODE","IntituleFr"]]

miss=diff_occ_fin[diff_occ_fin['miss_nomen_db'].apply(lambda x: nomen in x)]

# Ligne du BRAT avec les bat où il nous manque
bat_miss=sitex2_occ_block[sitex2_occ_block["id_bat"].isin(miss["id_bat"])] 
# Ne prendre que les lignes avec l'occup voulue
bat_miss_occup=bat_miss[bat_miss["occupcode_"].str.startswith(nomen)] 

# Grouper par la colonne 'occup' et compter les occurrences
resultat_miss = bat_miss_occup.groupby("occupcode_").agg(
    count=("occupcode_", "size"),   # Compter les occurrences
    sum_area=("area", "sum")  # Somme des valeurs dans la colonne 'area'
).reset_index()
#Merge avec all occup from BRAT
resultat_all=pd.merge(resultat_miss,resultat,on="occupcode_",how='left')

# Ajouter une colonne pour les groupes de niveau 2
resultat_all['group'] = resultat_all['occupcode_'].apply(assign_group)

# Grouper par la colonne 'group' et sommer les valeurs
grouped_df = resultat_all.groupby('group', as_index=False).agg(
    count=('count', 'sum'),
    sum_area=("sum_area",'sum'),
    count_all=('count_all', 'sum'),
    sum_area_all=("sum_area_all",'sum')).reset_index()
# Trouver le label de chaque catégorie
grouped_df=pd.merge(grouped_df,code_sitex2,left_on="group",right_on="CODE",how="left")
############## PLOT

label=grouped_df["IntituleFr"].str[:20]
if column=="sum_area":
    name="sp_"
    text="m²\n relevés par le BRAT"
else:
    name=""
    text="\noccupations"

# Étape 1 : Calculer les totaux des occurrences pour chaque catégorie
category_total_brat = grouped_df[column+"_all"]
# ce qu'il nous manque dans la DB
category_total_db = grouped_df[column]

# Vérifier que les tailles sont non négatives
sizes_brat = np.maximum(category_total_brat.values, 0)
sizes_db = np.minimum(np.maximum(category_total_db.values, 0), sizes_brat)

# Label pour chaque catégorie
labels = grouped_df["group"]

# Calculer les angles pour les secteurs du diagramme
angles = np.cumsum(sizes_brat) / np.sum(sizes_brat) * 360  # Angles cumulés
angles = np.concatenate(([0], angles))  # Inclure 0 pour l'angle de départ
from matplotlib.patches import Wedge

# Création du graphique
fig, ax = plt.subplots(figsize=(8, 8))

# Dessiner les secteurs principaux (BRAT)
wedges, texts, autotexts = plt.pie(
    sizes_brat, 
    labels=labels, 
    autopct='%1.1f%%', 
    startangle=90, 
    pctdistance=0.85, 
    wedgeprops={'edgecolor': 'black'},
    textprops={'color': 'black', 'fontsize': 10}
)

# Personnaliser les autotextes (pourcentages au centre)
for autotext in autotexts:
    autotext.set_fontsize(12)
    autotext.set_fontweight('bold')

# Ajouter le total d'occupations au centre
total_lines = category_total_brat.sum()
plt.text(
    0, 0, f'{int(total_lines)}'+text,
    horizontalalignment='center', verticalalignment='center', fontsize=14, fontweight='bold'
)
# Dessiner les superpositions hachurées pour DB
for i, (size_brat, size_db) in enumerate(zip(sizes_brat, sizes_db)):
    if size_db > 0:
        # Calcul des angles pour chaque superposition
        theta1 = 90 + angles[i]
        theta2 = 90 + angles[i] + (size_db / size_brat) * (angles[i + 1] - angles[i])
        
        # Ajouter la superposition hachurée
        wedge = Wedge(
            center=(0, 0),
            r=1,  # Rayon externe
            theta1=theta1,
            theta2=theta2,
            facecolor='none', 
            edgecolor='black',
            linewidth=1,
            hatch='//',
            alpha=0.5
        )
        plt.gca().add_patch(wedge)

# Ajouter un cercle blanc pour l'effet "donut"
centre_circle = plt.Circle((0, 0), 0.65, fc='white')
plt.gca().add_artist(centre_circle)

# Supprimer les axes
plt.axis('off')

# Ajouter un titre
plt.title("Répartition des " + nomen+" p/r au BRAT", fontsize=18)

# Ajouter une légende en dehors du graphique
plt.legend(
    wedges, label, 
    title="Légende", 
    loc="center left", 
    bbox_to_anchor=(1.05, 0.5),  # Légende positionnée à droite, centrée verticalement
    fontsize=10
)
# Ajuster l'apparence
plt.tight_layout()
# Afficher le graphique dans Streamlit
st.pyplot(fig)
