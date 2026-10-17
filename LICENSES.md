# Licences des dépendances du POC Médiathèque

Cet inventaire liste les 14 paquets Python résolus dans l'environnement virtuel local du projet (pour l'ontologie OWL 2, le parsing RDF, la validation SHACL Core et les règles SHACL-AF). 

Conformément aux choix d'architecture, **aucune dépendance SWRL / Java / Maven n'est intégrée dans ce projet à ce stade**. Aucun paquet résolu ne déclare de licence GPL ou AGPL.

## Dépendances Python

| Paquet | Version | Licence déclarée | Catégorie / Usage |
|---|---:|---|---|
| **pyshacl** | 0.40.1 | Apache-2.0 | directe runtime : moteur de validation SHACL Core et d'inférence SHACL-AF |
| **rdflib** | 7.6.0 | BSD-3-Clause | directe runtime : manipulation et sérialisation des graphes RDF |
| **owlrl** | 7.6.2 | W3C Software Notice (2015-05-13) | directe runtime : raisonneur sémantique OWL 2 RL / RDFS |
| **html5rdf** | 1.2.1 | MIT | transitive runtime : parsing RDFa/HTML5 |
| **importlib_metadata** | 9.0.1 | Apache-2.0 | transitive runtime : gestion des points d'entrée et métadonnées |
| **packaging** | 26.3 | Apache-2.0 OR BSD-2-Clause | transitive runtime : utilitaires de versionnage |
| **prettytable** | 3.18.0 | BSD-3-Clause | transitive runtime : mise en forme tabulaire |
| **pyparsing** | 3.3.3 | MIT | transitive runtime : analyseurs syntaxiques RDFLib |
| **wcwidth** | 0.9.2 | MIT | transitive runtime : calcul de largeur de caractères |
| **zipp** | 4.1.1 | MIT | transitive runtime : inspection d'archives zip |
| **pytest** | 9.1.1 | MIT | directe développement : suite de tests automatisés |
| **iniconfig** | 2.3.1 | MIT | transitive développement : lecture de la configuration pytest |
| **pluggy** | 1.7.0 | MIT | transitive développement : système de plugins pytest |
| **Pygments** | 2.21.0 | BSD-2-Clause | transitive développement : coloration syntaxique |

## Notes juridiques et conformité

1. **Permissions d'usage** : Les licences Apache-2.0, MIT, BSD-2/3-Clause et W3C accordent des droits étendus d'utilisation, de modification et d'exécution sans frais ni redevance, sous réserve de conserver les mentions de copyright et avis de licence associés.
2. **Exclusion SWRL** : Le projet n'embarque aucun JAR externe, aucun composant Maven ni runtime JVM.
3. Ce document constitue un inventaire technique et factuel, et non un conseil juridique formel.
