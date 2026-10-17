from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Theme(Base):
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    label = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("themes.id", ondelete="SET NULL"), nullable=True)

    parent = relationship("Theme", remote_side=[id], backref="sub_themes")
    livres = relationship("Livre", back_populates="theme")


class Auteur(Base):
    __tablename__ = "auteurs"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    nom = Column(String(255), nullable=False)
    co_auteur_id = Column(Integer, ForeignKey("auteurs.id", ondelete="SET NULL"), nullable=True)

    co_auteur = relationship("Auteur", remote_side=[id])
    livres = relationship("Livre", back_populates="auteur")


class Livre(Base):
    __tablename__ = "livres"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    titre = Column(String(255), nullable=False)
    isbn = Column(String(50), nullable=False)
    type_livre = Column(String(50), nullable=False, default="Livre")
    auteur_id = Column(Integer, ForeignKey("auteurs.id", ondelete="SET NULL"), nullable=True)
    theme_id = Column(Integer, ForeignKey("themes.id", ondelete="SET NULL"), nullable=True)

    auteur = relationship("Auteur", back_populates="livres")
    theme = relationship("Theme", back_populates="livres")
    exemplaires = relationship("Exemplaire", back_populates="livre", cascade="all, delete-orphan")


class Exemplaire(Base):
    __tablename__ = "exemplaires"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    code_barres = Column(String(50), unique=True, nullable=False)
    livre_id = Column(Integer, ForeignKey("livres.id", ondelete="CASCADE"), nullable=False)

    livre = relationship("Livre", back_populates="exemplaires")
    emprunts = relationship("Emprunt", back_populates="exemplaire")


class Abonne(Base):
    __tablename__ = "abonnes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    nom = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)

    emprunts = relationship("Emprunt", back_populates="abonne")


class Emprunt(Base):
    __tablename__ = "emprunts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    exemplaire_id = Column(Integer, ForeignKey("exemplaires.id", ondelete="CASCADE"), nullable=False)
    abonne_id = Column(Integer, ForeignKey("abonnes.id", ondelete="CASCADE"), nullable=False)
    date_emprunt = Column(Date, nullable=False)
    date_retour_prevue = Column(Date, nullable=False)
    jours_retard = Column(Integer, nullable=False, default=0)
    statut_emprunt = Column(String(50), nullable=True)
    penalite_euros = Column(Numeric(6, 2), nullable=True)

    exemplaire = relationship("Exemplaire", back_populates="emprunts")
    abonne = relationship("Abonne", back_populates="emprunts")
