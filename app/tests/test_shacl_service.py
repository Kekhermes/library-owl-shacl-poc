from datetime import date
from sqlalchemy.orm import Session

from app.src.models.entities import Emprunt
from app.src.services.shacl_service import run_shacl_af_inferences, validate_candidate_entity


def test_validate_candidate_valid_book(db_session: Session):
    candidate = {
        "code": "livre_nouveau",
        "titre": "Clean Code",
        "isbn": "978-0-13-235088-4",
        "type_livre": "Livre",
        "auteur_code": "auteur_berners_lee",
        "theme_code": "theme_informatique",
    }
    is_valid, msg = validate_candidate_entity(db_session, "livre", candidate)
    assert is_valid is True
    assert msg == ""


def test_validate_candidate_invalid_isbn_rejected(db_session: Session):
    candidate = {
        "code": "livre_bad",
        "titre": "Livre Invalide",
        "isbn": "123-NOT-AN-ISBN",
        "type_livre": "Livre",
        "auteur_code": "auteur_berners_lee",
        "theme_code": "theme_informatique",
    }
    is_valid, msg = validate_candidate_entity(db_session, "livre", candidate)
    assert is_valid is False
    assert len(msg) > 0


def test_validate_candidate_duplicate_isbn_rejected(db_session: Session):
    # L'ISBN de livre_asterix est 978-2-01-210133-3
    candidate = {
        "code": "livre_doublon",
        "titre": "Autre Livre avec Même ISBN",
        "isbn": "978-2-01-210133-3",
        "type_livre": "Livre",
        "auteur_code": "auteur_berners_lee",
        "theme_code": "theme_informatique",
    }
    is_valid, msg = validate_candidate_entity(db_session, "livre", candidate)
    assert is_valid is False
    assert "unicité requise" in msg or "distincts" in msg


def test_validate_candidate_inverted_dates_rejected(db_session: Session):
    candidate = {
        "code": "emprunt_bad_dates",
        "exemplaire_code": "exemplaire_ast_1",
        "abonne_code": "abonne_alice",
        "date_emprunt": date(2026, 11, 20),
        "date_retour_prevue": date(2026, 10, 1),
        "jours_retard": 0,
    }
    is_valid, msg = validate_candidate_entity(db_session, "emprunt", candidate)
    assert is_valid is False
    assert "antérieure" in msg or "lessThan" in msg or "dateEmprunt" in msg


def test_validate_candidate_overlapping_loan_rejected(db_session: Session):
    # emprunt_alice concerne exemplaire_ast_1 du 2026-10-01 au 2026-10-21
    candidate = {
        "code": "emprunt_collision",
        "exemplaire_code": "exemplaire_ast_1",
        "abonne_code": "abonne_bob",
        "date_emprunt": date(2026, 10, 15),
        "date_retour_prevue": date(2026, 11, 5),
        "jours_retard": 0,
    }
    is_valid, msg = validate_candidate_entity(db_session, "emprunt", candidate)
    assert is_valid is False
    assert "chevauchement" in msg or "plusieurs personnes" in msg


def test_run_shacl_af_inferences(db_session: Session):
    result = run_shacl_af_inferences(db_session)
    assert result["success"] is True
    assert result["total_emprunts"] == 2

    # Vérification que la base de données a bien été mise à jour par l'inférence
    emp_alice = db_session.query(Emprunt).filter(Emprunt.code == "emprunt_alice").first()
    emp_bob = db_session.query(Emprunt).filter(Emprunt.code == "emprunt_bob").first()

    assert emp_alice.statut_emprunt == "en règle"
    assert str(emp_alice.penalite_euros) == "0.00"

    assert emp_bob.statut_emprunt == "à relancer"
    assert str(emp_bob.penalite_euros) == "1.50"
