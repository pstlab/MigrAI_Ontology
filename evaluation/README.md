# MAI ontology evaluation material

This folder accompanies the revised manuscript and collects the artifacts used to make the ontology-level evaluation reproducible.

- `queries/cq1.rq` -- assisted-person qualities and assistive methods/tasks.
- `queries/cq2.rq` -- bearer-specific embodiment capabilities.
- `queries/cq3.rq` -- suitable embodiments, including the all-required-capabilities check.
- `queries/cq4.rq` -- contextual task opportunities.
- `queries/cq5.rq` -- embodiments associated with interaction contexts.
- `queries/cq6.rq` -- migration opportunities grounded in task opportunities.
- `ontology_precheck.py` -- local structural/pitfall-oriented scan over MAI-defined entities.
- `OOPS_request_template.xml` -- request template for an official OOPS! REST scan of the final release ontology.

The SPARQL queries assume that the individual-level forward rules described in the paper have already materialized `SuitableEmbodiment`, `TaskOpportunity`, and `MigrationOpportunity` assertions in the runtime ABox. They are retrieval/evaluation queries, not a substitute for the forward-rule layer.

Before repository release, run an OWL 2 DL reasoner (HermiT or Pellet) on the final ontology with imports resolved and run the official OOPS! service on the exact released ontology. Record the ontology version IRI, reasoner version, consistency result, and OOPS! report in the repository.
