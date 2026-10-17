# POC pédagogique : Ontologie OWL 2 et SHACL en Médiathèque

Ce projet local d'apprentissage explique pas à pas comment modéliser un domaine familier (la gestion des prêts et abonnés d'une médiathèque) avec une **ontologie OWL 2**, valider la cohérence intrinsèque du modèle (**T-Box**), valider l'intégrité des données réelles avec **SHACL Core** (**A-Box**), et déduire automatiquement de nouveaux faits avec les règles **SHACL-AF**.

Il est conçu pour débuter : **aucune connaissance préalable en ontologie, RDF ou graphes de connaissances n'est requise**.

---

## Ce que vous allez apprendre

- **Comprendre la frontière T-Box (Modèle) vs A-Box (Données)** :
  - **T-Box (Terminological Box)** : le vocabulaire, les classes, les hiérarchies et les axiomes logiques. Savoir comment vérifier qu'une modification du schéma n'introduit ni classe insatisfiable ni cycle d'héritage.
  - **A-Box (Assertional Box)** : les faits réels, les individus et les transactions d'emprunt. Savoir comment valider leur conformité stricte avec SHACL.
- **Distinguer l'Œuvre du support matériel** : comprendre pourquoi une ontologie sépare le concept abstrait d'un livre (`Document` / `Livre`) de son exemplaire physique étiqueté en rayon (`ExemplairePhysique`).
- **Manipuler les axiomes sémantiques OWL 2** :
  - la spécialisation de classes (`rdfs:subClassOf`) et les disjonctions (`owl:disjointWith`) ;
  - les relations symétriques (`owl:SymmetricProperty`) et transitives (`owl:TransitiveProperty`) ;
  - les relations miroirs (`owl:inverseOf`) et les contraintes fonctionnelles (`owl:FunctionalProperty`) ;
  - les clés uniques d'identification métier (`owl:hasKey`).
