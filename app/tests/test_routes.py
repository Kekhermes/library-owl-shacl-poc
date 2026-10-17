from fastapi.testclient import TestClient


def test_dashboard_route(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Tableau de bord de la Médiathèque" in response.text
    assert "Livres &amp; Œuvres" in response.text or "Livres & Œuvres" in response.text


def test_livres_crud_and_shacl_blocking(client: TestClient):
    # 1. Liste
    res = client.get("/livres")
    assert res.status_code == 200
    assert "Astérix le Gaulois" in res.text

    # 2. Ajout invalide (rejet SHACL 400)
    bad_res = client.post(
        "/livres",
        data={
            "titre": "Livre Faux",
            "isbn": "999-FAUX",
            "type_livre": "Livre",
            "auteur_id": "1",
            "theme_id": "1",
        },
    )
    assert bad_res.status_code == 400
    assert "Rejet SHACL" in bad_res.text

    # 3. Ajout valide
    good_res = client.post(
        "/livres",
        data={
            "titre": "Nouveau Livre Valide",
            "isbn": "978-2-07-061275-8",
            "type_livre": "Livre",
            "auteur_id": "1",
            "theme_id": "1",
        },
        follow_redirects=True,
    )
    assert good_res.status_code == 200
    assert "Nouveau Livre Valide" in good_res.text


def test_abonnes_crud_and_shacl_blocking(client: TestClient):
    # 1. Liste
    res = client.get("/abonnes")
    assert res.status_code == 200
    assert "Alice Dupont" in res.text

    # 2. Ajout invalide (email incorrect)
    bad_res = client.post(
        "/abonnes",
        data={
            "nom": "Faux Membre",
            "email": "email_sans_arobase",
        },
    )
    assert bad_res.status_code == 400
    assert "Rejet SHACL" in bad_res.text

    # 3. Ajout valide
    good_res = client.post(
        "/abonnes",
        data={
            "nom": "Nouvel Usager",
            "email": "nouvel.usager@example.org",
        },
        follow_redirects=True,
    )
    assert good_res.status_code == 200
    assert "Nouvel Usager" in good_res.text


def test_emprunts_and_shacl_temporal_blocking(client: TestClient):
    # 1. Ajout invalide (date_emprunt > date_retour_prevue)
    bad_res = client.post(
        "/emprunts",
        data={
            "exemplaire_id": "1",
            "abonne_id": "1",
            "date_emprunt": "2026-11-20",
            "date_retour_prevue": "2026-10-01",
            "jours_retard": "0",
        },
    )
    assert bad_res.status_code == 400
    assert "Rejet SHACL" in bad_res.text


def test_inference_page_and_run(client: TestClient):
    # 1. Page
    res = client.get("/inference")
    assert res.status_code == 200
    assert "Moteur d'Inférence SHACL-AF" in res.text

    # 2. Exécution de l'inférence
    run_res = client.post("/inference/run")
    assert run_res.status_code == 200
    assert "Rapport d'exécution SHACL-AF" in run_res.text
    assert "en règle" in run_res.text
    assert "à relancer" in run_res.text
