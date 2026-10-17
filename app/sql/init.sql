-- =============================================================================
-- Schéma relationnel PostgreSQL pour la Médiathèque (A-Box persistée)
-- =============================================================================

DROP TABLE IF EXISTS emprunts CASCADE;
DROP TABLE IF EXISTS exemplaires CASCADE;
DROP TABLE IF EXISTS livres CASCADE;
DROP TABLE IF EXISTS abonnes CASCADE;
DROP TABLE IF EXISTS auteurs CASCADE;
DROP TABLE IF EXISTS themes CASCADE;

-- 1. Thèmes documentaires
CREATE TABLE themes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    label VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES themes(id) ON DELETE SET NULL
);

-- 2. Auteurs
CREATE TABLE auteurs (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(255) NOT NULL,
    co_auteur_id INTEGER REFERENCES auteurs(id) ON DELETE SET NULL
);

-- 3. Livres / Documents
CREATE TABLE livres (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    titre VARCHAR(255) NOT NULL,
    isbn VARCHAR(50) UNIQUE NOT NULL,
    type_livre VARCHAR(50) NOT NULL DEFAULT 'Livre',
    auteur_id INTEGER REFERENCES auteurs(id) ON DELETE SET NULL,
    theme_id INTEGER REFERENCES themes(id) ON DELETE SET NULL
);

-- 4. Exemplaires physiques
CREATE TABLE exemplaires (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    code_barres VARCHAR(50) UNIQUE NOT NULL,
    livre_id INTEGER NOT NULL REFERENCES livres(id) ON DELETE CASCADE
);

-- 5. Abonnés inscrits
CREATE TABLE abonnes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- 6. Emprunts réels
CREATE TABLE emprunts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    exemplaire_id INTEGER NOT NULL REFERENCES exemplaires(id) ON DELETE CASCADE,
    abonne_id INTEGER NOT NULL REFERENCES abonnes(id) ON DELETE CASCADE,
    date_emprunt DATE NOT NULL,
    date_retour_prevue DATE NOT NULL,
    jours_retard INTEGER NOT NULL DEFAULT 0,
    statut_emprunt VARCHAR(50),
    penalite_euros NUMERIC(6, 2)
);

-- =============================================================================
-- Données initiales de démonstration (Correspondance exacte avec rdf/data.ttl)
-- =============================================================================

INSERT INTO themes (code, label, parent_id) VALUES
('theme_sciences', 'Sciences & Techniques', NULL),
('theme_informatique', 'Informatique', 1),
('theme_ontologies', 'Web Sémantique & Ontologies', 2);

INSERT INTO auteurs (code, nom, co_auteur_id) VALUES
('auteur_goscinny', 'René Goscinny', NULL),
('auteur_uderzo', 'Albert Uderzo', 1),
('auteur_berners_lee', 'Tim Berners-Lee', NULL);

-- Mise à jour symétrique du co-auteur pour Goscinny
UPDATE auteurs SET co_auteur_id = 2 WHERE code = 'auteur_goscinny';

INSERT INTO livres (code, titre, isbn, type_livre, auteur_id, theme_id) VALUES
('livre_asterix', 'Astérix le Gaulois', '978-2-01-210133-3', 'BandeDessinee', 1, 1),
('livre_ontologies', 'Le Web Sémantique et les Ontologies', '978-2-10-049876-5', 'Livre', 3, 3);

INSERT INTO exemplaires (code, code_barres, livre_id) VALUES
('exemplaire_ast_1', 'BC-AST-001', 1),
('exemplaire_ont_1', 'BC-ONT-001', 2),
('exemplaire_ont_2', 'BC-ONT-002', 2);

INSERT INTO abonnes (code, nom, email) VALUES
('abonne_alice', 'Alice Dupont', 'alice.dupont@example.org'),
('abonne_bob', 'Bob Martin', 'bob.martin@example.org'),
('abonne_claire', 'Claire Bernard', 'claire.bernard@example.org');

INSERT INTO emprunts (code, exemplaire_id, abonne_id, date_emprunt, date_retour_prevue, jours_retard, statut_emprunt, penalite_euros) VALUES
('emprunt_alice', 1, 1, '2026-10-01', '2026-10-21', 0, NULL, NULL),
('emprunt_bob', 2, 2, '2026-09-15', '2026-10-05', 3, NULL, NULL),
('emprunt_claire', 3, 3, '2026-09-01', '2026-09-22', 10, NULL, NULL);
