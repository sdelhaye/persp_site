#%%%
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ast
#%%


def load_csv(filepath):
    return pd.read_csv(filepath, sep=";")

@st.cache_data
def load_excel(filepath, sheet_name):
    return pd.read_excel(filepath, sheet_name=sheet_name)

# Visualisation sur l'application
st.markdown(
    """
    <h1 style='text-align: center; font-size: 36px; color: black;'>
    SITEX2.0 - Comparaison BD et relevé du BRAT 
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <p style='text-align: left; font-size: 20px; color: black;'>
    Résultats des 5318 bâtiments du relevé du BRAT (ZEMU+ZIR) au niveau 1 de la nomenclature avec une comparaison de ce que notre DB retrouve ou pas
    </p>
    """,
    unsafe_allow_html=True
)

date = st.select_slider(
    "Select a date of the state of our DB",
    options=[
        "23/10/24",
        "16/12/24"
    ],
)
st.write("The date for our DB state is", date)

if date=="23/10/24":
    datum="2024_10_23"
elif date=="16/12/24":
    datum="2024_12_16"

################   READ FILE
code="sitex"
# sitex2_occ_block=load_csv('tables/brat_releve_'+datum+'.csv')
# sp_miss_tot=load_csv('tables/sp_miss_tot_db'+code+"_"+datum+'.csv')
# sp_miss_tot['nomen_miss'] = sp_miss_tot['nomen_miss'].astype(str).str.zfill(2)
# diff_occ_fin=load_csv('tables/diff_releve_db'+code+"_"+datum+'.csv')
# # Transform string column into a list columnt
# diff_occ_fin["miss_nomen_db"]=diff_occ_fin["miss_nomen_db"].apply(lambda x: ast.literal_eval(x))
# diff_occ_fin["nomen_brat"]=diff_occ_fin["nomen_brat"].apply(lambda x: ast.literal_eval(x))
# diff_occ_fin["nomen_db"]=diff_occ_fin["nomen_db"].apply(lambda x: ast.literal_eval(x))

database=load_csv('tables/occup_db_releve.csv')
releve=load_csv('tables/brat_releve.csv')
sitex2_occ_block=releve
if code =="sitex":
    colname="nomen"
elif code=="pras":
    colname="regroupement_fill"
#Voir chaque bâtiment présent et comparer les résultats au n niveau de nomenclature
niveau=1
# Mise en niveau nomenclature, si NaN => laisse le NaN
database["nomen"] = database["nomenclature"].apply(lambda x: x[:2 + 3 * (niveau - 1)] if not pd.isna(x) else np.nan)
releve["nomen"] = releve["occupcode_id"].apply(lambda x: x[:2 + 3 * (niveau - 1)] if not pd.isna(x) else np.nan)

# Liste pour stocker les résultats
resultats = []
sp_miss_tot = pd.DataFrame(columns=["id_bat", "nomen_miss", "miss_area"])

for id_batiment in np.unique(releve["id_bat"]):
    occup_db=database[database["id_bat"]==id_batiment]
    occup_brat=releve[releve["id_bat"]==id_batiment]

    # Filtrer les valeurs "15"==Activité inconnue dans occup_brat
    occup_brat = occup_brat[occup_brat["nomen"] != "15"]    
    
    nomen_db=set(occup_db[colname].dropna().unique())
    nomen_brat=set(occup_brat[colname].dropna().unique())

    # Trouver les valeurs manquantes dans la DB (présentes dans BRAT mais pas dans DB)
    nomenclatures_manquantes_db = nomen_brat - nomen_db

    # Trouver les valeurs manquantes dans BRAT (présentes dans DB mais pas dans BRAT)
    nomenclatures_manquantes_brat = nomen_db - nomen_brat
    # Ajoute les date de la DB
    date_in=occup_db["date_insert"]
    # Nomenclature différente max
    max_nomenclatures_diff = max(len(nomen_db), len(nomen_brat))
    area_miss_tot=0
    for nomen_miss in nomenclatures_manquantes_db:  
        area_miss=np.sum(occup_brat[occup_brat[colname]==nomen_miss]["area"])
        area_miss_tot=area_miss_tot+area_miss
        # Créer un DataFrame temporaire pour concaténer
        temp_df = pd.DataFrame({
            "id_bat": [id_batiment],
            "nomen_miss": [nomen_miss],
            "miss_area": [area_miss]
        })

        # Utiliser pd.concat() pour ajouter la nouvelle ligne à sp_miss_tot
        sp_miss_tot = pd.concat([sp_miss_tot, temp_df], ignore_index=True)
    # Stocker les résultats sous forme de dictionnaire
    resultats.append({
        'id_bat': id_batiment,
        'len_occ_brat':len(nomen_brat),
        'len_occ_db':len(nomen_db),
        'miss_db': len(nomenclatures_manquantes_db),
        'miss_brat': len(nomenclatures_manquantes_brat),
        'miss_all' : len(nomenclatures_manquantes_brat)+len(nomenclatures_manquantes_db),
        'max_nomen': max_nomenclatures_diff,  # Max de nomenclatures 
        'miss_nomen_db': list(nomenclatures_manquantes_db),  # Ajout de la liste des valeurs manquantes
        'miss_area':area_miss_tot,
        'miss_nomen_brat': list(nomenclatures_manquantes_brat),
        'nomen_brat': list(nomen_brat),
        'nomen_db': list(nomen_db),
    })

