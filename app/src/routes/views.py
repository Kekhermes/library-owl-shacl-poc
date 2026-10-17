from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..core.config import BASE_DIR
from ..core.database import get_db
from ..models.entities import Abonne, Auteur, Emprunt, Exemplaire, Livre, Theme
from ..services.rdf_mapper import db_to_rdf_graph
from ..services.shacl_service import run_shacl_af_inferences, validate_candidate_entity

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "src" / "templates"))


# =============================================================================
# 1. Tableau de bord
# =============================================================================
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_livres = db.query(Livre).count()
    total_exemplaires = db.query(Exemplaire).count()
    total_abonnes = db.query(Abonne).count()
    total_emprunts = db.query(Emprunt).count()

    emprunts_en_retard = db.query(Emprunt).filter(Emprunt.jours_retard > 0).count()
    dernier_calcul = db.query(Emprunt).filter(Emprunt.statut_emprunt.isnot(None)).count()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_livres": total_livres,
            "total_exemplaires": total_exemplaires,
            "total_abonnes": total_abonnes,
            "total_emprunts": total_emprunts,
            "emprunts_en_retard": emprunts_en_retard,
            "dernier_calcul": dernier_calcul,
        },
    )


# =============================================================================
# 2. Gestion des Livres (CRUD + SHACL)
# =============================================================================
@router.get("/livres", response_class=HTMLResponse)
def list_livres(request: Request, db: Session = Depends(get_db), error: Optional[str] = None):
    livres = db.query(Livre).order_by(Livre.id.desc()).all()
    auteurs = db.query(Auteur).all()
    themes = db.query(Theme).all()
    return templates.TemplateResponse(
        request=request,
        name="livres.html",
        context={
            "livres": livres,
            "auteurs": auteurs,
            "themes": themes,
            "error": error,
        },
    )


