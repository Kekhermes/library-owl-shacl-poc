from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF, RDFS

from library_owl_shacl_poc.engine import load_ontology_graph, validate_tbox_consistency

EX = Namespace("https://example.org/library#")


def test_tbox_nominal_consistency():
    """Vérifie que la T-Box nominale est parfaitement cohérente, sans cycle ni insatisfiabilité."""
    report = validate_tbox_consistency()
    assert report["consistent"] is True
    assert report["classes_count"] >= 10
    assert len(report["errors"]) == 0
    assert len(report["warnings"]) == 0


def test_tbox_disjoint_conflict_breaking_change():
    """Simule une régression dans la T-Box : l'ajout d'une classe héritant de deux classes disjointes.

    Par exemple, déclarer un 'LivreHybride' qui serait à la fois sous-classe de 'LivreNumerique'
    et de 'ExemplairePhysique' (deux classes disjointes par axiome).
    """
    g = load_ontology_graph()

    # Ajout d'une classe logiquement impossible (insatisfiable)
    bad_class = EX.LivreHybrideImpossible
    g.add((bad_class, RDF.type, OWL.Class))
    g.add((bad_class, RDFS.subClassOf, EX.LivreNumerique))
    g.add((bad_class, RDFS.subClassOf, EX.ExemplairePhysique))

    report = validate_tbox_consistency(g)
    assert report["consistent"] is False
    assert any("insatisfiable" in err for err in report["errors"])
    assert any("LivreHybrideImpossible" in err for err in report["errors"])


def test_tbox_circular_subclass_breaking_change():
    """Simule une régression dans la T-Box : l'introduction d'un cycle d'héritage circulaire.

    Par exemple, déclarer Document subClassOf BandeDessinee alors que BandeDessinee est déjà
    subClassOf Livre subClassOf Document.
    """
    g = load_ontology_graph()

    # Introduction d'un cycle
    g.add((EX.Document, RDFS.subClassOf, EX.BandeDessinee))

    report = validate_tbox_consistency(g)
    assert report["consistent"] is False
    assert any("Cycle d'héritage" in err for err in report["errors"])


def test_tbox_missing_documentation_warning():
    """Vérifie que le validateur de T-Box signale l'absence de label ou de commentaire."""
    g = load_ontology_graph()

    orphan_class = EX.ClasseNonDocumentee
    g.add((orphan_class, RDF.type, OWL.Class))

    report = validate_tbox_consistency(g)
    assert report["consistent"] is True  # Logiquement cohérent mais...
    assert len(report["warnings"]) >= 2   # Avertissements qualité émis
    assert any("rdfs:label" in w for w in report["warnings"])
    assert any("rdfs:comment" in w for w in report["warnings"])
