from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF, RDFS, XSD

EX = Namespace("https://example.org/library#")


def test_ontology_classes_and_hierarchy():
    g = Graph()
    g.parse("rdf/ontology.ttl", format="turtle")

    # Classes principales
    classes = set(g.subjects(RDF.type, OWL.Class))
    assert EX.Document in classes
    assert EX.Livre in classes
    assert EX.BandeDessinee in classes
    assert EX.ExemplairePhysique in classes
    assert EX.Abonne in classes
    assert EX.Auteur in classes
    assert EX.Emprunt in classes

    # Hiérarchie (subClassOf)
    assert (EX.Livre, RDFS.subClassOf, EX.Document) in g
    assert (EX.BandeDessinee, RDFS.subClassOf, EX.Livre) in g
    assert (EX.Abonne, RDFS.subClassOf, EX.Personne) in g
    assert (EX.Auteur, RDFS.subClassOf, EX.Personne) in g

    # Disjonction
    assert (EX.LivreNumerique, OWL.disjointWith, EX.ExemplairePhysique) in g
    assert (EX.Abonne, OWL.disjointWith, EX.Auteur) in g


def test_ontology_properties_axioms():
    g = Graph()
    g.parse("rdf/ontology.ttl", format="turtle")

    # Inverses
    assert (EX.aPourAuteur, OWL.inverseOf, EX.aEcrit) in g
    assert (EX.aEcrit, OWL.inverseOf, EX.aPourAuteur) in g

    # Propriété symétrique
    assert (EX.coAuteurAvec, RDF.type, OWL.SymmetricProperty) in g

    # Propriété transitive
    assert (EX.themeParent, RDF.type, OWL.TransitiveProperty) in g

    # Propriétés fonctionnelles
    assert (EX.concerneExemplaire, RDF.type, OWL.FunctionalProperty) in g
    assert (EX.empruntePar, RDF.type, OWL.FunctionalProperty) in g
    assert (EX.codeBarres, RDF.type, OWL.FunctionalProperty) in g
    assert (EX.isbn, RDF.type, OWL.FunctionalProperty) in g


def test_data_individuals_loaded():
    g = Graph()
    g.parse("rdf/ontology.ttl", format="turtle")
    g.parse("rdf/data.ttl", format="turtle")

    # Individus
    assert (EX.livre_asterix, RDF.type, EX.BandeDessinee) in g
    assert (EX.livre_ontologies, RDF.type, EX.Livre) in g
    assert (EX.abonne_alice, RDF.type, EX.Abonne) in g
    assert (EX.emprunt_alice, RDF.type, EX.Emprunt) in g
    assert (EX.auteur_goscinny, EX.coAuteurAvec, EX.auteur_uderzo) in g
