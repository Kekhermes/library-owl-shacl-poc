from pathlib import Path

from rdflib import Graph

from library_owl_shacl_poc.cli import main
from library_owl_shacl_poc.export import save_graph


def test_cli_execution(tmp_path: Path, capsys):
    out_file = tmp_path / "test-result.ttl"
    main(output_path=out_file)

    captured = capsys.readouterr()
    assert "Démonstration : Ontologie OWL 2 et Règles SHACL en Médiathèque" in captured.out
    assert "Validation SHACL : CONFORME" in captured.out
    assert "emprunt_alice" in captured.out
    assert "en règle" in captured.out
    assert "emprunt_bob" in captured.out
    assert "à relancer" in captured.out
    assert "emprunt_claire" in captured.out
    assert "critique" in captured.out
    assert out_file.exists()


def test_save_graph(tmp_path: Path):
    g = Graph()
    out = tmp_path / "sub" / "graph.ttl"
    result = save_graph(g, out)
    assert result.exists()
    assert result == out
