from rdflib import Namespace
from rdflib.namespace import RDF
from sqlalchemy.orm import Session

from app.src.services.rdf_mapper import db_to_rdf_graph

EX = Namespace("https://example.org/library#")


def test_db_to_rdf_graph_mapping(db_session: Session):
    graph = db_to_rdf_graph(db_session, include_ontology=False)

    # Vérification des entités mappées
    assert (EX.livre_asterix, RDF.type, EX.BandeDessinee) in graph
    assert (EX.livre_ontologies, RDF.type, EX.Livre) in graph
    assert (EX.exemplaire_ast_1, RDF.type, EX.ExemplairePhysique) in graph
    assert (EX.abonne_alice, RDF.type, EX.Abonne) in graph
    assert (EX.emprunt_alice, RDF.type, EX.Emprunt) in graph

    # Relations d'inversion & propriétés
    assert (EX.livre_asterix, EX.aPourAuteur, EX.auteur_goscinny) in graph
    assert (EX.auteur_goscinny, EX.aEcrit, EX.livre_asterix) in graph
    assert (EX.auteur_goscinny, EX.coAuteurAvec, EX.auteur_uderzo) in graph
