from rdflib import Literal, Namespace

from library_owl_shacl_poc.engine import build_demo_graph

EX = Namespace("https://example.org/library#")


def test_shacl_rules_inference_nominal_cases():
    graph = build_demo_graph()

    # 1. Emprunt à l'heure (0 jour) -> "en règle"@fr, 0.0 €
    status_alice = list(graph.objects(EX.emprunt_alice, EX.statutEmprunt))
    penalite_alice = list(graph.objects(EX.emprunt_alice, EX.penaliteEuros))
    assert Literal("en règle", lang="fr") in status_alice
    assert any(str(p) == "0.0" for p in penalite_alice)

    # 2. Emprunt léger retard (3 jours) -> "à relancer"@fr, 1.50 €
    status_bob = list(graph.objects(EX.emprunt_bob, EX.statutEmprunt))
    penalite_bob = list(graph.objects(EX.emprunt_bob, EX.penaliteEuros))
    assert Literal("à relancer", lang="fr") in status_bob
    assert any(str(p) == "1.50" for p in penalite_bob)

    # 3. Emprunt retard critique (10 jours) -> "critique"@fr, 5.00 €
    status_claire = list(graph.objects(EX.emprunt_claire, EX.statutEmprunt))
    penalite_claire = list(graph.objects(EX.emprunt_claire, EX.penaliteEuros))
    assert Literal("critique", lang="fr") in status_claire
    assert any(str(p) == "5.00" for p in penalite_claire)