@router.post("/livres")
def create_livre(
    request: Request,
    titre: str = Form(...),
    isbn: str = Form(...),
    type_livre: str = Form("Livre"),
    auteur_id: int = Form(...),
    theme_id: int = Form(...),
    db: Session = Depends(get_db),
):
    auteur = db.query(Auteur).filter(Auteur.id == auteur_id).first()
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    code = f"livre_{int(datetime.now().timestamp())}"

    candidate_data = {
        "code": code,
        "titre": titre.strip(),
        "isbn": isbn.strip(),
        "type_livre": type_livre,
        "auteur_code": auteur.code if auteur else None,
        "theme_code": theme.code if theme else None,
    }

    # 1. Validation préventive bloquante par SHACL
    is_valid, error_msg = validate_candidate_entity(db, "livre", candidate_data)
    if not is_valid:
        livres = db.query(Livre).all()
        auteurs = db.query(Auteur).all()
        themes = db.query(Theme).all()
        return templates.TemplateResponse(
            request=request,
            name="livres.html",
            context={
                "livres": livres,
                "auteurs": auteurs,
                "themes": themes,
                "error": f"Rejet SHACL : {error_msg}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Écriture en base PostgreSQL
    nouveau_livre = Livre(
        code=code,
        titre=titre.strip(),
        isbn=isbn.strip(),
        type_livre=type_livre,
        auteur_id=auteur_id,
        theme_id=theme_id,
    )
    db.add(nouveau_livre)
    db.flush()

    # Création automatique d'un premier exemplaire physique
    nouvel_exemplaire = Exemplaire(
        code=f"exemplaire_{code}",
        code_barres=f"BC-{code[-6:].upper()}",
        livre_id=nouveau_livre.id,
    )
    db.add(nouvel_exemplaire)
    db.commit()

    return RedirectResponse(url="/livres", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/livres/{livre_id}/delete")
def delete_livre(livre_id: int, db: Session = Depends(get_db)):
    livre = db.query(Livre).filter(Livre.id == livre_id).first()
    if livre:
        db.delete(livre)
        db.commit()
    return RedirectResponse(url="/livres", status_code=status.HTTP_303_SEE_OTHER)


# =============================================================================
# 3. Gestion des Abonnés (CRUD + SHACL)
# =============================================================================
@router.get("/abonnes", response_class=HTMLResponse)
def list_abonnes(request: Request, db: Session = Depends(get_db), error: Optional[str] = None):
    abonnes = db.query(Abonne).order_by(Abonne.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="abonnes.html",
        context={
            "abonnes": abonnes,
            "error": error,
        },
    )


@router.post("/abonnes")
def create_abonne(
    request: Request,
    nom: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    code = f"abonne_{int(datetime.now().timestamp())}"
    candidate_data = {
        "code": code,
        "nom": nom.strip(),
        "email": email.strip(),
    }

    # Validation préventive SHACL
    is_valid, error_msg = validate_candidate_entity(db, "abonne", candidate_data)
    if not is_valid:
        abonnes = db.query(Abonne).all()
        return templates.TemplateResponse(
            request=request,
            name="abonnes.html",
            context={
                "abonnes": abonnes,
                "error": f"Rejet SHACL : {error_msg}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    nouvel_abonne = Abonne(code=code, nom=nom.strip(), email=email.strip())
    db.add(nouvel_abonne)
    db.commit()
    return RedirectResponse(url="/abonnes", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/abonnes/{abonne_id}/delete")
def delete_abonne(abonne_id: int, db: Session = Depends(get_db)):
    abonne = db.query(Abonne).filter(Abonne.id == abonne_id).first()
    if abonne:
        db.delete(abonne)
        db.commit()
    return RedirectResponse(url="/abonnes", status_code=status.HTTP_303_SEE_OTHER)


# =============================================================================
# 4. Gestion des Emprunts (CRUD + SHACL)
# =============================================================================
@router.get("/emprunts", response_class=HTMLResponse)
def list_emprunts(request: Request, db: Session = Depends(get_db), error: Optional[str] = None):
    emprunts = db.query(Emprunt).order_by(Emprunt.id.desc()).all()
    exemplaires = db.query(Exemplaire).all()
    abonnes = db.query(Abonne).all()
    return templates.TemplateResponse(
        request=request,
        name="emprunts.html",
        context={
            "emprunts": emprunts,
            "exemplaires": exemplaires,
            "abonnes": abonnes,
            "error": error,
        },
    )


@router.post("/emprunts")
def create_emprunt(
    request: Request,
    exemplaire_id: int = Form(...),
    abonne_id: int = Form(...),
    date_emprunt: str = Form(...),
    date_retour_prevue: str = Form(...),
    jours_retard: int = Form(0),
    db: Session = Depends(get_db),
):
    exemplaire = db.query(Exemplaire).filter(Exemplaire.id == exemplaire_id).first()
    abonne = db.query(Abonne).filter(Abonne.id == abonne_id).first()
    code = f"emprunt_{int(datetime.now().timestamp())}"

    candidate_data = {
        "code": code,
        "exemplaire_code": exemplaire.code if exemplaire else None,
        "abonne_code": abonne.code if abonne else None,
        "date_emprunt": date.fromisoformat(date_emprunt),
        "date_retour_prevue": date.fromisoformat(date_retour_prevue),
        "jours_retard": int(jours_retard),
    }

    # Validation préventive SHACL (moins-que temporel, retards positifs, etc.)
    is_valid, error_msg = validate_candidate_entity(db, "emprunt", candidate_data)
    if not is_valid:
        emprunts = db.query(Emprunt).all()
        exemplaires = db.query(Exemplaire).all()
        abonnes = db.query(Abonne).all()
        return templates.TemplateResponse(
            request=request,
            name="emprunts.html",
            context={
                "emprunts": emprunts,
                "exemplaires": exemplaires,
                "abonnes": abonnes,
                "error": f"Rejet SHACL : {error_msg}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    nouvel_emprunt = Emprunt(
        code=code,
        exemplaire_id=exemplaire_id,
        abonne_id=abonne_id,
        date_emprunt=date.fromisoformat(date_emprunt),
        date_retour_prevue=date.fromisoformat(date_retour_prevue),
        jours_retard=int(jours_retard),
    )
    db.add(nouvel_emprunt)
    db.commit()
    return RedirectResponse(url="/emprunts", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/emprunts/{emprunt_id}/retard")
def update_retard(
    request: Request,
    emprunt_id: int,
    jours_retard: int = Form(...),
    db: Session = Depends(get_db),
):
    emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt non trouvé")

    candidate_data = {
        "code": emprunt.code,
        "exemplaire_code": emprunt.exemplaire.code,
        "abonne_code": emprunt.abonne.code,
        "date_emprunt": emprunt.date_emprunt,
        "date_retour_prevue": emprunt.date_retour_prevue,
        "jours_retard": int(jours_retard),
    }

    is_valid, error_msg = validate_candidate_entity(db, "emprunt", candidate_data, existing_code=emprunt.code)
    if not is_valid:
        emprunts = db.query(Emprunt).all()
        exemplaires = db.query(Exemplaire).all()
        abonnes = db.query(Abonne).all()
        return templates.TemplateResponse(
            request=request,
            name="emprunts.html",
            context={
                "emprunts": emprunts,
                "exemplaires": exemplaires,
                "abonnes": abonnes,
                "error": f"Rejet SHACL : {error_msg}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    emprunt.jours_retard = int(jours_retard)
    db.commit()
    return RedirectResponse(url="/emprunts", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/emprunts/{emprunt_id}/delete")
def delete_emprunt(emprunt_id: int, db: Session = Depends(get_db)):
    emprunt = db.query(Emprunt).filter(Emprunt.id == emprunt_id).first()
    if emprunt:
        db.delete(emprunt)
        db.commit()
    return RedirectResponse(url="/emprunts", status_code=status.HTTP_303_SEE_OTHER)


# =============================================================================
# 5. Inférence SHACL-AF (Feature explicite avec feedback)
# =============================================================================
@router.get("/inference", response_class=HTMLResponse)
def inference_page(request: Request, db: Session = Depends(get_db)):
    emprunts = db.query(Emprunt).all()
    return templates.TemplateResponse(
        request=request,
        name="inference.html",
        context={
            "emprunts": emprunts,
            "feedback": None,
        },
    )


@router.post("/inference/run", response_class=HTMLResponse)
def run_inference(request: Request, db: Session = Depends(get_db)):
    result = run_shacl_af_inferences(db)
    emprunts = db.query(Emprunt).all()
    return templates.TemplateResponse(
        request=request,
        name="inference.html",
        context={
            "emprunts": emprunts,
            "feedback": result,
        },
    )


# =============================================================================
# 6. Visualiseur Turtle dynamique de la A-Box
# =============================================================================
@router.get("/rdf-export", response_class=HTMLResponse)
def view_rdf(request: Request, db: Session = Depends(get_db)):
    g = db_to_rdf_graph(db, include_ontology=False)
    turtle_text = g.serialize(format="turtle")
    return templates.TemplateResponse(
        request=request,
        name="rdf_export.html",
        context={
            "turtle_text": turtle_text,
            "triples_count": len(g),
        },
    )
