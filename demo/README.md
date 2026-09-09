# MAI Demonstration — Small Knowledge Graph

This folder contains a compact, reproducible demonstration of the competency-question evaluation reported for the MAI ontology.

The objective is not to benchmark reasoning performance or to reproduce a complete assistive deployment. Instead, the example shows how the ontology can be instantiated with a small ABox, how selected runtime knowledge can be materialized from the modeled relations, and how the six competency questions (CQ1–CQ6) can be executed over the resulting graph.

## Contents

The `small` demonstration contains:

- `mai_cq_demonstrator.py` — Python script that loads the MAI ontology, creates the demonstrative ABox, materializes the migration-related knowledge, executes the SPARQL competency questions, and exports the results.
- `materialized_graph.ttl` — Turtle serialization of the ontology plus the demonstrative ABox and the materialized assertions.
- `cq_results.csv` — detailed rows returned by the CQ queries.
- `cq_summary.csv` — compact summary containing query status, number of returned rows, and execution time.
- `cq_summary.tex` — LaTeX table generated from the CQ summary.
- `graph_statistics.csv` — statistics describing graph size before and after ABox construction and materialization.

The script can also load external `.sparql` files through the optional `--query-dir` argument. If no query directory is supplied, the six queries corresponding to the manuscript are embedded in the script.

## Requirements

The demonstration requires Python 3 and the following packages:

```bash
pip install rdflib pandas
```

## Running the demonstration

From the repository root, assuming the ontology file is available as `MigrAI_v0.2.rdf`, run:

```bash
python demo/small/mai_cq_demonstrator.py \
    --ontology MigrAI_v0.2.rdf \
    --outdir demo/small/results
```

To execute query files stored in a directory instead of the queries embedded in the script:

```bash
python demo/small/mai_cq_demonstrator.py \
    --ontology MigrAI_v0.2.rdf \
    --query-dir evaluation/queries \
    --outdir demo/small/results
```

The script writes the materialized graph and all result tables to the selected output directory.

## Demonstrative knowledge graph

The example starts from the MAI ontology and adds a small ABox inspired by the rehabilitation scenario described in the paper. It contains:

- one persistent cognitive agent and its `MigratableAgent` role;
- one assisted person and corresponding assisted-person role;
- two interaction contexts;
- one assistive method and one relevant human quality;
- multiple physical embodiments with different bearer-specific capability individuals.

The example intentionally includes embodiments with different functional and contextual characteristics so that the reasoning process can distinguish generic availability from functional suitability and context-dependent task realization.

The initial ontology contains 378 RDF triples. After adding the demonstrative ABox, the graph contains 412 triples. The materialization phase expands the graph to 431 triples.

The runtime layer creates:

- 2 `SuitableEmbodiment` roles;
- 2 `EmbodiedTask` individuals;
- 1 `TaskOpportunity`;
- 1 `MigrationOpportunity`.

These assertions reproduce the three reasoning stages discussed in the paper:

1. capability-based identification of candidate embodiments;
2. contextualization of suitable performers into task opportunities;
3. derivation of migration opportunities from available task opportunities.

## Competency-question results

The six competency questions all return non-empty results on the demonstrative graph:

| CQ | Status | Result rows |
|---|---|---:|
| CQ1 | PASS | 2 |
| CQ2 | PASS | 3 |
| CQ3 | PASS | 2 |
| CQ4 | PASS | 1 |
| CQ5 | PASS | 6 |
| CQ6 | PASS | 1 |

The result cardinalities are deliberately small because the demonstration is designed for inspectability rather than scale.

The queries illustrate the intended progression from user-related functional information and embodiment capabilities to functional suitability, contextual task opportunities, contextual availability, and migration opportunities.

## Reasoning scope

The materialization implemented in this script is procedural and deliberately lightweight.

It is intended to reproduce the operational knowledge-graph transformations described in the paper, rather than to provide a complete OWL-DL reasoner or a literal implementation of SWRL rules.

In particular:

- OWL axioms remain the intensional semantic model;
- the Python/RDFLib layer performs selected individual-level materialization over the demonstrative ABox;
- generated resources use deterministic IRIs so that the resulting graph is easy to inspect;
- capability matching is used as a candidate-filtering mechanism and does not claim arbitrary conjunctive satisfaction of independently specified capability requirements.

The demonstration should therefore be interpreted as evidence of representational adequacy and queryability, not as a benchmark of reasoning performance, migration-policy quality, or system-level robustness.

## Reproducibility

For a reproducible run, record:

- the exact ontology version used;
- the Python version;
- the installed versions of `rdflib` and `pandas`;
- the exact set of SPARQL query files, if provided externally.

The generated CSV and Turtle files can be inspected directly or regenerated by rerunning the script.