# Créer le DataFrame à partir de la liste de résultats
diff_occ_fin = pd.DataFrame(resultats)

# merge geom
# Groupement par id_bat pour obtenir une seule valeur de geometry par id_bat
# On peut utiliser `first`, `last`, ou une autre méthode d'agrégation
releve_unique = releve.groupby('id_bat', as_index=False).first()
#diff_occ_fin=pd.merge(diff_occ,releve_unique[["id_bat","geom"]],on="id_bat",how="left")



general=st.radio("Voulez-vous voir la comparaison de notre DB selon :",
               ["Le nombre d'occupation", "La superficie plancher" ])
general2=st.radio("Quel type de graphique voulez-vous voir:",
               ["Cammembert/circulaire", "Barre/histogramme" ])
general3=st.radio("Représentation des données :",
               ["BRAT uniquement", "BRAT + ce que notre DB ne trouve pas","BRAT + ce que notre DB retrouve" ])
## Graphique de base 
legend=["Logement","Hôtel","Bureau","Act. productives","Commerce","Ecole","Soin","Culte",
       "Transport","Ambassade","Aide à la population","Divertissement","Energie","Sport",
       "Production immatériel"]
if general=="Le nombre d'occupation":
    # Créer un DataFrame vide pour stocker les résultats cumulés
    category_pivot_total_brat = pd.DataFrame()
    category_pivot_total_db = pd.DataFrame()
    # Boucle sur les bâtiment avecs de 1 à max occupations diff
    for number in range(1, max(diff_occ_fin["len_occ_brat"])+1):  
        
        # Filtrer les lignes où miss_db == number
        df_filtered = diff_occ_fin[diff_occ_fin["len_occ_brat"] == number]
        
        # Exploser les listes dans 'nomen_brat' pour chaque occupation
        df_exploded = df_filtered.explode("nomen_brat")
        df_exploded_db = df_filtered.explode("miss_nomen_db")

        # Créer un tableau croisé dynamique pour compter les occurrences de chaque catégorie par miss_db
        category_pivot = pd.crosstab(df_exploded["len_occ_brat"], df_exploded["nomen_brat"])
        category_pivot_db = pd.crosstab(df_exploded_db["len_occ_brat"], df_exploded_db["miss_nomen_db"])
        
        # Ajouter les résultats de chaque catégorie à notre DataFrame total
        category_pivot_total_brat = pd.concat([category_pivot_total_brat, category_pivot], axis=0)
        category_pivot_total_db = pd.concat([category_pivot_total_db, category_pivot_db], axis=0)

    # Remplir les valeurs manquantes (NaN) avec des zéros
    category_pivot_total_brat = category_pivot_total_brat.fillna(0) # Contient le nbre d'occup du brat par bâtiment selon le nbre d'occupation différente
    category_pivot_total_db = category_pivot_total_db.fillna(0) # Contient le nbre d'occup manquantes de notre db par bâtiment selon le nbre d'occupation différente


    if code=="sitex":
        # Définir les couleurs pour les catégories
        color_dict = {
            "01": "#FEAB4E",    "02": "#FE7E7C",    "03": "#80A0D3",    "04": "#6C61AE",
            "05": "#E6A0C8",    "06": "#58C9D7",    "07": "#FF6961",    "08": "#FFD700",
            "09": "#00FF00",    "10": "#FFB6C1",    "11": "#FF6347",    "12": "#8A2BE2",
            "13": "#4682B4",    "14": "#9ACD32",    "16": "#6B8E23",    "20": "#B22222"}  

    elif code=="pras":
        color_dict = {
            "logement": "#FEAB4E",
            "hôtel": "#FE7E7C",
            "bureau": "#80A0D3",
            "commerce": "#E6A0C8",
            "industrie": "#6C61AE",
            "équipements": "#58C9D7",
        }    
        # Nouvel ordre des colonnes
        new_order = ["logement", "hôtel", "bureau", "industrie", "commerce", "équipements"]

        # Réorganiser les colonnes
        category_pivot_total_brat = category_pivot_total_brat[new_order]
        category_pivot_total_db = category_pivot_total_db[new_order]


    if general2=="Barre/histogramme":
        category_pivot_total_brat2=category_pivot_total_brat
        category_pivot_total_db2=category_pivot_total_db

        # Pour avoir l'échelle renseigné en terme de nomre de bâtiment et non d'occupations
        for j in range(2,max(diff_occ_fin["len_occ_brat"])+1):
            category_pivot_total_brat2.loc[j]=category_pivot_total_brat2.loc[j]/j
            category_pivot_total_db2.loc[j]=category_pivot_total_db2.loc[j]/j
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax = plt.gca()

        for i, col in enumerate(category_pivot_total_brat2.columns):
            # Plot des barres empilées
            ax.bar(
                category_pivot_total_brat2.index,  # x
                category_pivot_total_brat2[col],  # y
                bottom=category_pivot_total_brat2.loc[:, :col].cumsum(axis=1).shift(1, axis=1).fillna(0)[col],  # Position empilée
                color=color_dict[col],  # Couleur
                label=legend[i]  # Légende
            )
            if general3=="BRAT + ce que notre DB ne trouve pas":
                # Superposition des hachures pour `category_pivot_total_db`
                ax.bar(
                    category_pivot_total_brat2.index,  # x
                    category_pivot_total_db2[col],  # y
                    bottom=(category_pivot_total_brat2.loc[:, :col].cumsum(axis=1).shift(1, axis=1).fillna(0)[col]
                        + category_pivot_total_brat2[col] - category_pivot_total_db2[col]),  # Position : sommet de la barre initiale
                    facecolor="none",  # Pas de remplissage
                    edgecolor="black",  # Couleur des hachures
                    hatch="//"  # Style des hachures
                )
            elif general3=="BRAT + ce que notre DB retrouve":
                ax.bar(
                    category_pivot_total_brat2.index,  # x
                    category_pivot_total_brat[col]-category_pivot_total_db2[col],  # y
                    bottom=(category_pivot_total_brat2.loc[:, :col].cumsum(axis=1).shift(1, axis=1).fillna(0)[col]),  # Position : sommet des barres empilées
                    facecolor="none",  # Pas de remplissage
                    edgecolor="black",  # Couleur des hachures
                    hatch="o"  # Nouveau style de hachures
                )
        # Ajouter des labels et un titre
        plt.xlabel("Nombre d'occupations différentes", fontsize=12)
        plt.ylabel("Nombre de bâtiments", fontsize=12)

        plt.title('Relevé du BRAT', fontsize=14)

        # Ajouter une légende
        ax.legend(title="Catégories", bbox_to_anchor=(1.05, 1), loc="upper left")
        # Ajuster la présentation
        plt.tight_layout()   
        st.pyplot(fig)
    elif general2=="Cammembert/circulaire":
        
        # Étape 1 : Calculer les totaux des occurrences pour chaque catégorie
        category_total_brat = category_pivot_total_brat.sum()
        # ce qu'il nous manque dans la DB
        category_total_db = category_pivot_total_db.sum()

        # Vérifier que les tailles sont non négatives
        sizes_brat = category_total_brat.values
        sizes_db = category_total_db.values

        # Couleurs pour chaque catégorie
        labels = category_total_brat.index
        colors = [color_dict.get(cat, '#dddddd') for cat in labels]
        total = sum(sizes_brat)
        percentages = [f"{label} ({size / total * 100:.1f}%)" for label, size in zip(legend, sizes_brat)]

        # Calculer les angles pour les secteurs du diagramme
        angles = np.cumsum(sizes_brat) / np.sum(sizes_brat) * 360  # Angles cumulés
        angles = np.concatenate(([0], angles))  # Inclure 0 pour l'angle de départ
        from matplotlib.patches import Wedge

        # Créer le graphique
        fig, ax = plt.subplots(figsize=(8, 8))

        # Créer le pie chart initial avec les pourcentages
        wedges, texts, autotexts = plt.pie(
            sizes_brat, 
            labels=labels, 
            autopct='%1.1f%%',  # Pourcentages avec une décimale
            colors=colors,  # Couleurs pour chaque catégorie
            startangle=90, 
            pctdistance=0.85,  # Position des pourcentages par rapport au centre
            wedgeprops={'edgecolor': 'black'},  # Bordure noire pour chaque secteur
            textprops={'color': 'black', 'fontsize': 10}  # Couleur et taille du texte des labels
        )

        # Personnaliser les autotextes (les pourcentages) pour qu'ils apparaissent au centre
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        # Ajouter un cercle blanc au centre pour donner un effet de "donut"
        centre_circle = plt.Circle((0, 0), 0.65, fc='white')
        plt.gca().add_artist(centre_circle)

        # Ajouter le nombre total d'occupations au centre
        total_lines = category_total_brat.sum()
        plt.text(
            0, 0, f'{int(total_lines)}\noccupations',
            horizontalalignment='center', verticalalignment='center', fontsize=16, fontweight='bold'
        )
        if general3!="BRAT uniquement":
            # Dessiner la superposition hachurée pour `category_total_db`
            for i, (label, size_brat, size_db, color) in enumerate(zip(labels, sizes_brat, sizes_db, colors)):
                # Angles pour le secteur principal
                theta1 = 90+ angles[i]
                theta2 = 90+ angles[i + 1]
                
                # Dessiner la superposition plus sombre pour `category_total_db` avec des hachures
                fraction = size_db / size_brat if size_brat > 0 else 0  # Fraction pour `category_total_db`
                if fraction > 0:
                    theta_mid = theta1 + fraction * (theta2 - theta1)  # Angle intermédiaire pour la superposition
                    if general3=="BRAT + ce que notre DB ne trouve pas":
                        plt.gca().add_patch(
                            Wedge(
                                center=(0, 0), r=1, theta1=theta1, theta2=theta_mid,
                                facecolor=color, edgecolor='black', linewidth=1, alpha=0.6, 
                                hatch='//'  # Application des hachures sur la zone superposée
                            )
                        )
                    elif general3=="BRAT + ce que notre DB retrouve":
                        plt.gca().add_patch(
                            Wedge(
                                center=(0, 0), r=1, theta1=theta_mid, theta2=theta2,
                                facecolor=color, edgecolor='black', linewidth=1, alpha=0.6, 
                                hatch='o'  # Application des hachures sur la zone superposée
                            )
                        )        
        # Ajouter un cercle blanc au centre pour donner un effet de "donut"
        centre_circle = plt.Circle((0, 0), 0.65, fc='white')
        plt.gca().add_artist(centre_circle)
        # Ajouter une légende en dehors du graphique
        plt.legend(
            wedges, percentages, 
            title="Légende", 
            loc="center left", 
            bbox_to_anchor=(1.05, 0.5),  # Légende positionnée à droite, centrée verticalement
            fontsize=10
        )   
        # Supprimer les axes x et y
        plt.axis('off')

        plt.title("Relevé du BRAT", fontsize=18)

        # Ajuster l'apparence
        plt.tight_layout()
        st.pyplot(fig)
