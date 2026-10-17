from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from library_owl_shacl_poc.engine import load_raw_graphs, validate_abox

EX = Namespace("https://example.org/library#")


def test_nominal_abox_data_conforms():
    """Vérifie que les données réelles et faits de la A-Box respectent tous les contrats SHACL."""
    conforms, _, report_text = validate_abox()
    assert conforms is True, f"Le jeu de données nominal doit être conforme: {report_text}"


def test_abox_invalid_isbn_is_rejected():
    """Vérifie le rejet SHACL d'un livre dont l'ISBN ne respecte pas le motif normalisé."""
    _, shapes_graph = load_raw_graphs()
    test_graph = Graph()
    test_graph.parse("rdf/ontology.ttl", format="turtle")

    bad_book = EX.bad_book
    test_graph.add((bad_book, RDF.type, EX.Livre))
    test_graph.add((bad_book, EX.titre, Literal("Livre invalide")))
    test_graph.add((bad_book, EX.isbn, Literal("ABC-12345")))  # Violates regex

    conforms, _, report = validate_abox(test_graph, shapes_graph)
    assert conforms is False
    assert "ISBN" in report or "LivreValidationShape" in report


def test_abox_invalid_dates_is_rejected():
    """Vérifie le rejet SHACL d'un emprunt dont la date de début est postérieure à la date de fin."""
    _, shapes_graph = load_raw_graphs()
    test_graph = Graph()
    test_graph.parse("rdf/ontology.ttl", format="turtle")

    bad_loan = EX.bad_loan
    test_graph.add((bad_loan, RDF.type, EX.Emprunt))
    test_graph.add((bad_loan, EX.concerneExemplaire, EX.exemplaire_ast_1))
    test_graph.add((bad_loan, EX.empruntePar, EX.abonne_alice))
    test_graph.add((bad_loan, EX.joursRetard, Literal(0)))
    test_graph.add((bad_loan, EX.dateEmprunt, Literal("2026-10-25", datatype=XSD.date)))
    test_graph.add((bad_loan, EX.dateRetourPrevue, Literal("2026-10-10", datatype=XSD.date)))

    conforms, _, report = validate_abox(test_graph, shapes_graph)
    assert conforms is False
    assert "dateEmprunt" in report or "dateRetourPrevue" in report or "lessThan" in report


def test_abox_negative_delay_is_rejected():
    """Vérifie le rejet SHACL d'une valeur numérique hors bornes (retard négatif)."""
    _, shapes_graph = load_raw_graphs()
    test_graph = Graph()
    test_graph.parse("rdf/ontology.ttl", format="turtle")

    bad_loan = EX.bad_loan_neg
    test_graph.add((bad_loan, RDF.type, EX.Emprunt))
    test_graph.add((bad_loan, EX.concerneExemplaire, EX.exemplaire_ast_1))
    test_graph.add((bad_loan, EX.empruntePar, EX.abonne_alice))
    test_graph.add((bad_loan, EX.joursRetard, Literal(-2)))  # Violates minInclusive 0
    test_graph.add((bad_loan, EX.dateEmprunt, Literal("2026-10-01", datatype=XSD.date)))
    test_graph.add((bad_loan, EX.dateRetourPrevue, Literal("2026-10-21", datatype=XSD.date)))

    conforms, _, report = validate_abox(test_graph, shapes_graph)
    assert conforms is False
    assert "joursRetard" in report or "minInclusive" in report


def test_abox_closed_shape_abonne_rejects_unknown_properties():
    """Vérifie la protection en monde fermé : rejet des propriétés inconnues sur une fiche usager."""
    _, shapes_graph = load_raw_graphs()
    test_graph = Graph()
    test_graph.parse("rdf/ontology.ttl", format="turtle")

    bad_user = EX.bad_user
    test_graph.add((bad_user, RDF.type, EX.Abonne))
    test_graph.add((bad_user, EX.nom, Literal("Jean Invalide")))
    test_graph.add((bad_user, EX.email, Literal("jean@example.org")))
    test_graph.add((bad_user, EX.proprieteInconnue, Literal("valeur interdite")))

    conforms, _, report = validate_abox(test_graph, shapes_graph)
    assert conforms is False
    assert "ClosedConstraintComponent" in report or "AbonneValidationShape" in report


def test_abox_disjoint_role_abonne_auteur_rejected():
    """Vérifie le rejet SHACL d'un individu déclaré à la fois Abonne et Auteur (disjonction de rôle)."""
    _, shapes_graph = load_raw_graphs()
    test_graph = Graph()
    test_graph.parse("rdf/ontology.ttl", format="turtle")

    dual_role = EX.dual_role_user
    test_graph.add((dual_role, RDF.type, EX.Abonne))
    test_graph.add((dual_role, RDF.type, EX.Auteur))
    test_graph.add((dual_role, EX.nom, Literal("Docteur Jekyll")))
    test_graph.add((dual_role, EX.email, Literal("jekyll@example.org")))

    conforms, _, report = validate_abox(test_graph, shapes_graph)
    assert conforms is False
    assert "disjointes" in report or "AbonneDisjointWithAuteurShape" in report or "NotConstraintComponent" in report
