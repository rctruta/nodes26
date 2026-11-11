# Run `20261111T213005Z` compared with `20261111T161252Z`

Both runs ingest the same documents and ask the same queries unless the
definitions say otherwise. The first table shows every setting; the rest
show what each run recorded.

## Settings

| Setting | `20261111T161252Z` | `20261111T213005Z` | Same |
| --- | --- | --- | --- |
| Experiment | `catalog_lamp` | `catalog_lamp_upstream_ontology` | **no** |
| Code | commit `2c01a5a`, clean tree | commit `6a737a3`, clean tree | **no** |
| Memory library | 0.8.0 | 0.8.0 | yes |
| Ontology | none; built-in schema `poleo` | `upstream_support_desk.yaml` (SHA-256 `d85f0887388e6617ea91e310f2099178fb4529818f21940398de321200f38e88`) | **no** |
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

| Arm | Stage | `20261111T161252Z` | `20261111T213005Z` |
| --- | --- | --- | --- |
| control | base | OBJECT; 1; not recorded; 11; 4 / 0.7367; 2 / 0.8197 | OBJECT:PRODUCT; 1; 1; 8; 3 / 0.7367; 2 / 0.8197 |
| single | base | OBJECT; 1; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 1; 1; 7; 3 / 0.7488; 1 / 0.8711 |
| copies | base | OBJECT; 1; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 1; 1; 7; 3 / 0.7488; 1 / 0.8711 |
| copies | expanded | OBJECT; 4; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 4; 4; 7; 3 / 0.7488; 1 / 0.8711 |
| distinct | base | OBJECT; 1; not recorded; 11; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 1; 1; 7; 3 / 0.7488; 1 / 0.8711 |
| distinct | expanded | OBJECT; 4; not recorded; 15; 4 / 0.7488; 1 / 0.8711 | OBJECT:PRODUCT; 4; 4; 8; 3 / 0.7488; 1 / 0.8711 |

## Expansion

| Arm | `20261111T161252Z` | `20261111T213005Z` |
| --- | --- | --- |
| copies | sources 1 to 4; same embedding True; same score True; same rank True; new entities: none | sources 1 to 4; same embedding True; same score True; same rank True; new entities: none |
| distinct | sources 1 to 4; same embedding True; same score True; same rank True; new entities: office desks, procurement handbook, task light, workplace catalog | sources 1 to 4; same embedding True; same score True; same rank True; new entities: workplace catalog |

## Agent trials

Each cell is trials with the subject's name in a tool result, trials with it in
the answer, and the tools the agent called. A name in an answer is not a
recommendation; read the trial files.

| Arm | Memory | `20261111T161252Z` | `20261111T213005Z` |
| --- | --- | --- | --- |
| control | long_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| control | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; search_memory |
| single | long_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| single | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| copies | long_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; get_entity_provenance, search_memory |
| copies | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; search_memory |
| distinct | long_term | 2 of 3; 2 of 3; search_memory | 3 of 3; 3 of 3; cypher_query, get_entity_provenance, search_memory |
| distinct | short_term | 3 of 3; 3 of 3; search_memory | 3 of 3; 3 of 3; search_memory |