elif general=="La superficie plancher":
    # Couleurs pour chaque catégorie
    if code=="sitex":
        # Définir les couleurs pour les catégories
        color_dict = {
            "01": "#FEAB4E",    "02": "#FE7E7C",    "03": "#80A0D3",    "04": "#6C61AE",
            "05": "#E6A0C8",    "06": "#58C9D7",    "07": "#FF6961",    "08": "#FFD700",
            "09": "#00FF00",    "10": "#FFB6C1",    "11": "#FF6347",    "12": "#8A2BE2",
            "13": "#4682B4",    "14": "#9ACD32",    "16": "#6B8E23",    "20": "#B22222"}  
 
    elif code=="pras":
        color_dict = {
            "logement": "#FEAB4E",
            "hôtel": "#FE7E7C",
            "bureau": "#80A0D3",
            "commerce": "#E6A0C8",
            "industrie": "#6C61AE",
            "équipements": "#58C9D7",
        }    
    data = sitex2_occ_block
    if code=="pras":
        data=data[data["regroupement_fill"].isna()==False]
        colname="regroupement_fill"
    else:
        colname="nomen"
    
    data=data[~data['occupcode_id'].str.startswith('15')]
    niveau=1
    data["nomen"]=data["occupcode_id"].apply(lambda x: x[:2 + 3 * (niveau - 1)] if not pd.isna(x) else np.nan)

    # Groupement par la colonne "nomen" et somme des valeurs de la colonne "area"
    result = data.groupby(colname)["area"].sum().reset_index()

    # Ce qu'il nous manque en superficie plancher par categérie
    miss_sp = sp_miss_tot.groupby("nomen_miss")["miss_area"].sum().reset_index()
    # Jointure 
    result_df=pd.merge(result,miss_sp,left_on=colname,right_on="nomen_miss")
    result_df["diff_area (%)"]=result_df["miss_area"]/result_df["area"]*100

    if general2=="Barre/histogramme":
        # Liste pour stocker les résultats
        results = []
        results_all=[]

        for number in range(1, max(diff_occ_fin["len_occ_brat"]) + 1):  
            # Filtrer les lignes où len_occ_brat == number
            df_filtered = diff_occ_fin[diff_occ_fin["len_occ_brat"] == number]

            # Obtenir tous les id_bat concernés
            relevant_ids = df_filtered["id_bat"].unique()

            # Filtrer les données correspondantes dans `data`
            bat = data[data["id_bat"].isin(relevant_ids)]

            # Grouper par nomen et id_bat pour calculer les sommes
            batgroup = bat.groupby(["id_bat", "nomen"]).agg(
                sum_area=("area", "sum")
            ).reset_index()

            # Récupérer les miss_nomen_db pour chaque id_bat
            miss_nomen_map = df_filtered.set_index("id_bat")["miss_nomen_db"].explode()

            # Filtrer pour ne garder que les nomen manquants
            batgroup["is_missing"] = batgroup.apply(
                lambda row: row["nomen"] in miss_nomen_map[miss_nomen_map.index == row["id_bat"]].values, axis=1
            )
            batgroup_miss = batgroup[batgroup["is_missing"]]

            # Grouper par nomen pour obtenir les sommes globales
            batmiss_final = batgroup_miss.groupby("nomen").agg(
                total_area=("sum_area", "sum")
            )
            batall_final=batgroup.groupby("nomen").agg(
                total_area=("sum_area", "sum")
            )

            # Ajouter une colonne pour identifier le numéro
            batmiss_final["number"] = number
            batall_final["number"] = number

            # Ajouter le résultat au tableau global
            results.append(batmiss_final)
            results_all.append(batall_final)

        # Concaténer tous les résultats
        final_df = pd.concat(results)
        final_all_df=pd.concat(results_all)

        # Créer le tableau croisé
        pivot_table = final_df.pivot_table(
            index=final_df.index,  # Catégories (indices de batmiss_final)
            columns="number",      # Les différents numbers
            values="total_area",   # Les valeurs de total_area
            aggfunc="sum",         # Fonction d'agrégation
            fill_value=0           # Remplir les valeurs manquantes avec 0
        )
        pivot_table_all = final_all_df.pivot_table(
            index=final_all_df.index,  # Catégories (indices de batmiss_final)
            columns="number",      # Les différents numbers
            values="total_area",   # Les valeurs de total_area
            aggfunc="sum",         # Fonction d'agrégation
            fill_value=0           # Remplir les valeurs manquantes avec 0
        )
       # Inverser les lignes et colonnes du pivot_table
        pivot_table = pivot_table.transpose()
        pivot_table_all = pivot_table_all.transpose()
        fig, ax = plt.subplots(figsize=(8, 8))
        ax = plt.gca()

        for i, col in enumerate(pivot_table.columns):
            # Plot des barres empilées
            ax.bar(
                pivot_table_all.index,  # x
                pivot_table_all[col],  # y
                bottom=pivot_table_all.loc[:, :col].cumsum(axis=1).shift(1, axis=1).fillna(0)[col],  # Position empilée
                color=color_dict[col],  # Couleur
                label=legend[i]  # Légende
            )
            if general3=="BRAT + ce que notre DB ne trouve pas":
                # Superposition des hachures pour `category_pivot_total_db`
                ax.bar(
                    pivot_table_all.index,  # x
                    pivot_table[col],  # y
                    bottom=(pivot_table_all.loc[:, :col].cumsum(axis=1).shift(1, axis=1).fillna(0)[col]
                        + pivot_table_all[col] - pivot_table[col]),  # Position : sommet de la barre initiale
                    facecolor="none",  # Pas de remplissage
                    edgecolor="black",  # Couleur des hachures
                    hatch="//"  # Style des hachures
                )
            elif general3=="BRAT + ce que notre DB retrouve":
                ax.bar(
                    pivot_table_all.index,  # x
                    pivot_table_all[col]-pivot_table[col],  # y
                    bottom=(pivot_table_all.loc[:, :col].cumsum(axis=1).shift(1, axis=1).fillna(0)[col]),  # Position : sommet des barres empilées
                    facecolor="none",  # Pas de remplissage
                    edgecolor="black",  # Couleur des hachures
                    hatch="o"  # Nouveau style de hachures
                )
        # Ajouter des labels et un titre
        plt.xlabel("Nombre d'occupations différentes", fontsize=12)
        plt.ylabel("Superficie plancher (m²)", fontsize=12)

        plt.title('Relevé du BRAT', fontsize=14)

        # Ajouter une légende
        ax.legend(title="Catégories", bbox_to_anchor=(1.05, 1), loc="upper left")
        # Ajuster la présentation
        plt.tight_layout()   
        st.pyplot(fig)

    elif general2=="Cammembert/circulaire":
        # Étape 1 : Calculer les totaux des occurrences pour chaque catégorie
        category_total_brat = result_df["area"]
        # ce qu'il nous manque dans la DB
        category_total_db = result_df["miss_area"]

        # Vérifier que les tailles sont non négatives
        sizes_brat = np.maximum(category_total_brat.values, 0)
        sizes_db = np.minimum(np.maximum(category_total_db.values, 0), sizes_brat)

        total = sum(sizes_brat)
        percentages = [f"{label} ({size / total * 100:.1f}%)" for label, size in zip(legend, sizes_brat)]

        labels = result_df[colname]
        colors = [color_dict.get(cat, '#dddddd') for cat in result_df[colname]]

        # Calculer les angles pour les secteurs du diagramme
        angles = np.cumsum(sizes_brat) / np.sum(sizes_brat) * 360  # Angles cumulés
        angles = np.concatenate(([0], angles))  # Inclure 0 pour l'angle de départ
        from matplotlib.patches import Wedge

        # Créer le graphique
        fig, ax = plt.subplots(figsize=(8, 8))

        # Créer le pie chart initial avec les pourcentages
        wedges, texts, autotexts = plt.pie(
            sizes_brat, 
            labels=labels, 
            autopct='%1.1f%%',  # Pourcentages avec une décimale
            colors=colors,  # Couleurs pour chaque catégorie
            startangle=90, 
            pctdistance=0.85,  # Position des pourcentages par rapport au centre
            wedgeprops={'edgecolor': 'black'},  # Bordure noire pour chaque secteur
            textprops={'color': 'black', 'fontsize': 10}  # Couleur et taille du texte des labels
        )

        # Personnaliser les autotextes (les pourcentages) pour qu'ils apparaissent au centre
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        # Ajouter un cercle blanc au centre pour donner un effet de "donut"
        centre_circle = plt.Circle((0, 0), 0.65, fc='white')
        plt.gca().add_artist(centre_circle)

        # Ajouter le nombre total d'occupations au centre
        total_lines = category_total_brat.sum()
        plt.text(
            0, 0, f'{int(total_lines)} m²\n relevés par le BRAT',
            horizontalalignment='center', verticalalignment='center', fontsize=14, fontweight='bold'
        )
        if general3!="BRAT uniquement":
            # Dessiner la superposition hachurée pour `category_total_db`
            for i, (label, size_brat, size_db, color) in enumerate(zip(labels, sizes_brat, sizes_db, colors)):
                # Angles pour le secteur principal
                theta1 = 90+ angles[i]
                theta2 = 90+ angles[i + 1]
                
                # Dessiner la superposition plus sombre pour `category_total_db` avec des hachures
                fraction = size_db / size_brat if size_brat > 0 else 0  # Fraction pour `category_total_db`
                if fraction > 0:
                    theta_mid = theta1 + fraction * (theta2 - theta1)  # Angle intermédiaire pour la superposition
                    if general3=="BRAT + ce que notre DB ne trouve pas":
                        plt.gca().add_patch(
                            Wedge(
                                center=(0, 0), r=1, theta1=theta1, theta2=theta_mid,
                                facecolor=color, edgecolor='black', linewidth=1, alpha=0.6, 
                                hatch='//'  # Application des hachures sur la zone superposée
                            )
                        )
                    elif general3=="BRAT + ce que notre DB retrouve":
                        plt.gca().add_patch(
                            Wedge(
                                center=(0, 0), r=1, theta1=theta_mid, theta2=theta2,
                                facecolor=color, edgecolor='black', linewidth=1, alpha=0.6, 
                                hatch='o'  # Application des hachures sur la zone superposée
                            )
                        )                        
        # Ajouter un cercle blanc au centre pour donner un effet de "donut"
        centre_circle = plt.Circle((0, 0), 0.65, fc='white')
        plt.gca().add_artist(centre_circle)

        plt.legend(
            wedges, percentages, 
            title="Légende", 
            loc="center left", 
            bbox_to_anchor=(1.05, 0.5),  # Légende positionnée à droite, centrée verticalement
            fontsize=10
        )       

        # Supprimer les axes x et y
        plt.axis('off')

        # Ajouter un titre
        plt.title("Relevé du BRAT", fontsize=18)

        # Ajuster l'apparence
        plt.tight_layout()
        st.pyplot(fig)

