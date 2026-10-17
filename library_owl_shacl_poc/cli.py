from pathlib import Path

from rdflib import Namespace

from .engine import build_demo_graph, validate_abox, validate_tbox_consistency
from .export import save_graph
from .visualization import export_visualizations

EX = Namespace("https://example.org/library#")
LOANS = (
    ("emprunt_alice", EX.emprunt_alice, "Alice Dupont (Astérix le Gaulois)"),
    ("emprunt_bob", EX.emprunt_bob, "Bob Martin (Web Sémantique et Ontologies)"),
    ("emprunt_claire", EX.emprunt_claire, "Claire Bernard (Web Sémantique et Ontologies)"),
)


def main(output_path: str | Path = Path("artifacts/library-result.ttl")) -> None:
    print("=" * 76)
    print("Démonstration Pédagogique : Ontologie OWL 2 et Règles SHACL en Médiathèque")
    print("=" * 76)
    print("Un triplet RDF se lit : Sujet (Exemplaire/Emprunt) — Prédicat (Propriété) — Objet (Valeur).\n")

    # -------------------------------------------------------------------------
    # 1. Validation de la T-Box (Terminological Box)
    # -------------------------------------------------------------------------
    print("┌" + "─" * 74 + "┐")
    print("│ 1. VALIDATION DE LA T-BOX (Modèle conceptuel & Vocabulaire)             │")
    print("└" + "─" * 74 + "┘")
    print("Objectif : vérifier que le schéma de l'ontologie est intrinsèquement sain.")
    print("- Détection des classes insatisfiables (conflits d'héritage entre classes disjointes)")
    print("- Détection des cycles d'héritage illégaux (boucles subClassOf)")
    print("- Contrôle qualité de la documentation (présence des rdfs:label et rdfs:comment)\n")

    tbox_report = validate_tbox_consistency()
    if tbox_report["consistent"]:
        print(
            f"  -> Résultat T-Box : MODÈLE COHÉRENT ET VALIDE\n"
            f"     {tbox_report['classes_count']} classes OWL, "
            f"{tbox_report['object_properties_count']} relations d'objets, "
            f"{tbox_report['datatype_properties_count']} propriétés de données.\n"
            f"     Aucun conflit logique ni cycle détecté."
        )
    else:
        print("  -> Résultat T-Box : INCOHÉRENCE DÉTECTÉE DANS LE MODÈLE !")
        for err in tbox_report["errors"]:
            print(f"     [ERREUR T-BOX] {err}")

    # -------------------------------------------------------------------------
    # 2. Validation de la A-Box (Assertional Box)
    # -------------------------------------------------------------------------
    print("\n┌" + "─" * 74 + "┐")
    print("│ 2. VALIDATION DE LA A-BOX (Faits réels & Données d'instances)           │")
    print("└" + "─" * 74 + "┘")
    print("Objectif : vérifier que les données concrètes respectent les contrats SHACL.")
    print("- Validation syntaxique (format regex ISBN-13 sur les livres)")
    print("- Intégrité temporelle (dateEmprunt antérieure à dateRetourPrevue)")
    print("- Monde fermé sur les usagers (rejet des propriétés inconnues sur les abonnés)")
    print("- Disjonction des rôles (un usager abonné ne peut être déclaré auteur)\n")

    abox_conforms, _, report_text = validate_abox()
    if abox_conforms:
        print("  -> Résultat A-Box : DONNÉES 100% CONFORMES (toutes les formes SHACL sont satisfaites).")
    else:
        print("  -> Résultat A-Box : NON CONFORME (violations détectées).")
        print(report_text)

    # -------------------------------------------------------------------------
    # 3. Inférence SHACL-AF (Règles conditionnelles)
    # -------------------------------------------------------------------------
    print("\n┌" + "─" * 74 + "┐")
    print("│ 3. INFÉRENCE PAR RÈGLES SHACL-AF (Enrichissement du graphe)             │")
    print("└" + "─" * 74 + "┘")
    print("Objectif : calculer dynamiquement le statut et les pénalités sans code métier.")
    print("   Règle 1 : retard = 0 jour  -> statut « en règle », pénalité 0.00 €.")
    print("   Règle 2 : 0 < retard < 7 j -> statut « à relancer », pénalité 0.50 € / jour.")
    print("   Règle 3 : retard >= 7 j    -> statut « critique », pénalité 0.50 € / jour.\n")

    graph = build_demo_graph()
    destination = save_graph(graph, output_path)

    for label, uri, desc in LOANS:
        delays = list(graph.objects(uri, EX.joursRetard))
        delay = delays[0] if delays else 0
        statuts = [str(val) for val in sorted(graph.objects(uri, EX.statutEmprunt), key=str)]
        penalites = [str(val) for val in sorted(graph.objects(uri, EX.penaliteEuros), key=str)]

        statut_str = ", ".join(statuts) if statuts else "aucun statut calculé"
        penalite_str = f"{penalites[0]} €" if penalites else "0.00 €"

        print(f"[{label}] {desc} :")
        print(f"  retard={delay} jour(s) -> Statut: {statut_str} | Pénalité: {penalite_str}")
        for s in statuts:
            print(f'  triplet inféré: sujet={label} ; prédicat=statutEmprunt ; objet="{s}"@fr')
        for p in penalites:
            print(f'  triplet inféré: sujet={label} ; prédicat=penaliteEuros ; objet="{p}"^^xsd:decimal')

    print(f"\nGraphe enrichi enregistré: {destination}")
    viz_artifacts = export_visualizations(graph, Path(destination).parent)
    print(f"Diagramme Mermaid enregistré: {viz_artifacts['mermaid']}")
    print(f"Visualisation interactive HTML enregistrée: {viz_artifacts['html']}")
    print("=" * 76)
