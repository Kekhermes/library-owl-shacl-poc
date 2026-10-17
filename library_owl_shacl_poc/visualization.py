import html
import json
from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

EX = Namespace("https://example.org/library#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def _local_name(uri: URIRef | str) -> str:
    """Extrait le nom local lisible d'un URI."""
    uri_str = str(uri)
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    return uri_str.rstrip("/").split("/")[-1]


def _get_label(graph: Graph, node: URIRef | str) -> str:
    """Renvoie le rdfs:label français ou le nom local d'un nœud."""
    labels = list(graph.objects(URIRef(str(node)), RDFS.label))
    for lbl in labels:
        if isinstance(lbl, Literal) and lbl.language == "fr":
            return str(lbl)
    if labels:
        return str(labels[0])
    return _local_name(node)


def _get_comment(graph: Graph, node: URIRef | str) -> str:
    """Renvoie le commentaire rdfs:comment ou une chaîne vide."""
    comments = list(graph.objects(URIRef(str(node)), RDFS.comment))
    for comment in comments:
        if isinstance(comment, Literal) and comment.language == "fr":
            return str(comment)
    if comments:
        return str(comments[0])
    return ""


def generate_mermaid_ontology(ontology_graph: Graph) -> str:
    """Génère la syntaxe Mermaid classDiagram pour l'ontologie OWL de médiathèque."""
    lines = [
        "classDiagram",
        "    direction LR",
    ]

    classes = sorted(
        set(ontology_graph.subjects(RDF.type, OWL.Class)),
        key=_local_name,
    )

    datatype_props = sorted(
        set(ontology_graph.subjects(RDF.type, OWL.DatatypeProperty)),
        key=_local_name,
    )
    class_attributes: dict[str, list[str]] = {cls: [] for cls in classes}
    for prop in datatype_props:
        domain = ontology_graph.value(prop, RDFS.domain)
        prop_range = ontology_graph.value(prop, RDFS.range)
        type_str = _local_name(prop_range) if prop_range else "string"
        name_str = _local_name(prop)
        if domain and domain in class_attributes:
            class_attributes[domain].append(f"+{type_str} {name_str}")

    for cls in classes:
        cls_name = _local_name(cls)
        lines.append(f"    class {cls_name} {{")
        for attr in class_attributes.get(cls, []):
            lines.append(f"        {attr}")
        lines.append("    }")

    for subclass, _, superclass in ontology_graph.triples((None, RDFS.subClassOf, None)):
        if (subclass, RDF.type, OWL.Class) in ontology_graph or isinstance(subclass, URIRef):
            sub_name = _local_name(subclass)
            super_name = _local_name(superclass)
            lines.append(f"    {super_name} <|-- {sub_name} : subClassOf")

    object_props = sorted(
        set(ontology_graph.subjects(RDF.type, OWL.ObjectProperty)),
        key=_local_name,
    )
    for prop in object_props:
        domain = ontology_graph.value(prop, RDFS.domain)
        prop_range = ontology_graph.value(prop, RDFS.range)
        prop_name = _local_name(prop)
        if domain and prop_range:
            dom_name = _local_name(domain)
            rng_name = _local_name(prop_range)
            lines.append(f"    {dom_name} --> {rng_name} : {prop_name}")

    return "\n".join(lines) + "\n"


def _build_vis_data(graph: Graph) -> dict[str, list[dict[str, Any]]]:
    """Construit les nœuds et arêtes pour la bibliothèque vis-network."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    # 1. Classes OWL (T-Box)
    classes = set(graph.subjects(RDF.type, OWL.Class))
    datatype_props = sorted(
        set(graph.subjects(RDF.type, OWL.DatatypeProperty)),
        key=_local_name,
    )
    class_attributes: dict[str, list[str]] = {str(cls): [] for cls in classes}
    for prop in datatype_props:
        domain = graph.value(prop, RDFS.domain)
        prop_range = graph.value(prop, RDFS.range)
        p_name = _local_name(prop)
        t_name = _local_name(prop_range) if prop_range else "Literal"
        if domain and str(domain) in class_attributes:
            class_attributes[str(domain)].append(f"+ {p_name} : {t_name}")

    for cls in classes:
        cls_id = str(cls)
        name = _local_name(cls)
        label = _get_label(graph, cls)
        comment = _get_comment(graph, cls)
        node_ids.add(cls_id)

        attrs = class_attributes.get(cls_id, [])
        attr_text = ("\n────────────\n" + "\n".join(attrs)) if attrs else ""
        display_label = f"«Class»\n{label}\n({name}){attr_text}"

        nodes.append({
            "id": cls_id,
            "label": display_label,
            "title": f"<b>Classe OWL :</b> {name}<br><b>Label :</b> {label}<br><b>URI :</b> {cls_id}<br>{comment}",
            "group": "tbox_class",
            "category": "tbox",
            "raw_name": name,
            "comment": comment,
            "shape": "box",
            "color": {"background": "#1e40af", "border": "#1d4ed8"},
            "font": {"color": "#ffffff", "face": "Inter, sans-serif", "bold": True},
        })

    # 2. Relations subClassOf (T-Box)
    for sub, _, sup in graph.triples((None, RDFS.subClassOf, None)):
        edges.append({
            "from": str(sub),
            "to": str(sup),
            "label": "subClassOf",
            "category": "tbox",
            "arrows": {"to": {"type": "triangle"}},
            "dashes": True,
            "color": {"color": "#60a5fa"},
            "font": {"background": "#0f172a", "color": "#93c5fd"},
        })

    # 3. Object Properties (T-Box)
    for prop in graph.subjects(RDF.type, OWL.ObjectProperty):
        domain = graph.value(prop, RDFS.domain)
        prop_range = graph.value(prop, RDFS.range)
        p_label = _get_label(graph, prop)
        p_comment = _get_comment(graph, prop)
        if domain and prop_range:
            edges.append({
                "from": str(domain),
                "to": str(prop_range),
                "label": p_label,
                "title": f"<b>ObjectProperty :</b> {_local_name(prop)}<br>{p_comment}",
                "category": "tbox",
                "arrows": "to",
                "color": {"color": "#38bdf8"},
                "font": {"background": "#0f172a", "color": "#7dd3fc"},
                "width": 2,
            })

    # 4. Individus / Faits (A-Box)
    individuals: set[URIRef] = set()
    for s, p, o in graph.triples((None, RDF.type, None)):
        if o not in (OWL.Class, OWL.Ontology, OWL.ObjectProperty, OWL.DatatypeProperty):
            if isinstance(s, URIRef):
                individuals.add(s)

    for ind in sorted(individuals, key=_local_name):
        ind_id = str(ind)
        name = _local_name(ind)
        label = _get_label(graph, ind)
        comment = _get_comment(graph, ind)
        types = [_local_name(t) for t in graph.objects(ind, RDF.type)]
        types_str = ", ".join(types)

        delays = list(graph.objects(ind, EX.joursRetard))
        delay_val = str(delays[0]) if delays else None

        statuts = list(graph.objects(ind, EX.statutEmprunt))
        statut_val = ", ".join([str(s) for s in statuts]) if statuts else None

        penalites = list(graph.objects(ind, EX.penaliteEuros))
        penalite_val = str(penalites[0]) if penalites else None

        titres = list(graph.objects(ind, EX.titre))
        titre_val = str(titres[0]) if titres else None

        details = [f"<b>Individu :</b> {name}", f"<b>Libellé :</b> {label}", f"<b>Type(s) :</b> {types_str}"]
        if titre_val:
            details.append(f"<b>Titre :</b> {titre_val}")
        if delay_val is not None:
            details.append(f"<b>Retard constaté :</b> {delay_val} jour(s)")
        if statut_val:
            details.append(f"<b>Statut calculé :</b> {statut_val}")
        if penalite_val is not None:
            details.append(f"<b>Pénalité calculée :</b> {penalite_val} €")

        node_color = "#059669"
        if "Emprunt" in types_str:
            if statut_val == "critique":
                node_color = "#dc2626"
            elif statut_val == "à relancer":
                node_color = "#ea580c"
            else:
                node_color = "#16a34a"
        elif "Abonne" in types_str:
            node_color = "#0284c7"
        elif "Livre" in types_str or "Document" in types_str:
            node_color = "#7c3aed"
        elif "Auteur" in types_str:
            node_color = "#d97706"

        node_ids.add(ind_id)
        nodes.append({
            "id": ind_id,
            "label": f"{label}\n({name})",
            "title": "<br>".join(details),
            "group": "abox_individual",
            "category": "abox",
            "raw_name": name,
            "comment": comment,
            "delay": delay_val,
            "statut": statut_val,
            "penalite": penalite_val,
            "types": types,
            "shape": "dot",
            "size": 22,
            "color": {"background": node_color, "border": "#ffffff"},
            "font": {"color": "#f8fafc", "face": "Inter, sans-serif"},
        })

        for t in graph.objects(ind, RDF.type):
            t_str = str(t)
            if t_str in node_ids:
                edges.append({
                    "from": ind_id,
                    "to": t_str,
                    "label": "rdf:type",
                    "category": "instance_of",
                    "arrows": "to",
                    "dashes": [2, 4],
                    "color": {"color": "#64748b"},
                    "font": {"background": "#0f172a", "color": "#94a3b8", "size": 10},
                })

    # 5. Relations entre individus (A-Box)
    for ind in individuals:
        ind_id = str(ind)
        for prop, target in graph.predicate_objects(ind):
            target_str = str(target)
            if isinstance(target, URIRef) and target_str in node_ids and prop != RDF.type:
                edges.append({
                    "from": ind_id,
                    "to": target_str,
                    "label": _local_name(prop),
                    "category": "abox",
                    "arrows": "to",
                    "color": {"color": "#34d399"},
                    "font": {"background": "#0f172a", "color": "#6ee7b7", "size": 11},
                    "width": 1.5,
                })

    return {"nodes": nodes, "edges": edges}


def generate_interactive_html(graph: Graph, destination: str | Path) -> Path:
    """Génère une page HTML autonome avec Vis.js pour visualiser l'ontologie de la médiathèque."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = _build_vis_data(graph)
    data_json = json.dumps(data, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualisation Sémantique : Médiathèque OWL 2 & SHACL</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --border: #475569;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        #sidebar {{
            width: 380px;
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            z-index: 10;
            box-shadow: 4px 0 16px rgba(0,0,0,0.4);
        }}
        #header {{
            padding: 1.25rem;
            border-bottom: 1px solid var(--border);
        }}
        #header h1 {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.35rem;
        }}
        #header p {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.35;
        }}
        #controls {{
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        .control-group-title {{
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            font-weight: 700;
        }}
        .btn-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }}
        .filter-btn {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.4rem 0.75rem;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .filter-btn.active {{
            background: var(--accent);
            color: #0f172a;
            border-color: var(--accent);
            font-weight: 700;
        }}
        .search-box {{
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            font-size: 0.82rem;
        }}
        #details-pane {{
            flex: 1;
            padding: 1.25rem;
            overflow-y: auto;
        }}
        .card {{
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .card h3 {{
            font-size: 0.95rem;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }}
        .card-row {{
            margin-bottom: 0.4rem;
            font-size: 0.82rem;
            line-height: 1.4;
        }}
        .card-label {{
            color: var(--text-secondary);
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-regle {{ background: #065f46; color: #a7f3d0; }}
        .badge-relancer {{ background: #9a3412; color: #fed7aa; }}
        .badge-critique {{ background: #991b1b; color: #fecaca; }}
        #network-container {{
            flex: 1;
            height: 100%;
            position: relative;
        }}
        #legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(30, 41, 59, 0.92);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.85rem 1.1rem;
            font-size: 0.75rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}
        .legend-bullet {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .legend-box {{
            width: 14px;
            height: 10px;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div id="header">
            <h1>Médiathèque OWL 2 & SHACL</h1>
            <p>Visualisation interactive de la T-Box (vocabulaire & axiomes) et de l'A-Box (faits & inférences).</p>
        </div>
        <div id="controls">
            <div class="control-group-title">Filtres de vision</div>
            <div class="btn-group">
                <button class="filter-btn active" onclick="setFilter('all')">Tout</button>
                <button class="filter-btn" onclick="setFilter('tbox')">T-Box (Classes)</button>
                <button class="filter-btn" onclick="setFilter('abox')">A-Box (Faits)</button>
                <button class="filter-btn" onclick="setFilter('loans')">Emprunts seuls</button>
            </div>
            <input type="text" id="search" class="search-box" placeholder="Rechercher une ressource..." oninput="handleSearch()">
        </div>
        <div id="details-pane">
            <div class="card">
                <h3>Guide d'inspection</h3>
                <p class="card-row">Cliquez sur un nœud pour afficher ses propriétés, attributs et valeurs inférées par SHACL.</p>
            </div>
            <div id="selected-info"></div>
        </div>
    </div>
    <div id="network-container">
        <div id="legend">
            <div class="legend-item"><span class="legend-box" style="background: #1e40af;"></span> Classe OWL (T-Box)</div>
            <div class="legend-item"><span class="legend-bullet" style="background: #16a34a;"></span> Emprunt en règle (0 j)</div>
            <div class="legend-item"><span class="legend-bullet" style="background: #ea580c;"></span> Emprunt à relancer (3 j)</div>
            <div class="legend-item"><span class="legend-bullet" style="background: #dc2626;"></span> Emprunt critique (10 j)</div>
            <div class="legend-item"><span class="legend-bullet" style="background: #0284c7;"></span> Abonné inscrit</div>
            <div class="legend-item"><span class="legend-bullet" style="background: #7c3aed;"></span> Document / Livre</div>
        </div>
    </div>

    <script>
        const rawData = {data_json};
        let network = null;
        let activeFilter = 'all';

        function buildDataSet(filter) {{
            let filteredNodes = rawData.nodes;
            if (filter === 'tbox') {{
                filteredNodes = rawData.nodes.filter(n => n.category === 'tbox');
            }} else if (filter === 'abox') {{
                filteredNodes = rawData.nodes.filter(n => n.category === 'abox');
            }} else if (filter === 'loans') {{
                filteredNodes = rawData.nodes.filter(n => n.types && n.types.includes('Emprunt') || n.raw_name === 'Emprunt');
            }}

            const visibleIds = new Set(filteredNodes.map(n => n.id));
            const filteredEdges = rawData.edges.filter(e => visibleIds.has(e.from) && visibleIds.has(e.to));

            return {{
                nodes: new vis.DataSet(filteredNodes),
                edges: new vis.DataSet(filteredEdges)
            }};
        }}

        function initNetwork() {{
            const container = document.getElementById('network-container');
            const data = buildDataSet('all');
            const options = {{
                physics: {{
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {{
                        gravitationalConstant: -70,
                        centralGravity: 0.015,
                        springLength: 120,
                        springConstant: 0.08
                    }},
                    maxVelocity: 50,
                    minVelocity: 0.1,
                    stabilization: {{ iterations: 150 }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 100,
                    navigationButtons: true
                }}
            }};

            network = new vis.Network(container, data, options);

            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    showDetails(nodeId);
                }}
            }});
        }}

        function showDetails(nodeId) {{
            const node = rawData.nodes.find(n => n.id === nodeId);
            if (!node) return;

            const pane = document.getElementById('selected-info');
            let badgeHtml = '';
            if (node.statut === 'en règle') {{
                badgeHtml = '<span class="badge badge-regle">En règle</span>';
            }} else if (node.statut === 'à relancer') {{
                badgeHtml = '<span class="badge badge-relancer">À relancer</span>';
            }} else if (node.statut === 'critique') {{
                badgeHtml = '<span class="badge badge-critique">Critique</span>';
            }}

            pane.innerHTML = `
                <div class="card">
                    <h3>${{node.raw_name}} ${{badgeHtml}}</h3>
                    <div class="card-row"><span class="card-label">Label :</span> ${{node.label.split('\\n')[0]}}</div>
                    <div class="card-row"><span class="card-label">Catégorie :</span> ${{node.category.toUpperCase()}}</div>
                    ${{node.comment ? `<div class="card-row"><span class="card-label">Description :</span> ${{node.comment}}</div>` : ''}}
                    ${{node.delay !== undefined && node.delay !== null ? `<div class="card-row"><span class="card-label">Retard :</span> ${{node.delay}} jour(s)</div>` : ''}}
                    ${{node.statut ? `<div class="card-row"><span class="card-label">Statut calculé :</span> ${{node.statut}}</div>` : ''}}
                    ${{node.penalite !== undefined && node.penalite !== null ? `<div class="card-row"><span class="card-label">Pénalité calculée :</span> ${{node.penalite}} €</div>` : ''}}
                    <div class="card-row" style="margin-top: 0.5rem; word-break: break-all; font-size: 0.72rem; color: var(--text-secondary);">
                        <b>URI :</b> ${{node.id}}
                    </div>
                </div>
            `;
        }}

        function setFilter(filter) {{
            activeFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            const data = buildDataSet(filter);
            network.setData(data);
        }}

        function handleSearch() {{
            const query = document.getElementById('search').value.toLowerCase().trim();
            if (!query) return;
            const match = rawData.nodes.find(n => n.raw_name.toLowerCase().includes(query) || (n.label && n.label.toLowerCase().includes(query)));
            if (match && network) {{
                network.focus(match.id, {{ scale: 1.2, animation: true }});
                network.selectNodes([match.id]);
                showDetails(match.id);
            }}
        }}

        window.onload = initNetwork;
    </script>
</body>
</html>
"""
    path.write_text(html_content, encoding="utf-8")
    return path


def export_visualizations(
    graph: Graph,
    output_dir: str | Path = "artifacts",
) -> dict[str, Path]:
    """Génère et sauvegarde le diagramme Mermaid et la page HTML interactive."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    mermaid_content = generate_mermaid_ontology(graph)
    mermaid_path = out / "ontology.mmd"
    mermaid_path.write_text(mermaid_content, encoding="utf-8")

    html_path = generate_interactive_html(graph, out / "ontology-graph.html")

    return {
        "mermaid": mermaid_path,
        "html": html_path,
    }


def cli() -> None:
    """CLI autonome pour générer uniquement les visualisations."""
    from .engine import build_demo_graph

    graph = build_demo_graph()
    artifacts = export_visualizations(graph)
    print(f"diagramme Mermaid enregistré: {artifacts['mermaid']}")
    print(f"visualisation interactive HTML enregistrée: {artifacts['html']}")


if __name__ == "__main__":
    cli()
