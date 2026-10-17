from pathlib import Path

from rdflib import Namespace

from .engine import build_demo_graph, validate_data_graph
from .export import save_graph
from .visualization import export_visualizations

EX = Namespace("https://example.org/library#")
LOANS = (
    ("emprunt_alice", EX.emprunt_alice, "Alice Dupont (Astérix le Gaulois)"),
    ("emprunt_bob", EX.emprunt_bob, "Bob Martin (Web Sémantique et Ontologies)"),
    ("emprunt_claire", EX.emprunt_claire, "Claire Bernard (Web Sémantique et Ontologies)"),
)


def main(output_path: str | Path = Path("artifacts/library-result.ttl")) -> None:
    print("=" * 72)
    print("Démonstration : Ontologie OWL 2 et Règles SHACL en Médiathèque")
    print("=" * 72)
    print("Un triplet RDF se lit : Sujet (Exemplaire/Emprunt) — Prédicat (Propriété) — Objet (Valeur).")
    print("1. Étape de validation SHACL Core : vérification de l'intégrité des données.")

    conforms, _, report_text = validate_data_graph()
    if conforms:
        print("  -> Validation SHACL : CONFORME (tous les contrats de forme sont respectés).")
    else:
        print("  -> Validation SHACL : NON CONFORME.")
        print(report_text)

    print("\n2. Étape d'inférence SHACL-AF : exécution des règles conditionnelles.")
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
    print("=" * 72)
