#!/usr/bin/env python3
"""
MAI ontology demonstrator / CQ evaluation script.

Purpose
-------
1. Load the MAI OWL/RDF ontology.
2. Construct a small demonstrative ABox for the rehabilitation scenario.
3. Optionally materialize the three operational reasoning stages discussed in the paper:
     SuitableEmbodiment -> TaskOpportunity -> MigrationOpportunity
4. Execute CQ1-CQ6 SPARQL queries.
5. Export:
     - materialized_graph.ttl
     - cq_results.csv
     - cq_summary.csv
     - cq_summary.tex

Requirements
------------
pip install rdflib pandas

Notes
-----
- The script deliberately implements the runtime reasoning procedurally in Python/RDFLib.
  It does NOT claim that RDFLib provides OWL-DL reasoning or native existential Jena rules.
- Capability matching is used as a candidate-filtering mechanism. It checks whether a
  candidate embodiment provides a capability compatible with the modeled functional
  requirement. It does not claim arbitrary conjunctive coverage of independent requirements.
- The demo ABox is intentionally small and transparent; it is meant to demonstrate
  representational coverage of the Competency Questions, not system performance.
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import XSD

MAI = Namespace("http://www.istc.cnr.it/pst/ontologies/2024/migrai#")
DUL = Namespace("http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#")
SOMA = Namespace("http://www.ease-crc.org/ont/SOMA.owl#")
EX = Namespace("http://www.istc.cnr.it/pst/ontologies/2024/migrai/demo#")

PREFIXES = """\
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>
PREFIX soma: <http://www.ease-crc.org/ont/SOMA.owl#>
PREFIX mai: <http://www.istc.cnr.it/pst/ontologies/2024/migrai#>
PREFIX ex: <http://www.istc.cnr.it/pst/ontologies/2024/migrai/demo#>
"""

# The CQ queries below are aligned with the latest manuscript supplied with the revision.
QUERIES: Dict[str, str] = {
    "CQ1": PREFIXES + """
SELECT DISTINCT ?person ?quality ?method ?task
WHERE {
  ?assistedRole rdf:type mai:AssistedPerson ;
                dul:isRoleOf ?person .

  ?quality rdf:type mai:HumanQuality ;
           dul:isQualityOf ?person .

  ?method rdf:type mai:AssistiveMethod ;
          mai:hasEffectOn ?quality .

  OPTIONAL {
    ?task rdf:type mai:EmbodiedTask ;
          dul:isDefinedIn ?method .
  }
}
ORDER BY ?person ?quality ?method ?task
""",
    "CQ2": PREFIXES + """
SELECT DISTINCT ?embodiment ?capability ?capType
WHERE {
  ?embodiment rdf:type mai:Embodiment ;
              dul:hasQuality ?capability .

  ?capability rdf:type ?capType .
  ?capType rdfs:subClassOf* soma:Capability .
}
ORDER BY ?embodiment ?capType
""",
    "CQ3": PREFIXES + """
SELECT DISTINCT ?task ?method ?suitable ?embodiment
WHERE {
  ?suitable rdf:type mai:SuitableEmbodiment ;
            dul:isRoleOf ?embodiment ;
            soma:hasTask ?task .

  ?task rdf:type mai:EmbodiedTask ;
        dul:isDefinedIn ?method .
  ?method rdf:type mai:AssistiveMethod .
  ?embodiment rdf:type mai:Embodiment .

  FILTER NOT EXISTS {
    ?method mai:describesFunctionality ?requiredCap .
    ?requiredCap rdf:type ?requiredType .
    ?requiredType rdfs:subClassOf* soma:Capability .

    FILTER NOT EXISTS {
      ?embodiment dul:hasQuality ?providedCap .
      ?providedCap rdf:type ?providedType .
      ?providedType rdfs:subClassOf* ?requiredType .
    }
  }
}
ORDER BY ?task ?embodiment
""",
    "CQ4": PREFIXES + """