st.write("Les \% montrent la part de la catégorie par rapport à toute les catégories relevées par le BRAT. Le hachuré montre la part de ce que notre DB n'arrive pas à retrouver et les cercles sont ce que notre DB arrive à retrouver")

######### Histo de ce que notre DB retrouve par catégorie en %
st.markdown(
    """
    <p style='text-align: left; font-size: 20px; color: black;'>
    Part de ce que notre DB n'arrive pas à trouver pour chaque grande catégorie
    </p>
    """,
    unsafe_allow_html=True
)
typee=st.radio("Comparaison de notre DB selon :",
               ["Le nombre d'occupation", "La superficie plancher"  ])
nomen_to_label = {"01": "Logement",    "02": "Hôtel",    "03": "Bureau",    "04": "Act. productives",
    "05": "Commerce",    "06": "Ecole",    "07": "Soin",    "08": "Culte",    "09": "Transport",
    "10": "Ambassade",    "11": "Aide à la pop",    "13": "Divertissement",    "14": "Energie",
    "16": "Sport",    "20": "Production imm"
}

niveau=1
sitex2_occ_block["nomen"]=sitex2_occ_block["occupcode_"].apply(lambda x: x[:2 + 3 * (niveau - 1)] if not pd.isna(x) else np.nan)

if code=="pras":
    data=data[data["regroupement_fill"].isna()==False]
    colname="regroupement_fill"
