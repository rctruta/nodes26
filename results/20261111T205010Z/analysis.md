# Run analysis

Run: `20261111T205010Z`
Experiment: `catalog_lamp_strict` (SHA-256 `334dc0c462974562869f3da9e197ab567e8fa5bc6251e632bea64349de96df75`)
Code: commit `5813b57100da2f4aa7bdbb6a82744b7a075d6655`, clean tree
Target: `Meadowlight Lamp`. Control entity: `Harbor Task Lamp`
Primary query: Which desk lamp should I consider for an energy-efficient office upgrade?
Primary search threshold: 0.7
Core ingestion and retrieval complete: **yes**
Agent trials complete: **yes**

## Settings

- Ontology: `procurement_catalog.yaml` (SHA-256 `6e9246588188bbb9d72909c6f4ce7aac7534e53a463bc44a4d23f6803763eb3d`)
- Validation mode: strict
- Provenance links written at ingestion: yes
- Agent tools: search_memory, get_entity_provenance, cypher_query
- Memory library version: 0.8.0

## Graph and retrieval

Each row follows the arm's subject entity: the control entity in the control arm,
the target in the others. `Target nodes` counts nodes named after the target.
`Provenance` counts the source messages the library's provenance call returned.

| Arm | Stage | Subject | Type | Sources | Provenance | Entities | Target nodes | Entity rank / score | Message rank / score |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| control | base | Harbor Task Lamp | OBJECT:PRODUCT | 1 | 1 | 11 | 0 | 4 / 0.7367 | 2 / 0.8197 |
| single | base | Meadowlight Lamp | OBJECT:PRODUCT | 1 | 1 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| copies | base | Meadowlight Lamp | OBJECT:PRODUCT | 1 | 1 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| copies | expanded | Meadowlight Lamp | OBJECT:PRODUCT | 4 | 4 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| distinct | base | Meadowlight Lamp | OBJECT:PRODUCT | 1 | 1 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| distinct | expanded | Meadowlight Lamp | OBJECT:PRODUCT | 4 | 4 | 17 | 1 | 5 / 0.7488 | 1 / 0.8711 |

## Expansion comparison

- copies: sources 1 to 4; same node: True; same embedding: True; same score: True; same rank: True; new entities: none.
- distinct: sources 1 to 4; same node: True; same embedding: True; same score: True; same rank: False; new entities: facilities guide, low-energy product, office lighting, procurement handbook, task light, workplace catalog.

## Agent trials

A name in a tool result or an answer is not a recommendation. Read the full trial
file before labeling one.

| Arm | Memory | Trial | Subject | Tool calls | Tools used | In tool result | In answer |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| control | long_term | 1 | Harbor Task Lamp | 2 | get_entity_provenance, search_memory | yes | yes |
| control | long_term | 2 | Harbor Task Lamp | 2 | get_entity_provenance, search_memory | yes | yes |
| control | long_term | 3 | Harbor Task Lamp | 3 | get_entity_provenance, search_memory | yes | yes |
| control | short_term | 1 | Harbor Task Lamp | 3 | search_memory | yes | yes |
| control | short_term | 2 | Harbor Task Lamp | 1 | search_memory | yes | yes |
| control | short_term | 3 | Harbor Task Lamp | 3 | search_memory | yes | yes |
| single | long_term | 1 | Meadowlight Lamp | 4 | get_entity_provenance, search_memory | yes | yes |
| single | long_term | 2 | Meadowlight Lamp | 3 | get_entity_provenance, search_memory | yes | yes |
| single | long_term | 3 | Meadowlight Lamp | 2 | get_entity_provenance, search_memory | yes | yes |
| single | short_term | 1 | Meadowlight Lamp | 2 | get_entity_provenance, search_memory | yes | yes |
| single | short_term | 2 | Meadowlight Lamp | 3 | get_entity_provenance, search_memory | yes | yes |
| single | short_term | 3 | Meadowlight Lamp | 3 | get_entity_provenance, search_memory | yes | yes |
| copies | long_term | 1 | Meadowlight Lamp | 2 | get_entity_provenance, search_memory | yes | yes |
| copies | long_term | 2 | Meadowlight Lamp | 3 | cypher_query, search_memory | yes | yes |
| copies | long_term | 3 | Meadowlight Lamp | 5 | get_entity_provenance, search_memory | yes | yes |
| copies | short_term | 1 | Meadowlight Lamp | 2 | search_memory | yes | yes |
| copies | short_term | 2 | Meadowlight Lamp | 1 | search_memory | yes | yes |
| copies | short_term | 3 | Meadowlight Lamp | 2 | search_memory | yes | yes |
| distinct | long_term | 1 | Meadowlight Lamp | 10 | get_entity_provenance, search_memory | yes | yes |
| distinct | long_term | 2 | Meadowlight Lamp | 9 | cypher_query, get_entity_provenance, search_memory | yes | yes |
| distinct | long_term | 3 | Meadowlight Lamp | 4 | get_entity_provenance, search_memory | yes | yes |
| distinct | short_term | 1 | Meadowlight Lamp | 2 | search_memory | yes | yes |
| distinct | short_term | 2 | Meadowlight Lamp | 2 | get_entity_provenance, search_memory | yes | yes |
| distinct | short_term | 3 | Meadowlight Lamp | 2 | search_memory | yes | yes |

## Missing planned files

None.
