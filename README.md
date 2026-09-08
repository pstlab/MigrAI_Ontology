# MigrAI Ontology

Semantic model for **Migratable Artificial Intelligence (MAI)**.

This repository contains the ontology and evaluation artifacts developed to support
the representation and reasoning requirements of intelligent agents that can operate
through heterogeneous physical embodiments while preserving a persistent cognitive
identity.

The ontology has been developed in the context of continuous and personalized
assistance, with particular reference to rehabilitation scenarios involving
heterogeneous interactive technologies such as social robots, tablets, smartphones,
smart displays, and related assistive devices.

---

## Motivation

Conventional intelligent and robotic systems typically associate an intelligent agent
with a specific physical embodiment.

Migratable Artificial Intelligence instead considers a persistent intelligent entity
whose cognitive state, goals, memory, user knowledge, and interaction continuity can be
maintained while the physical device through which the agent perceives and acts changes
over time.

From a semantic perspective, this requires an explicit representation of:

- the persistent intelligent agent;
- heterogeneous physical embodiments;
- capabilities borne by each embodiment;
- assistive tasks and their functional requirements;
- user-related assistance needs;
- interaction contexts;
- suitable embodiments for a given task;
- contextual task opportunities;
- migration opportunities.

The MigrAI ontology provides the semantic structures required to formally represent
these elements and reason about their relationships.

---

## Ontological Foundations

The ontology is grounded in and reuses concepts and modeling patterns from:

- **DOLCE / DOLCE+DnS Ultralite (DUL)**, providing the foundational semantics for
  physical objects, qualities, roles, descriptions, and contextual classification;
- **SOMA — SOcio-physical Model of Activities**, providing semantic patterns for
  tasks, capabilities, dispositions, affordances, and agent-environment interaction;
- **MOI — Metacognitive Ontology for Introspection**, from which selected patterns
  concerning cognitive agents, tasks, capabilities, and performer roles are reused.

The MigrAI ontology specializes these foundations to address the specific
representation requirements of migratable agents.

---

## Main Modeling Principles

### Persistent Agent and Physical Embodiments

A central principle of MigrAI is the separation between the persistent intelligent
agent and the physical artifacts through which it operates.

An `Embodiment` represents a physical device capable of providing perception,
interaction, or action functionalities.

Different embodiments may therefore realize the same persistent intelligent agent
under different interaction conditions.

Examples include:

- social robots;
- tablets;
- smartphones;
- smart TVs and displays;
- other interactive assistive devices.

---

### Capabilities and Task Requirements

Following SOMA, capabilities are modeled as qualities borne by physical objects.

Each concrete embodiment therefore possesses its own bearer-specific capability
individuals.

Task-side functional requirements and embodiment-side capabilities are intentionally
kept distinct.

An assistive task specifies the types of capabilities required for its realization,
whereas an embodiment bears concrete capability instances classified according to the
corresponding capability taxonomy.

This distinction avoids representing a capability as one shared individual associated
simultaneously with a task and multiple physical embodiments.

---

### Suitable Embodiments

The ontology reuses the performer-role pattern to represent the relationship between
tasks and potential realizers.

`SuitableEmbodiment` identifies an embodiment that can act as a performer for an
`EmbodiedTask` because its bearer-specific capabilities satisfy the functional
requirements associated with that task.

Conceptually:

```text
EmbodiedTask
     |
     v
functional requirements
     |
     v
Capability types
     ^
     |
bearer-specific capabilities
     ^
     |
Embodiment