else:
    colname="nomen"

if typee=="Le nombre d'occupation":
    data=diff_occ_fin

    # Créer un DataFrame vide pour stocker les résultats cumulés
    category_pivot_total_brat = pd.DataFrame()
    category_pivot_total_db = pd.DataFrame()
    # Boucle sur les bâtiment avecs de 1 à max occupations diff
    for number in range(1, max(data["len_occ_brat"])+1):  
        
        # Filtrer les lignes où miss_db == number
        df_filtered = data[data["len_occ_brat"] == number]
        
        # Exploser les listes dans 'nomen_brat' pour chaque occupation
        df_exploded = df_filtered.explode("nomen_brat")
        df_exploded_db = df_filtered.explode("miss_nomen_db")

        # Créer un tableau croisé dynamique pour compter les occurrences de chaque catégorie par miss_db
        category_pivot = pd.crosstab(df_exploded["len_occ_brat"], df_exploded["nomen_brat"])
        category_pivot_db = pd.crosstab(df_exploded_db["len_occ_brat"], df_exploded_db["miss_nomen_db"])
        
        # Ajouter les résultats de chaque catégorie à notre DataFrame total
        category_pivot_total_brat = pd.concat([category_pivot_total_brat, category_pivot], axis=0)
        category_pivot_total_db = pd.concat([category_pivot_total_db, category_pivot_db], axis=0)

    # Remplir les valeurs manquantes (NaN) avec des zéros
    category_pivot_total_brat = category_pivot_total_brat.fillna(0) # Contient le nbre d'occup du brat par bâtiment selon le nbre d'occupation différente
    category_pivot_total_db = category_pivot_total_db.fillna(0) # Contient le nbre d'occup manquantes de notre db par bâtiment selon le nbre d'occupation différente

    # Étape 1 : Calculer les totaux des occurrences pour chaque catégorie
    category_total_brat = category_pivot_total_brat.sum()
    # ce qu'il nous manque dans la DB
    category_total_db = category_pivot_total_db.sum()
    category_total_miss=category_total_db/category_total_brat*100
