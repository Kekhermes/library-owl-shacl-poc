# Glossaire pédagogique : Ontologie OWL 2 et Validation SHACL

Ce glossaire accompagne le projet d'apprentissage **Médiathèque OWL 2 & SHACL**. Il est conçu pour les personnes débutant dans le Web Sémantique et les graphes de connaissances. Chaque notion technique y est définie en français accessible et illustrée par un exemple concret issu du projet.

---

## 1. Fondations RDF et syntaxe Turtle

### RDF (Resource Description Framework)
**RDF** est le standard du W3C pour représenter des informations et des connaissances sur le Web. Au lieu de ranger les données dans des tables relationnelles rigides, RDF les représente sous la forme d'un **graphe de relations**.

### Triplet RDF
L'atome de base de RDF est le **triplet**, qui se compose toujours de trois éléments : **Sujet — Prédicat — Objet**.
- **Sujet** : la ressource dont on parle (ex. : `ex:livre_asterix`).
- **Prédicat** : la relation, la propriété ou le lien (ex. : `ex:titre`).
- **Objet** : la valeur ou la ressource reliée (ex. : `"Astérix le Gaulois"`).

> ⚠️ **Attention au mot « Objet »** : En programmation orientée objet, « objet » désigne une entité logicielle. En RDF, l'« objet » désigne uniquement la **troisième position** du triplet (la cible du lien).

### Graphe RDF
Un ensemble de triplets forme un **graphe RDF**. Dans ce graphe, les nœuds sont les sujets et les objets, et les arêtes orientées sont les prédicats.

### URI / IRI (Uniform Resource Identifier)
Chaque concept ou ressource dans un graphe possède un identifiant unique universel sous forme d'URI (ex. : `https://example.org/library#Livre`).

### Turtle (.ttl)
**Turtle** (Terse RDF Triple Language) est une syntaxe textuelle compacte et lisible pour écrire des graphes RDF.
- Le préfixe (ex. : `@prefix ex: <https://example.org/library#> .`) permet d'écrire `ex:Livre` au lieu de répéter l'adresse complète.
- Le point `.` termine une affirmation (un fait).
- Le point-virgule `;` permet d'énoncer plusieurs propriétés sur le même sujet sans répéter son nom.

---

## 2. Modélisation sémantique avec OWL 2

### Ontologie
Une **ontologie** est une spécification formelle et explicite d'une conceptualisation partagée. Elle définit le « dictionnaire » et la « grammaire » logique d'un domaine : quelles catégories d'objets existent et comment elles sont reliées.

### T-Box (Terminological Box)
La **T-Box** rassemble les définitions conceptuelles, le vocabulaire et les axiomes généraux du domaine, indépendamment de toute donnée concrète :
- Les classes (`owl:Class`) et leur hiérarchie (`subClassOf`) ;
- Les relations autorisées et leurs caractéristiques (`inverseOf`, `SymmetricProperty`, `TransitiveProperty`) ;
- Les disjonctions conceptuelles (`owl:disjointWith`).
- *Fichier associé :* `rdf/ontology.ttl`.

### A-Box (Assertional Box)
La **A-Box** rassemble les faits concrets, les individus observés et les transactions du monde réel :
- Les personnes (`ex:abonne_alice`, `ex:auteur_goscinny`) ;
- Les exemplaires physiques et leurs codes-barres (`ex:exemplaire_ast_1`) ;
- Les emprunts réels datés et leurs retards (`ex:emprunt_bob`).
- *Fichier associé :* `rdf/data.ttl`.

### Cohérence sémantique (Consistency)
Une ontologie (T-Box) est dite **cohérente** s'il existe au moins un modèle mathématique possible dans lequel tous ses axiomes sont simultanément vrais, sans contradiction interne.

### Satisfiabilité d'une classe (Satisfiability)
Une classe est **satisfiable** s'il est logiquement possible pour un individu d'en faire partie. Si une classe hérite de deux classes mutuellement disjointes (ex. `LivreNumerique` et `ExemplairePhysique`), elle devient **insatisfiable** : aucun individu ne peut légalement exister dans cette catégorie sans provoquer une contradiction logique.

