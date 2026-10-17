from datetime import date
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.src.core.database import Base, get_db
from app.src.models.entities import Abonne, Auteur, Emprunt, Exemplaire, Livre, Theme
from app.src.main import app

# SQLite en mémoire partagé avec StaticPool pour conserver les tables entre connexions
TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Insertion des données de base de test
    t1 = Theme(code="theme_sciences", label="Sciences & Techniques")
    t2 = Theme(code="theme_informatique", label="Informatique", parent=t1)
    t3 = Theme(code="theme_ontologies", label="Web Sémantique & Ontologies", parent=t2)
    session.add_all([t1, t2, t3])

    a1 = Auteur(code="auteur_goscinny", nom="René Goscinny")
    a2 = Auteur(code="auteur_uderzo", nom="Albert Uderzo", co_auteur=a1)
    a3 = Auteur(code="auteur_berners_lee", nom="Tim Berners-Lee")
    session.add_all([a1, a2, a3])
    session.flush()
    a1.co_auteur = a2

    l1 = Livre(code="livre_asterix", titre="Astérix le Gaulois", isbn="978-2-01-210133-3", type_livre="BandeDessinee", auteur=a1, theme=t1)
    l2 = Livre(code="livre_ontologies", titre="Le Web Sémantique et les Ontologies", isbn="978-2-10-049876-5", type_livre="Livre", auteur=a3, theme=t3)
    session.add_all([l1, l2])
    session.flush()

    ex1 = Exemplaire(code="exemplaire_ast_1", code_barres="BC-AST-001", livre=l1)
    ex2 = Exemplaire(code="exemplaire_ont_1", code_barres="BC-ONT-001", livre=l2)
    session.add_all([ex1, ex2])

    ab1 = Abonne(code="abonne_alice", nom="Alice Dupont", email="alice.dupont@example.org")
    ab2 = Abonne(code="abonne_bob", nom="Bob Martin", email="bob.martin@example.org")
    session.add_all([ab1, ab2])
    session.flush()

    emp1 = Emprunt(
        code="emprunt_alice",
        exemplaire=ex1,
        abonne=ab1,
        date_emprunt=date(2026, 10, 1),
        date_retour_prevue=date(2026, 10, 21),
        jours_retard=0,
    )
    emp2 = Emprunt(
        code="emprunt_bob",
        exemplaire=ex2,
        abonne=ab2,
        date_emprunt=date(2026, 9, 15),
        date_retour_prevue=date(2026, 10, 5),
        jours_retard=3,
    )
    session.add_all([emp1, emp2])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
