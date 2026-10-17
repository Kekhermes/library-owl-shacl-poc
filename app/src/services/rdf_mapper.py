from datetime import date
from decimal import Decimal
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from sqlalchemy.orm import Session

from ..core.config import RDF_ONTOLOGY_PATH
from ..models.entities import Abonne, Auteur, Emprunt, Exemplaire, Livre, Theme

EX = Namespace("https://example.org/library#")


def db_to_rdf_graph(db: Session, include_ontology: bool = True) -> Graph:
    """Convertit toutes les entités relationnelles de PostgreSQL en graphe RDF (A-Box)."""
    graph = Graph()
    if include_ontology:
        graph.parse(RDF_ONTOLOGY_PATH, format="turtle")

    # 1. Thèmes
    for theme in db.query(Theme).all():
        uri = EX[theme.code]
        graph.add((uri, RDF.type, EX.Theme))
        graph.add((uri, RDFS.label, Literal(theme.label, lang="fr")))
        if theme.parent:
            graph.add((uri, EX.themeParent, EX[theme.parent.code]))

    # 2. Auteurs
    for auteur in db.query(Auteur).all():
        uri = EX[auteur.code]
        graph.add((uri, RDF.type, EX.Auteur))
        graph.add((uri, EX.nom, Literal(auteur.nom)))
        if auteur.co_auteur:
            graph.add((uri, EX.coAuteurAvec, EX[auteur.co_auteur.code]))

    # 3. Livres / Documents
    for livre in db.query(Livre).all():
        uri = EX[livre.code]
        livre_type = EX.BandeDessinee if livre.type_livre == "BandeDessinee" else EX.Livre
        graph.add((uri, RDF.type, livre_type))
        graph.add((uri, EX.titre, Literal(livre.titre)))
        graph.add((uri, EX.isbn, Literal(livre.isbn)))
        if livre.auteur:
            graph.add((uri, EX.aPourAuteur, EX[livre.auteur.code]))
            graph.add((EX[livre.auteur.code], EX.aEcrit, uri))
        if livre.theme:
            graph.add((uri, EX.traiteDe, EX[livre.theme.code]))

    # 4. Exemplaires physiques
    for exemplaire in db.query(Exemplaire).all():
        uri = EX[exemplaire.code]
        graph.add((uri, RDF.type, EX.ExemplairePhysique))
        graph.add((uri, EX.codeBarres, Literal(exemplaire.code_barres)))
        graph.add((uri, EX.exemplaireDe, EX[exemplaire.livre.code]))

    # 5. Abonnés
    for abonne in db.query(Abonne).all():
        uri = EX[abonne.code]
        graph.add((uri, RDF.type, EX.Abonne))
        graph.add((uri, EX.nom, Literal(abonne.nom)))
        graph.add((uri, EX.email, Literal(abonne.email)))

    # 6. Emprunts
    for emprunt in db.query(Emprunt).all():
        uri = EX[emprunt.code]
        graph.add((uri, RDF.type, EX.Emprunt))
        graph.add((uri, EX.concerneExemplaire, EX[emprunt.exemplaire.code]))
        graph.add((uri, EX.empruntePar, EX[emprunt.abonne.code]))
        graph.add((uri, EX.dateEmprunt, Literal(emprunt.date_emprunt.isoformat(), datatype=XSD.date)))
        graph.add((uri, EX.dateRetourPrevue, Literal(emprunt.date_retour_prevue.isoformat(), datatype=XSD.date)))
        graph.add((uri, EX.joursRetard, Literal(int(emprunt.jours_retard), datatype=XSD.integer)))
        if emprunt.statut_emprunt:
            graph.add((uri, EX.statutEmprunt, Literal(emprunt.statut_emprunt, lang="fr")))
        if emprunt.penalite_euros is not None:
            graph.add((uri, EX.penaliteEuros, Literal(str(emprunt.penalite_euros), datatype=XSD.decimal)))

    return graph