### Classe insatisfiable (`owl:Nothing`)
En logique OWL 2, toute classe insatisfiable est logiquement subsumée par `owl:Nothing` (l'ensemble vide). C'est le signal d'alarme absolu d'une erreur de modélisation dans la T-Box.

### Cycle d'héritage illégal
Une boucle dans les relations de sous-classes (ex. $A \sqsubseteq B \sqsubseteq C \sqsubseteq A$). En logique OWL, un tel cycle force $A$, $B$ et $C$ à être rigoureusement équivalentes, ce qui détruit la hiérarchie souhaitée et signale une erreur de conception dans la T-Box.

### Classe (`owl:Class`)
Une **classe** représente une catégorie d'entités qui partagent des caractéristiques communes. 
- *Exemple :* `ex:Document`, `ex:Livre`, `ex:Abonne`.

### Sous-classe (`rdfs:subClassOf`)
La relation de spécialisation ou d'héritage sémantique. Si $A$ est sous-classe de $B$, alors tout individu de type $A$ est automatiquement reconnu comme étant aussi de type $B$ par un raisonneur.
- *Exemple :* `ex:BandeDessinee rdfs:subClassOf ex:Livre .` (Toute BD est un livre).

### Disjonction (`owl:disjointWith`)
Axiome déclarant que deux classes sont mutuellement exclusives. Un même individu ne peut pas appartenir simultanément aux deux classes.
- *Exemple :* `ex:LivreNumerique owl:disjointWith ex:ExemplairePhysique .`

### Propriété d'Objet (`owl:ObjectProperty`)
Une propriété qui relie **deux ressources** (deux individus du graphe).
- *Exemple :* `ex:concerneExemplaire` relie un `Emprunt` à un `ExemplairePhysique`.

### Propriété de Données (`owl:DatatypeProperty`)
Une propriété qui relie un individu à une **valeur littérale simple** (un texte, un entier, une date).
- *Exemple :* `ex:joursRetard` relie un emprunt à l'entier `3` (`xsd:integer`).

### Inversion de Propriétés (`owl:inverseOf`)
Déclare que deux relations sont le reflet miroir l'une de l'autre.
- *Exemple :* `ex:aPourAuteur owl:inverseOf ex:aEcrit .` Si Asterix a pour auteur Goscinny, alors Goscinny a écrit Asterix.

### Propriété Symétrique (`owl:SymmetricProperty`)
Une relation bidirectionnelle automatique : si $A$ est relié à $B$, alors $B$ est nécessairement relié à $A$.
- *Exemple :* `ex:coAuteurAvec`. Si Goscinny est co-auteur avec Uderzo, alors Uderzo est co-auteur avec Goscinny.

### Propriété Transitive (`owl:TransitiveProperty`)
Une relation qui se propage le long d'une chaîne : si $A \rightarrow B$ et $B \rightarrow C$, alors $A \rightarrow C$.
- *Exemple :* `ex:themeParent`. Si *Sciences* est parent d'*Informatique*, et *Informatique* est parent d'*Ontologies*, alors *Sciences* est parent d'*Ontologies*.

### Propriété Fonctionnelle (`owl:FunctionalProperty`)
Indique qu'un individu ne peut avoir au plus **qu'une seule valeur** pour cette propriété.
- *Exemple :* À un instant donné, un emprunt ne peut concerner qu'un seul exemplaire physique (`ex:concerneExemplaire`).

### Clé d'identification (`owl:hasKey`)
Axiome OWL 2 permettant de désigner un groupe de propriétés qui identifie de manière unique chaque instance d'une classe.
- *Exemple :* Le `ex:codeBarres` d'un `ExemplairePhysique`.

### Hypothèse du Monde Ouvert (OWA - Open World Assumption)
En OWL, ce qui n'est pas explicitement affirmé dans le graphe n'est **pas considéré comme faux**, mais simplement comme **inconnu**. 
> *Conséquence capitale :* L'absence d'une date d'emprunt dans une fiche ne provoque pas une erreur en OWL ! C'est pourquoi OWL est parfait pour l'inférence, mais incapable à lui seul de valider la conformité d'un formulaire ou d'un flux de données. C'est le rôle de SHACL.

---

## 3. Validation et Règles avec SHACL

### SHACL (Shapes Constraint Language)
Standard W3C (2017) dédié à la **validation de graphes RDF**. Contrairement à OWL, SHACL opère sous une logique proche du **monde clos** : il vérifie si les données fournies satisfont un contrat strict.

### Forme de Nœud (`sh:NodeShape`)
Une forme qui cible et valide une ressource dans son ensemble (le « focus node »).
- *Exemple :* `ex:LivreValidationShape` cible la classe `ex:Livre`.

### Forme de Propriété (`sh:PropertyShape`)
Une forme qui valide les valeurs associées à un chemin donné (`sh:path`) depuis le nœud cible.
- *Exemple :* Vérifier que le chemin `ex:isbn` est présent au moins une fois (`sh:minCount 1`).

### Expression Régulière (`sh:pattern`)
Contrainte vérifiant qu'une chaîne de caractères respecte un masque syntaxique formel (Regex).
- *Exemple :* L'ISBN-13 doit commencer par 978 ou 979 : `^97[89]-\\d{1,5}-\\d+-\\d+-[0-9X]$`.

### Comparaison Relationnelle (`sh:lessThan`)
Contrainte vérifiant une inégalité stricte entre les valeurs de deux propriétés différentes du même nœud.
- *Exemple :* `ex:dateEmprunt sh:lessThan ex:dateRetourPrevue .`

### Forme Négative (`sh:not`)
Contrainte imposant qu'un nœud ne satisfasse PAS une forme cible.
- *Exemple :* `sh:not [ sh:class ex:Auteur ]` appliqué aux abonnés garantit qu'aucun individu ne peut cumuler les deux rôles disjoints.

### Monde Fermé en SHACL (`sh:closed true`)
Option interdisant qu'un individu possède des propriétés qui ne sont pas explicitement déclarées dans sa forme SHACL (à l'exception de celles listées dans `sh:ignoredProperties`). Idéal pour garantir l'intégrité de formulaires ou de profils adhérents.

### SHACL Advanced Features (SHACL-AF) & Règles (`sh:rule`)
Extension de SHACL permettant de déduire de nouveaux triplets au lieu de simplement renvoyer un rapport d'erreur.
- `sh:SPARQLRule` : utilise une requête `CONSTRUCT` avec des filtres (`FILTER`) et des calculs (`BIND`) pour injecter automatiquement des triplets calculés (ex. : statut d'emprunt `"en règle"@fr`, `"à relancer"@fr`, et calcul du montant de pénalité en euros).
