from pathlib import Path

from library_owl_shacl_poc.engine import build_demo_graph
from library_owl_shacl_poc.visualization import (
    export_visualizations,
    generate_interactive_html,
    generate_mermaid_ontology,
)


def test_visualization_generation(tmp_path: Path):
    graph = build_demo_graph()

    mermaid_code = generate_mermaid_ontology(graph)
    assert "classDiagram" in mermaid_code
    assert "Livre" in mermaid_code
    assert "Emprunt" in mermaid_code
    assert "subClassOf" in mermaid_code

    html_path = generate_interactive_html(graph, tmp_path / "graph.html")
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "vis-network" in content
    assert "Médiathèque OWL 2 & SHACL" in content

    artifacts = export_visualizations(graph, tmp_path / "artifacts")
    assert artifacts["mermaid"].exists()
    assert artifacts["html"].exists()
