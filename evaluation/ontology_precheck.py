#!/usr/bin/env python3
"""Local structural pre-screen for the MAI namespace.

This script does NOT claim to execute the OOPS! scanner. It checks a subset of
structural conditions corresponding to OOPS! pitfall definitions that can be
reproduced directly from the RDF graph: P04, P06, P08, P11 and P19.
"""
from pathlib import Path
from collections import defaultdict
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Namespace

HERE = Path(__file__).resolve().parent
ONTOLOGY = HERE.parent / "MigrAI_v0.2.rdf"
MAI = Namespace("http://www.istc.cnr.it/pst/ontologies/2024/migrai#")

g = Graph()
g.parse(str(ONTOLOGY))

classes = sorted({c for c in g.subjects(RDF.type, OWL.Class)
                  if isinstance(c, URIRef) and str(c).startswith(str(MAI))}, key=str)
props = sorted({p for p in g.subjects(RDF.type, OWL.ObjectProperty)
                if isinstance(p, URIRef) and str(p).startswith(str(MAI))}, key=str)
entities = classes + props

# P04-like unconnected entities (ignore type/annotation-only triples)
ignored = {RDF.type, RDFS.label, RDFS.comment}
unconnected = []
for e in entities:
    linked = any(p not in ignored for p, _ in g.predicate_objects(e)) or \
             any(p not in ignored for _, p in g.subject_predicates(e))
    if not linked:
        unconnected.append(e)

# P06-like cycles in named class hierarchy
edges = defaultdict(set)
for c in classes:
    for sup in g.objects(c, RDFS.subClassOf):
        if isinstance(sup, URIRef):
            edges[c].add(sup)

def has_cycle():
    visiting, visited = set(), set()
    def dfs(n):
        if n in visiting: return True
        if n in visited: return False
        visiting.add(n)
        for m in edges.get(n, ()):
            if dfs(m): return True
        visiting.remove(n); visited.add(n)
        return False
    return any(dfs(n) for n in list(edges))

# P08-like entities without human-readable annotation
no_ann = [e for e in entities
          if not list(g.objects(e, RDFS.label)) and not list(g.objects(e, RDFS.comment))]

# P11-like missing domain/range for MAI properties
missing_dr = []
for p in props:
    dom = list(g.objects(p, RDFS.domain))
    ran = list(g.objects(p, RDFS.range))
    if not dom or not ran:
        missing_dr.append((p, bool(dom), bool(ran)))

# P19-like multiple domain/range statements
multi_dr = []
for p in props:
    dom = list(g.objects(p, RDFS.domain))
    ran = list(g.objects(p, RDFS.range))
    if len(dom) > 1 or len(ran) > 1:
        multi_dr.append((p, len(dom), len(ran)))

name = lambda x: str(x).split('#')[-1]
print(f"Triples: {len(g)}")
print(f"MAI classes: {len(classes)}")
print(f"MAI object properties: {len(props)}")
print(f"P04-like unconnected elements: {len(unconnected)}")
print(f"P06-like named hierarchy cycle: {'YES' if has_cycle() else 'NO'}")
print(f"P08-like missing label/comment: {len(no_ann)} / {len(entities)}")
print("P11-like missing domain/range:")
for p, has_dom, has_ran in missing_dr:
    print(f"  - {name(p)}: domain={'yes' if has_dom else 'no'}, range={'yes' if has_ran else 'no'}")
print(f"P19-like multiple domain/range: {len(multi_dr)}")