- **Valider des données avec SHACL Core** :
  - expressions régulières sur formats normalisés (format international ISBN-13 avec `sh:pattern`) ;
  - contraintes temporelles relationnelles (date d'emprunt antérieure au retour avec `sh:lessThan`) ;
  - gestion du monde fermé sur les profils usagers (`sh:closed true`) ;
  - disjonction des rôles appliquée aux données réelles (`sh:not`).
- **Calculer des faits avec SHACL-AF** :
  - déduire automatiquement le statut d'un prêt (`« en règle »`, `« à relancer »`, `« critique »`) et le montant exact des pénalités financières de retard.

---

## Prérequis et environnement

- **Python 3.11** ;
- Aucun service externe, aucun serveur web, aucune base de données ni conteneur Docker pour la partie socle CLI ;
- **Aucune JVM / Java / Maven** : conformément aux objectifs pédagogiques actuels, ce projet n'implémente pas SWRL à ce stade.

---

## Installer et lancer (Partie 1 : Socle CLI)

Depuis la racine du projet :

```bash
# 1. Créer et activer l'environnement virtuel
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements-dev.txt

# 3. Lancer la suite de tests automatisés (27 tests)
pytest

# 4. Exécuter la démonstration pédagogique
python -m library_owl_shacl_poc
```

### Exemple de sortie console attendue :

```text
============================================================================
Démonstration Pédagogique : Ontologie OWL 2 et Règles SHACL en Médiathèque
============================================================================
Un triplet RDF se lit : Sujet (Exemplaire/Emprunt) — Prédicat (Propriété) — Objet (Valeur).

┌──────────────────────────────────────────────────────────────────────────┐
│ 1. VALIDATION DE LA T-BOX (Modèle conceptuel & Vocabulaire)             │
└──────────────────────────────────────────────────────────────────────────┘
Objectif : vérifier que le schéma de l'ontologie est intrinsèquement sain.
- Détection des classes insatisfiables (conflits d'héritage entre classes disjointes)
- Détection des cycles d'héritage illégaux (boucles subClassOf)
- Contrôle qualité de la documentation (présence des rdfs:label et rdfs:comment)

  -> Résultat T-Box : MODÈLE COHÉRENT ET VALIDE
     11 classes OWL, 9 relations d'objets, 10 propriétés de données.
     Aucun conflit logique ni cycle détecté.

┌──────────────────────────────────────────────────────────────────────────┐
│ 2. VALIDATION DE LA A-BOX (Faits réels & Données d'instances)           │
└──────────────────────────────────────────────────────────────────────────┘
Objectif : vérifier que les données concrètes respectent les contrats SHACL.
- Validation syntaxique (format regex ISBN-13 sur les livres)
- Intégrité temporelle (dateEmprunt antérieure à dateRetourPrevue)
- Monde fermé sur les usagers (rejet des propriétés inconnues sur les abonnés)
- Disjonction des rôles (un usager abonné ne peut être déclaré auteur)

  -> Résultat A-Box : DONNÉES 100% CONFORMES (toutes les formes SHACL sont satisfaites).

┌──────────────────────────────────────────────────────────────────────────┐
│ 3. INFÉRENCE PAR RÈGLES SHACL-AF (Enrichissement du graphe)             │
└──────────────────────────────────────────────────────────────────────────┘
Objectif : calculer dynamiquement le statut et les pénalités sans code métier.
   Règle 1 : retard = 0 jour  -> statut « en règle », pénalité 0.00 €.
   Règle 2 : 0 < retard < 7 j -> statut « à relancer », pénalité 0.50 € / jour.
   Règle 3 : retard >= 7 j    -> statut « critique », pénalité 0.50 € / jour.

[emprunt_alice] Alice Dupont (Astérix le Gaulois) :
  retard=0 jour(s) -> Statut: en règle | Pénalité: 0.0 €
  triplet inféré: sujet=emprunt_alice ; prédicat=statutEmprunt ; objet="en règle"@fr
  triplet inféré: sujet=emprunt_alice ; prédicat=penaliteEuros ; objet="0.0"^^xsd:decimal
[emprunt_bob] Bob Martin (Web Sémantique et Ontologies) :
  retard=3 jour(s) -> Statut: à relancer | Pénalité: 1.50 €
  triplet inféré: sujet=emprunt_bob ; prédicat=statutEmprunt ; objet="à relancer"@fr
  triplet inféré: sujet=emprunt_bob ; prédicat=penaliteEuros ; objet="1.50"^^xsd:decimal
[emprunt_claire] Claire Bernard (Web Sémantique et Ontologies) :
  retard=10 jour(s) -> Statut: critique | Pénalité: 5.00 €
  triplet inféré: sujet=emprunt_claire ; prédicat=statutEmprunt ; objet="critique"@fr
  triplet inféré: sujet=emprunt_claire ; prédicat=penaliteEuros ; objet="5.00"^^xsd:decimal

Graphe enrichi enregistré: artifacts/library-result.ttl
Diagramme Mermaid enregistré: artifacts/ontology.mmd
Visualisation interactive HTML enregistrée: artifacts/ontology-graph.html
============================================================================
```

---

## Visualisation graphique de l'ontologie

Le projet génère automatiquement deux visualisations complémentaires sans aucune dépendance serveur :

1. **Diagramme statique Mermaid (`artifacts/ontology.mmd`)** :  
   Affichable nativement dans GitHub et dans les lecteurs Markdown :

   ```mermaid
   classDiagram
       direction LR
       class Document {
           +string titre
       }
       class Livre {
           +string isbn
       }
       class ExemplairePhysique {
           +string codeBarres
       }
       class Abonne {
           +string email
           +string nom
       }
       class Emprunt {
           +date dateEmprunt
           +date dateRetourPrevue
           +integer joursRetard
           +decimal penaliteEuros
           +langString statutEmprunt
       }
       Document <|-- Livre : subClassOf
       Livre <|-- BandeDessinee : subClassOf
       ExemplairePhysique --> Document : exemplaireDe
       Emprunt --> ExemplairePhysique : concerneExemplaire
       Emprunt --> Abonne : empruntePar
   ```

2. **Visualisation interactive autonome HTML (`artifacts/ontology-graph.html`)** :  
   - S'ouvre par simple double-clic dans n'importe quel navigateur web moderne (zéro serveur).
   - Moteur physique dynamique avec zoom et déplacement de nœuds.
   - Filtres interactifs par bouton : vue globale, vue Vocabulaire (**T-Box**), vue Faits (**A-Box**), ou vue Emprunts seuls.
   - Panneau latéral détaillant chaque nœud au clic (propriétés, descriptions en français, statuts et pénalités calculées).

---

## Partie 2 : Application Fullstack PostgreSQL & SHACL (`app/`)

Une seconde partie isolée dans le répertoire [`app/`](app/) propose une application web complète (FastAPI + Jinja2/Tailwind + PostgreSQL) conteneurisée avec Docker :
- **Persistance A-Box dans PostgreSQL** : tables relationnelles dédiées (`livres`, `abonnes`, `emprunts`) avec projection dynamique vers RDF.
- **Validation SHACL Core bloquante** : toute tentative d'ajout ou modification de données non conformes (ISBN invalide, dates d'emprunt incohérentes, email usager erroné) est interceptée et bloquée par SHACL avant écriture en base.
- **Inférence SHACL-AF à la demande** : déclenchement interactif des règles sémantiques depuis l'interface avec rapport de feedback détaillé (nouveaux statuts et calcul des pénalités financières).
- **Export RDF dynamique** : inspection en direct des triplets générés depuis la base relationnelle.

### Lancer l'application avec Docker :

```bash
cd app
docker compose up --build
```

L'application est ensuite directement accessible sur [http://localhost:8000](http://localhost:8000).

---

## Guides et documentation

1. [Glossaire pédagogique](docs/glossaire.md) : tous les termes techniques traduits en français clair avec des exemples (T-Box, A-Box, cohérence, satisfiabilité).
2. [Guide pas à pas](docs/guide-pedagogique.md) : explication détaillée du scénario, des axiomes logiques, des mécanismes pour ne rien casser lors de modifications T-Box ou ajouts A-Box.
3. [Inventaire des licences](LICENSES.md) : audit des dépendances installées (aucune licence GPL/AGPL).