elif typee=="La superficie plancher":
    data=sitex2_occ_block[sitex2_occ_block["nomen"]!="15"]
    # Groupement par la colonne "nomen" et somme des valeurs de la colonne "area"
    result = data.groupby(colname)["area"].sum().reset_index()


    # Ce qu'il nous manque en superficie plancher par categérie
    miss_sp = sp_miss_tot.groupby("nomen_miss")["miss_area"].sum().reset_index()
    # Jointure 
    result_df=pd.merge(result,miss_sp,left_on=colname,right_on="nomen_miss")
    result_df["diff_area (%)"]=result_df["miss_area"]/result_df["area"]*100
    category_total_miss=result_df[[colname,"diff_area (%)"]]

    category_total_miss = category_total_miss.groupby(colname)["diff_area (%)"].sum()
    
# Trier les valeurs par ordre croissant
category_total_miss_sorted = category_total_miss.sort_values()
# Génération des noms de catégorie à partir de nomen_to_label
category_labels = [nomen_to_label.get(code, f"Code inconnu ({code})") for code in category_total_miss_sorted.index]

# Créer le graphique (bar plot)
fig, ax = plt.subplots(figsize=(10, 6))

# Génération des couleurs
colors = [color_dict.get(code, '#dddddd') for code in category_total_miss_sorted.index]

