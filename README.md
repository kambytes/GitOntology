# Git-Onto-Logic: A Knowledge Graph for Version Control Systems

**Git-Onto-Logic** is a Semantic Web application designed to model and analyze the structural and logical complexities of the Git version control system. By transforming raw repository metadata into a machine-understandable ontology, this project enables advanced querying and automated reasoning over development histories.

## Overview
The project leverages **Knowledge Representation (KR)** to bridge the gap between flat metadata and deep semantic insights[cite:. It allows users to explore relationships between repositories, contributors, and code changes through an interactive web interface.

### Key Capabilities:
- **Semantic Modeling**: Models core Git entities including Repositories, Branches, Commits, Users, Files, and Tags.
- **Automated Reasoning**: Uses SWRL (Semantic Web Rule Language) to infer "hidden" knowledge, such as automatically classifying merge commits or identifying concurrent contributors across multiple projects.
- **Interactive Exploration**: A Flask-powered web interface for navigating the knowledge graph, running custom SPARQL queries, and performing data validation.

---

## Technology Stack
- **Ontology Engineering**: OWL 2.0, Protégé (Design & Visualization).
- **Programming**: Python (Owlready2 for ontology management, Flask for the web UI).
- **Reasoning & Querying**: Pellet Reasoner (supporting SWRLB built-ins), SPARQL (via RDFlib).
- **Data Sources**: GitHub REST API (JSON extraction).

---

## Ontology Schema & Logic
The ontology is built around a structured hierarchy and logic-driven rules:

### Core Classes & Properties
* **Classes**: `Repository`, `Branch`, `Commit`, `User`, `File`, `Tag`.
* **Object Properties**: Functional and inverse relations such as `belongsToRepo`, `hasCommit`, `authoredBy`, and `hasParentCommit`.

### Semantic Inference (SWRL Rules)
Specific rules were implemented to provide automated classification:
* **Commit Classification**: Commits are automatically categorized as `InitialCommit`, `NormalCommit`, or `MergeCommit` based on parent counts.
* **Contribution Mapping**: If a user authors a commit on a branch belonging to a repository, they are inferred to be a contributor to that repository (`contributesTo`).
* **Branch Typing**: Branches are classified as `MainBranch` or `SecondaryBranch` based on their default status.

## 🖥️ Project Structure
The system is organized into three processing stages to ensure data integrity:
1.  **Base Ontology (`git_ontology_base.owl`)**: The unpopulated schema and rules.
2.  **Populated Ontology (`git_ontology_populated.owl`)**: Individuals generated from extracted GitHub JSON data.
3.  **Reasoned Ontology (`git_ontology_reasoned.owl`)**: The final knowledge graph containing all inferred triples and relationships.