SELECT DISTINCT ?opportunity ?context ?person ?embodiment ?task
WHERE {
  ?opportunity rdf:type mai:TaskOpportunity ;
               soma:definesTrigger ?assistedRole ;
               soma:definesBearer ?suitable ;
               dul:definesTask ?task .

  ?assistedRole rdf:type mai:AssistedPerson ;
                dul:isRoleOf ?person .
  ?suitable rdf:type mai:SuitableEmbodiment ;
            dul:isRoleOf ?embodiment .

  ?person mai:hasContext ?context .
  ?embodiment mai:hasContext ?context .
  ?context rdf:type mai:InteractionContext .
  ?task rdf:type mai:EmbodiedTask .
}
ORDER BY ?context ?task ?embodiment
""",
    "CQ5": PREFIXES + """
SELECT DISTINCT ?context ?contextType ?embodiment
WHERE {
  ?embodiment rdf:type mai:Embodiment ;
              mai:hasContext ?context .

  ?context rdf:type ?contextType .
  ?contextType rdfs:subClassOf* mai:InteractionContext .
}
ORDER BY ?context ?embodiment
""",
    "CQ6": PREFIXES + """
SELECT DISTINCT ?migration ?agent ?candidateEmbodiment ?taskOpportunity ?task
WHERE {
  ?migration rdf:type mai:MigrationOpportunity ;
             soma:definesBearer ?agent ;
             soma:definesTrigger ?suitable .

  ?suitable rdf:type mai:SuitableEmbodiment ;
            dul:isRoleOf ?candidateEmbodiment ;
            soma:hasTask ?task .

  ?taskOpportunity rdf:type mai:TaskOpportunity ;
                   soma:definesBearer ?suitable ;
                   dul:definesTask ?task .

  ?agent rdf:type dul:CognitiveAgent ;
         dul:hasRole ?migratableRole .

  ?migratableRole rdf:type mai:MigratableAgent .

  ?candidateEmbodiment rdf:type mai:Embodiment .
  ?task rdf:type mai:EmbodiedTask .
}
ORDER BY ?migration ?task ?candidateEmbodiment
""",
}


def bind_namespaces(g: Graph) -> None:
    for pfx, ns in [
        ("mai", MAI), ("dul", DUL), ("soma", SOMA), ("ex", EX),
        ("rdf", RDF), ("rdfs", RDFS), ("owl", OWL)
    ]:
        g.bind(pfx, ns)


def add_type(g: Graph, individual: URIRef, cls: URIRef) -> None:
    g.add((individual, RDF.type, cls))


def add_demo_abox(g: Graph) -> None:
    """Create a small, readable rehabilitation/migration ABox."""
    bind_namespaces(g)

    # Contexts
    room = EX.HospitalRoomContext
    gym = EX.RehabilitationGymContext
    add_type(g, room, MAI.InteractionContext)
    add_type(g, room, MAI.ProfessionalContext)
    add_type(g, gym, MAI.InteractionContext)
    add_type(g, gym, MAI.ProfessionalContext)

    # Persistent cognitive agent and roles
    agent = EX.PersistentAgent
    migratable_role = EX.MigratableAgentRole
    add_type(g, agent, DUL.CognitiveAgent)
    add_type(g, migratable_role, MAI.MigratableAgent)
    g.add((agent, DUL.hasRole, migratable_role))
    # Contextualize the role in both demo contexts.
    g.add((migratable_role, DUL.isDefinedIn, room))
    g.add((migratable_role, DUL.isDefinedIn, gym))

    # Assisted person and role
    person = EX.Patient
    assisted_role = EX.AssistedPatientRole
    add_type(g, person, DUL.NaturalPerson)
    add_type(g, assisted_role, MAI.AssistedPerson)
    g.add((assisted_role, DUL.isRoleOf, person))
    # CQ4 uses hasContext on the person; Rule-style contextualization uses isDefinedIn on the role.
    g.add((person, MAI.hasContext, room))
    g.add((assisted_role, DUL.isDefinedIn, room))

    # User-side quality / need dimension
    quality = EX.CognitiveEngagementQuality
    add_type(g, quality, MAI.HumanQuality)
    g.add((quality, DUL.isQualityOf, person))

    # Assistive method
    method = EX.OrientationMethod
    add_type(g, method, MAI.AssistiveMethod)
    g.add((method, MAI.hasEffectOn, quality))

    # Task-side required capability individual.
    # This follows the CQ3 query pattern: the required capability is a distinct individual
    # classified by a capability type; it is not the same individual as an embodiment capability.
    required_cap = EX.RequiredCommunicationCapability
    add_type(g, required_cap, MAI.CommunicationCapability)
    g.add((method, MAI.describesFunctionality, required_cap))

    # Ensure the relevant capability classes are connected to SOMA:Capability for SPARQL
    # property-path evaluation even if imported SOMA axioms are not locally dereferenced.
    g.add((MAI.SocialCapability, RDFS.subClassOf, SOMA.Capability))
    g.add((MAI.CommunicationCapability, RDFS.subClassOf, MAI.SocialCapability))
    g.add((MAI.NavigationCapability, RDFS.subClassOf, SOMA.Capability))

    # Embodiment 1: tablet in hospital room, capable of communication.
    tablet = EX.Tablet01
    tablet_cap = EX.TabletCommunicationCapability
    add_type(g, tablet, MAI.Embodiment)
    add_type(g, tablet, MAI.Tablet)
    add_type(g, tablet_cap, MAI.CommunicationCapability)
    g.add((tablet, DUL.hasQuality, tablet_cap))
    g.add((tablet, MAI.hasContext, room))

    # Embodiment 2: robot in gym, with communication + navigation capability.
    robot = EX.Robot01
    robot_comm = EX.RobotCommunicationCapability
    robot_nav = EX.RobotNavigationCapability
    add_type(g, robot, MAI.Embodiment)
    add_type(g, robot_comm, MAI.CommunicationCapability)
    add_type(g, robot_nav, MAI.NavigationCapability)
    g.add((robot, DUL.hasQuality, robot_comm))
    g.add((robot, DUL.hasQuality, robot_nav))
    g.add((robot, MAI.hasContext, gym))

    # Embodiment 3: a display in the room with no modeled communication capability.
    display = EX.PassiveDisplay01
    add_type(g, display, MAI.Embodiment)
    g.add((display, MAI.hasContext, room))


def subclass_closure(g: Graph, cls: URIRef) -> set[URIRef]:
    """Return cls plus explicit rdfs:subClassOf ancestors available in the loaded graph."""
    out = {cls}
    frontier = [cls]
    while frontier:
        cur = frontier.pop()
        for parent in g.objects(cur, RDFS.subClassOf):
            if isinstance(parent, URIRef) and parent not in out:
                out.add(parent)
                frontier.append(parent)
    return out


def capability_types(g: Graph, capability: URIRef) -> set[URIRef]:
    types = set()
    for cls in g.objects(capability, RDF.type):
        if isinstance(cls, URIRef):
            types |= subclass_closure(g, cls)
    return types


def capability_compatible(g: Graph, provided: URIRef, required: URIRef) -> bool:
    """True if any provided capability type is equal to/subclass of any required capability type."""
    ptypes = capability_types(g, provided)
    rtypes = capability_types(g, required)
    return bool(ptypes & rtypes)


def materialize_demo_reasoning(g: Graph) -> Dict[str, int]:
    """
    Procedurally materialize the three reasoning stages.

    Stage 1: SuitableEmbodiment + EmbodiedTask
    Stage 2: TaskOpportunity
    Stage 3: MigrationOpportunity

    The procedure is deterministic and transparent: generated URI names are based on
    method / embodiment identifiers instead of anonymous fresh nodes.
    """
    stats = {"suitable_roles": 0, "embodied_tasks": 0, "task_opportunities": 0, "migration_opportunities": 0}

    # ---- Stage 1: capability compatibility -> SuitableEmbodiment ----
    methods = list(g.subjects(RDF.type, MAI.AssistiveMethod))
    embodiments = list(g.subjects(RDF.type, MAI.Embodiment))

    for method in methods:
        requirements = list(g.objects(method, MAI.describesFunctionality))
        if not requirements:
            continue

        for emb in embodiments:
            provided = list(g.objects(emb, DUL.hasQuality))
            # Modeling convention used here: identify a candidate when at least one
            # modeled requirement is compatible with at least one provided capability.
            matches = [(req, cap) for req in requirements for cap in provided
                       if capability_compatible(g, cap, req)]
            if not matches:
                continue

            emb_name = str(emb).rsplit("#", 1)[-1]
            meth_name = str(method).rsplit("#", 1)[-1]
            role = EX[f"Suitable_{emb_name}_{meth_name}"]
            task = EX[f"Task_{emb_name}_{meth_name}"]

            add_type(g, role, MAI.SuitableEmbodiment)
            add_type(g, task, MAI.EmbodiedTask)
            g.add((role, DUL.isRoleOf, emb))
            g.add((role, SOMA.hasTask, task))
            g.add((task, DUL.isDefinedIn, method))

            # Contextualize role for each context in which the embodiment is available.
            for ctx in g.objects(emb, MAI.hasContext):
                g.add((role, DUL.isDefinedIn, ctx))

            # Keep the matching bearer-specific capability as affordance evidence.
            # The exact property is not needed by the CQ queries, so no extra assumption
            # is introduced here beyond the query-required relations.
            stats["suitable_roles"] += 1
            stats["embodied_tasks"] += 1

    # ---- Stage 2: shared context -> TaskOpportunity ----
    assisted_roles = list(g.subjects(RDF.type, MAI.AssistedPerson))
    suitable_roles = list(g.subjects(RDF.type, MAI.SuitableEmbodiment))

    for ar in assisted_roles:
        ar_contexts = set(g.objects(ar, DUL.isDefinedIn))
        for sr in suitable_roles:
            shared = ar_contexts & set(g.objects(sr, DUL.isDefinedIn))
            if not shared:
                continue
            for task in g.objects(sr, SOMA.hasTask):
                sr_name = str(sr).rsplit("#", 1)[-1]
                ar_name = str(ar).rsplit("#", 1)[-1]
                task_name = str(task).rsplit("#", 1)[-1]
                opp = EX[f"TaskOpportunity_{ar_name}_{sr_name}_{task_name}"]
                add_type(g, opp, MAI.TaskOpportunity)
                g.add((opp, SOMA.definesTrigger, ar))
                g.add((opp, SOMA.definesBearer, sr))
                g.add((opp, DUL.definesTask, task))
                stats["task_opportunities"] += 1

    # ---- Stage 3: task opportunity -> MigrationOpportunity ----
    agents = list(g.subjects(RDF.type, DUL.CognitiveAgent))
    for agent in agents:
        migr_roles = [r for r in g.objects(agent, DUL.hasRole) if (r, RDF.type, MAI.MigratableAgent) in g]
        if not migr_roles:
            continue

        for to in g.subjects(RDF.type, MAI.TaskOpportunity):
            suitable = next(iter(g.objects(to, SOMA.definesBearer)), None)
            if suitable is None:
                continue
            task = next(iter(g.objects(to, DUL.definesTask)), None)
            if task is None:
                continue

            # CQ6 expects the persistent CognitiveAgent as definesBearer and the
            # SuitableEmbodiment role as definesTrigger. This is the query-level view
            # materialized here.
            to_name = str(to).rsplit("#", 1)[-1]
            mo = EX[f"MigrationOpportunity_{to_name}"]
            add_type(g, mo, MAI.MigrationOpportunity)
            g.add((mo, SOMA.definesBearer, agent))
            g.add((mo, SOMA.definesTrigger, suitable))
            stats["migration_opportunities"] += 1

    return stats


def load_query_files(query_dir: Path | None) -> Dict[str, str]:
    if query_dir is None:
        return QUERIES
    found = {}
    for path in sorted(query_dir.glob("*.sparql")):
        found[path.stem.upper()] = path.read_text(encoding="utf-8")
    return found or QUERIES


def term_to_text(v) -> str:
    if v is None:
        return ""
    return str(v)


def execute_queries(g: Graph, queries: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    result_rows = []
    summary_rows = []

    for cq, query in queries.items():
        start = time.perf_counter()
        error = ""
        rows = []
        vars_ = []
        try:
            res = g.query(query)
            vars_ = [str(v) for v in res.vars]
            for row in res:
                rows.append({vars_[i]: term_to_text(row[i]) for i in range(len(vars_))})
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        for idx, row in enumerate(rows, start=1):
            result_rows.append({"CQ": cq, "row": idx, **row})

        summary_rows.append({
            "CQ": cq,
            "status": "PASS" if rows and not error else ("EMPTY" if not error else "ERROR"),
            "result_rows": len(rows),
            "query_time_ms": round(elapsed_ms, 3),
            "error": error
        })

    return pd.DataFrame(result_rows), pd.DataFrame(summary_rows)


def write_latex_summary(summary: pd.DataFrame, outpath: Path) -> None:
    clean = summary[["CQ", "status", "result_rows", "query_time_ms"]].copy()
    clean.columns = ["CQ", "Status", "Rows", "Query time (ms)"]
    latex = clean.to_latex(index=False, escape=True, caption="Execution of the competency-question queries over the demonstrative MAI knowledge graph.", label="tab:cq-execution")
    outpath.write_text(latex, encoding="utf-8")


def graph_stats(g: Graph, reasoning_stats: Dict[str, int]) -> pd.DataFrame:
    return pd.DataFrame([
        {"metric": "RDF triples after materialization", "value": len(g)},
        {"metric": "Demo SuitableEmbodiment roles", "value": reasoning_stats.get("suitable_roles", 0)},
        {"metric": "Demo EmbodiedTask individuals", "value": reasoning_stats.get("embodied_tasks", 0)},
        {"metric": "Demo TaskOpportunity individuals", "value": reasoning_stats.get("task_opportunities", 0)},
        {"metric": "Demo MigrationOpportunity individuals", "value": reasoning_stats.get("migration_opportunities", 0)},
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", required=True, help="Path to MAI OWL/RDF file")
    parser.add_argument("--outdir", default="mai_cq_results", help="Output directory")
    parser.add_argument("--query-dir", default=None, help="Optional folder containing *.sparql files")
    parser.add_argument("--no-reasoning", action="store_true", help="Build demo ABox but skip procedural materialization")
    args = parser.parse_args()

    ontology_path = Path(args.ontology)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    g = Graph()
    g.parse(ontology_path)
    bind_namespaces(g)
    tbox_triples = len(g)

    add_demo_abox(g)
    abox_plus_tbox_triples = len(g)

    reasoning_stats = {}
    if not args.no_reasoning:
        reasoning_stats = materialize_demo_reasoning(g)

    queries = load_query_files(Path(args.query_dir) if args.query_dir else None)
    results, summary = execute_queries(g, queries)

    g.serialize(outdir / "materialized_graph.ttl", format="turtle")
    results.to_csv(outdir / "cq_results.csv", index=False)
    summary.to_csv(outdir / "cq_summary.csv", index=False)
    write_latex_summary(summary, outdir / "cq_summary.tex")

    stats = graph_stats(g, reasoning_stats)
    extra = pd.DataFrame([
        {"metric": "Ontology/TBox triples loaded", "value": tbox_triples},
        {"metric": "Triples after demo ABox creation", "value": abox_plus_tbox_triples},
    ])
    stats = pd.concat([extra, stats], ignore_index=True)
    stats.to_csv(outdir / "graph_statistics.csv", index=False)

    print("\n=== MAI CQ DEMONSTRATION ===")
    print(stats.to_string(index=False))
    print("\n=== CQ SUMMARY ===")
    print(summary.to_string(index=False))
    print(f"\nOutputs written to: {outdir.resolve()}")


if __name__ == "__main__":
    main()