# Dessin des barres
bars = ax.bar(category_labels, category_total_miss_sorted, color=colors, edgecolor='black')

# Ajouter les valeurs sur chaque barre
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height + 1, f'{height:.2f}%', 
            ha='center', fontsize=10, color='black')

# Ajouter des titres et labels
plt.title("Ce qu'il manque à notre DB", fontsize=16)

plt.ylabel('Part de '+typee+ " manquante", fontsize=14)

# Rotation des noms des catégories pour une meilleure lisibilité
plt.xticks(rotation=45, fontsize=12)
plt.tight_layout()
st.pyplot(fig)

st.write("Ces chiffres sont simplement un rapport entre ce que notre DB retrouve et le total de ce que le BRAT à trouver. Sur le diagramme circulaire, cela peut être vu par le hachuré divisé sur toute la couleur.")

############################# Par catégorie
st.markdown(
    """
    <p style='text-align: left; font-size: 20px; color: black;'>
    Résultat du relevé du BRAT au sein de chaque catégorie SITEX (niveau 2 ou 3 de la nomenclature)
    </p>
    """,
    unsafe_allow_html=True
)
st.write("Ce qu'il nous manque par catégorie Sitex")
categ=st.radio("Quelle catégorie voulez-vous voir ?",
               ["Logement", "Hôtel", "Bureau","Industrie","Commerce","Ecole","Soin",
                "Culte","Transport","Ambassade","Aide à la pop","Divertissement",
                "Energie","Sport"])
column_txt=st.radio("Voulez voir le manque de notre DB selon :",
               ["Le nombre d'occupation", "La superficie plancher" ])
niv_txt=st.radio("Précision de la nomenclature :",
               ["Niveau 2", "Niveau 3" ])
