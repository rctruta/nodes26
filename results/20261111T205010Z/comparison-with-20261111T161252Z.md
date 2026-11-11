# Run `20261111T205010Z` compared with `20261111T161252Z`

Both runs ingest the same documents and ask the same queries unless the
definitions say otherwise. The first table shows every setting; the rest
show what each run recorded.

## Settings

| Setting | `20261111T161252Z` | `20261111T205010Z` | Same |
| --- | --- | --- | --- |
| Experiment | `catalog_lamp` | `catalog_lamp_strict` | **no** |
| Code | commit `2c01a5a`, clean tree | commit `5813b57`, clean tree | **no** |
| Memory library | 0.8.0 | 0.8.0 | yes |
| Ontology | none; built-in schema `poleo` | `procurement_catalog.yaml` (SHA-256 `6e9246588188bbb9d72909c6f4ce7aac7534e53a463bc44a4d23f6803763eb3d`) | **no** |
| Validation mode | strict | strict | yes |
| Provenance links written | no | yes | **no** |
| Agent tools | search_memory | search_memory, get_entity_provenance, cypher_query | **no** |
| Target | Meadowlight Lamp | Meadowlight Lamp | yes |
| Control entity | Harbor Task Lamp | Harbor Task Lamp | yes |
| Primary query | Which desk lamp should I consider for an energy-efficient office upgrade? | Which desk lamp should I consider for an energy-efficient office upgrade? | yes |
| Search threshold | 0.7 | 0.7 | yes |

## Graph and retrieval

Each cell is `type`, linked messages, provenance sources, entities in the graph,
entity rank / score, message rank / score, for the arm's subject entity.

| Arm | Stage | `20261111T161252Z` | `20261111T205010Z` |
| --- | --- | --- | --- |
| control | base | OBJECT; 1; not recorded; 11; 4 / 0.7367; 2 / 0.8197 | OBJECT:PRODUCT; 1; 1; 11; 4 / 0.7367; 2 / 0.8197 |
| single | base | OBJECT; 1; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 1; 1; 11; 4 / 0.7488; 1 / 0.8711 |
| copies | base | OBJECT; 1; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 1; 1; 11; 4 / 0.7488; 1 / 0.8711 |
| copies | expanded | OBJECT; 4; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 4; 4; 11; 4 / 0.7488; 1 / 0.8711 |
| distinct | base | OBJECT; 1; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 1; 1; 11; 4 / 0.7488; 1 / 0.8711 |
| distinct | expanded | OBJECT; 4; not recorded; 15; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 4; 4; 17; 5 / 0.7488; 1 / 0.8711 |

## Expansion

| Arm | `20261111T161252Z` | `20261111T205010Z` |
| --- | --- | --- |
| copies | sources 1 to 4; same embedding True; same score True; same rank True; new entities: none | sources 1 to 4; same embedding True; same score True; same rank True; new entities: none |
| distinct | sources 1 to 4; same embedding True; same score True; same rank True; new entities: office desks, procurement handbook, task light, workplace catalog | sources 1 to 4; same embedding True; same score True; same rank False; new entities: facilities guide, low-energy product, office lighting, procurement handbook, task light, workplace catalog |

## Agent trials

Each cell is trials with the subject's name in a tool result, trials with it in
the answer, and the tools the agent called. A name in an answer is not a
recommendation; read the trial files.

| Arm | Memory | `20261111T161252Z` | `20261111T205010Z` |
| --- | --- | --- | --- |
| control | long_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| control | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; search_memory |
| single | long_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| single | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| copies | long_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; cypher_query, get_entity_provenance, search_memory |
| copies | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; search_memory |
| distinct | long_term | 2 of 3; 2 of 3; search_memory | 3 of 3; 3 of 3; cypher_query, get_entity_provenance, search_memory |
| distinct | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
