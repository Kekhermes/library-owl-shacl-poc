from decimal import Decimal
from typing import Any
from pyshacl import shacl_rules, validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD
from sqlalchemy.orm import Session

from ..core.config import RDF_SHAPES_PATH
from ..models.entities import Abonne, Emprunt, Exemplaire, Livre
from .rdf_mapper import db_to_rdf_graph

EX = Namespace("https://example.org/library#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def get_shapes_graph() -> Graph:
    shapes_g = Graph()
    shapes_g.parse(RDF_SHAPES_PATH, format="turtle")
    return shapes_g


def _extract_friendly_message(report_graph: Graph, report_text: str) -> str:
    """Extrait un message d'erreur lisible à partir du rapport de violation SHACL."""
    messages = []
    for result in report_graph.subjects(RDF.type, SH.ValidationResult):
        msg_nodes = list(report_graph.objects(result, SH.resultMessage))
        if msg_nodes:
            messages.append(str(msg_nodes[0]))
    if messages:
        return " ; ".join(messages)
    # Repli sur les premières lignes informatives du texte brut
    lines = [line.strip() for line in report_text.splitlines() if "Message:" in line or "Severity:" in line]
    return " | ".join(lines) if lines else "Violation des contraintes de forme SHACL."


def validate_candidate_entity(
    db: Session,
    entity_type: str,
    data: dict[str, Any],
    existing_code: str | None = None,
) -> tuple[bool, str]:
    """Valide préventivement une entité candidate avant écriture dans PostgreSQL."""
    # 1. Générer le graphe actuel de la base
    graph = db_to_rdf_graph(db, include_ontology=True)
    shapes_graph = get_shapes_graph()

    # 2. Si modification, retirer temporairement les triplets de l'individu existant
    if existing_code:
        node_uri = EX[existing_code]
        for s, p, o in list(graph.triples((node_uri, None, None))):
            graph.remove((s, p, o))

    # 3. Injecter les triplets de l'entité candidate
    code = existing_code or data.get("code") or "candidat_temp"
    subject = EX[code]

    if entity_type == "livre":
        cls_type = EX.BandeDessinee if data.get("type_livre") == "BandeDessinee" else EX.Livre
        graph.add((subject, RDF.type, cls_type))
        if data.get("titre"):
            graph.add((subject, EX.titre, Literal(data["titre"])))
        if data.get("isbn"):
            graph.add((subject, EX.isbn, Literal(data["isbn"])))
        if data.get("auteur_code"):
            graph.add((subject, EX.aPourAuteur, EX[data["auteur_code"]]))
        if data.get("theme_code"):
            graph.add((subject, EX.traiteDe, EX[data["theme_code"]]))

    elif entity_type == "abonne":
        graph.add((subject, RDF.type, EX.Abonne))
        if data.get("nom"):
            graph.add((subject, EX.nom, Literal(data["nom"])))
        if data.get("email"):
            graph.add((subject, EX.email, Literal(data["email"])))

    elif entity_type == "exemplaire":
        graph.add((subject, RDF.type, EX.ExemplairePhysique))
        if data.get("code_barres"):
            graph.add((subject, EX.codeBarres, Literal(data["code_barres"])))
        if data.get("livre_code"):
            graph.add((subject, EX.exemplaireDe, EX[data["livre_code"]]))

    elif entity_type == "emprunt":
        graph.add((subject, RDF.type, EX.Emprunt))
        if data.get("exemplaire_code"):
            graph.add((subject, EX.concerneExemplaire, EX[data["exemplaire_code"]]))
        if data.get("abonne_code"):
            graph.add((subject, EX.empruntePar, EX[data["abonne_code"]]))
        if data.get("date_emprunt"):
            d_emp = data["date_emprunt"].isoformat() if hasattr(data["date_emprunt"], "isoformat") else str(data["date_emprunt"])
            graph.add((subject, EX.dateEmprunt, Literal(d_emp, datatype=XSD.date)))
        if data.get("date_retour_prevue"):
            d_ret = data["date_retour_prevue"].isoformat() if hasattr(data["date_retour_prevue"], "isoformat") else str(data["date_retour_prevue"])
            graph.add((subject, EX.dateRetourPrevue, Literal(d_ret, datatype=XSD.date)))
        if "jours_retard" in data and data["jours_retard"] is not None:
            graph.add((subject, EX.joursRetard, Literal(int(data["jours_retard"]), datatype=XSD.integer)))

    # 4. Valider avec pySHACL
    conforms, report_graph, report_text = validate(
        graph,
        shacl_graph=shapes_graph,
        advanced=True,
    )

    if conforms:
        return True, ""
    error_msg = _extract_friendly_message(report_graph, report_text)
    return False, error_msg


def run_shacl_af_inferences(db: Session) -> dict[str, Any]:
    """Exécute les règles SHACL-AF sur les emprunts et persiste les déductions dans PostgreSQL."""
    data_graph = db_to_rdf_graph(db, include_ontology=True)
    shapes_graph = get_shapes_graph()

    # Exécution du moteur de règles SHACL-AF
    expanded_graph = shacl_rules(data_graph, shacl_graph=shapes_graph, advanced=True)

    deltas = []
    emprunts = db.query(Emprunt).all()

    for emp in emprunts:
        uri = EX[emp.code]
        inferred_statuts = list(expanded_graph.objects(uri, EX.statutEmprunt))
        inferred_penalites = list(expanded_graph.objects(uri, EX.penaliteEuros))

        new_statut = str(inferred_statuts[0]) if inferred_statuts else None
        new_penalite = Decimal(str(inferred_penalites[0])) if inferred_penalites else None

        old_statut = emp.statut_emprunt
        old_penalite = emp.penalite_euros

        has_changed = (new_statut != old_statut) or (new_penalite != old_penalite)

        if new_statut is not None:
            emp.statut_emprunt = new_statut
        if new_penalite is not None:
            emp.penalite_euros = new_penalite

        deltas.append({
            "code": emp.code,
            "abonne": emp.abonne.nom if emp.abonne else "Inconnu",
            "livre": emp.exemplaire.livre.titre if emp.exemplaire and emp.exemplaire.livre else "Inconnu",
            "jours_retard": emp.jours_retard,
            "old_statut": old_statut or "Non calculé",
            "new_statut": new_statut or "Non calculé",
            "old_penalite": f"{old_penalite:.2f} €" if old_penalite is not None else "0.00 €",
            "new_penalite": f"{new_penalite:.2f} €" if new_penalite is not None else "0.00 €",
            "has_changed": has_changed,
        })

    db.commit()

    return {
        "success": True,
        "total_emprunts": len(emprunts),
        "deltas": deltas,
    }