layout=st.radio("Représentation des données  :",
               ["BRAT uniquement", "BRAT + ce que notre DB ne trouve pas","BRAT + ce que notre DB retrouve" ])

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
if niv_txt=="Niveau 2":
    niv=2
elif niv_txt=="Niveau 3":
    niv=3


# Date de notre DB 
datum="2024_10_23"
#### Si on veut nomenclature sitex ou pras
code="sitex"
# Si on veut enlever burea acc = False
bur_acc=True

### Fonction pour grouper selon le niveau 2 pour au final sommer le nbre d'occupation et la superficie
def assign_group(code,niveau):
    niv1 = code[:2]  # Extraire le niveau 1
    niv2= code[3:5] # Extraire le niveau 2
    if niveau==2:
        # Boucler sur tous les sous-niveaux possibles
        for i in range(0, 51):  # Inclut 0 à 50
            suffix = f".{i:02}"  # Format des suffixes, ex : '.00', '.01', ..., '.50'
            if code.startswith(niv1 + suffix):
                return niv1 + suffix +".00.00"
        return "others"  # Si aucune correspondance
    elif niveau==3:
        for i in range(0, 21):  # Inclut 0 à 02
            suffix = f".{i:02}"  # Format des suffixes, ex : '.00', '.01', ..., '.50'
            if code.startswith(niv1 +'.'+niv2+ suffix):
                return niv1 + "."+ niv2 + suffix +".00"
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
resultat_all['group'] = resultat_all['occupcode_'].apply(lambda code: assign_group(code, niveau=niv))

# Grouper par la colonne 'group' et sommer les valeurs
grouped_df = resultat_all.groupby('group', as_index=False).agg(
    count=('count', 'sum'),
    sum_area=("sum_area",'sum'),
    count_all=('count_all', 'sum'),
    sum_area_all=("sum_area_all",'sum')).reset_index()
# Trouver le label de chaque catégorie
grouped_df=pd.merge(grouped_df,code_sitex2,left_on="group",right_on="CODE",how="left")
############## PLOT
colors = ['#95add9','#b590d9', '#d9b68c', '#71c1d9', '#d99191', '#9dd5a3', '#d9a688', '#d9add4',
        '#bbb3d9', '#b8d39c', '#d9beb3', '#88afb8', '#d9a387', '#9ac7b7', '#d9ca7d']
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
total = sum(sizes_brat)
percentages = [f"{label} ({size / total * 100:.1f}%)" for label, size in zip(label, sizes_brat)]

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
    textprops={'color': 'black', 'fontsize': 10},
    colors=colors  # Palette personnalisée
)

# Personnaliser les autotextes (pourcentages au centre)
for autotext in autotexts:
    autotext.set_fontsize(10)
    autotext.set_fontweight('bold')

# Ajouter le total d'occupations au centre
total_lines = category_total_brat.sum()
plt.text(
    0, 0, f'{int(total_lines)}'+text,
    horizontalalignment='center', verticalalignment='center', fontsize=14, fontweight='bold'
)
if layout!="BRAT uniquement":
    # Dessiner les superpositions hachurées pour DB
    for i, (size_brat, size_db) in enumerate(zip(sizes_brat, sizes_db)):
        if size_db > 0:
            # Calcul des angles pour chaque superposition
            theta1 = 90 + angles[i]
            theta2 = 90 + angles[i] + (size_db / size_brat) * (angles[i + 1] - angles[i])
            theta3= 90 + angles[i] + (angles[i + 1] - angles[i])
            if layout=="BRAT + ce que notre DB ne trouve pas":
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
            elif layout=="BRAT + ce que notre DB retrouve":
                # Ajouter la superposition hachurée
                wedge = Wedge(
                    center=(0, 0),
                    r=1,  # Rayon externe
                    theta1=theta2,
                    theta2=theta3,
                    facecolor='none', 
                    edgecolor='black',
                    linewidth=1,
                    hatch='o',
                    alpha=0.5
                )                
            plt.gca().add_patch(wedge)

# Ajouter un cercle blanc pour l'effet "donut"
centre_circle = plt.Circle((0, 0), 0.65, fc='white')
plt.gca().add_artist(centre_circle)

# Supprimer les axes
plt.axis('off')

# Ajouter un titre
plt.title("Relevé du BRAT pour la catégorie " + categ, fontsize=18)

# Ajouter une légende en dehors du graphique
plt.legend(
    wedges, percentages, 
    title="Légende", 
    loc="center left", 
    bbox_to_anchor=(1.05, 0.5),  # Légende positionnée à droite, centrée verticalement
    fontsize=10
)
# Ajuster l'apparence
plt.tight_layout()
# Afficher le graphique dans Streamlit
st.pyplot(fig)

st.write("Les \% montrent la part de la catégorie par rapport à toute les catégories relevées par le BRAT. Le hachuré montre la part de ce que notre DB n'arrive pas à retrouver et les cercles sont ce que notre DB arrive à retrouver")
