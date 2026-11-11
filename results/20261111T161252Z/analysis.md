# Run analysis

Run: `20261111T161252Z`
Experiment: `catalog_lamp` (SHA-256 `0d393788348bb9b373b67a927f282664758b893fcebbe6c8717c9085fc11935a`)
Code: commit `2c01a5a0a04c350020b561f67080887dc82fd029`, clean tree
Target: `Meadowlight Lamp`. Control entity: `Harbor Task Lamp`
Primary query: Which desk lamp should I consider for an energy-efficient office upgrade?
Primary search threshold: 0.7
Core ingestion and retrieval complete: **yes**
Agent trials complete: **yes**

## Graph and retrieval

Each row follows the arm's subject entity: the control entity in the control arm,
the target in the others. `Target nodes` counts nodes named after the target.

| Arm | Stage | Subject | Type | Sources | Entities | Target nodes | Entity rank / score | Message rank / score |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| control | base | Harbor Task Lamp | OBJECT | 1 | 11 | 0 | 4 / 0.7367 | 2 / 0.8197 |
| single | base | Meadowlight Lamp | OBJECT | 1 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| copies | base | Meadowlight Lamp | OBJECT | 1 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| copies | expanded | Meadowlight Lamp | OBJECT | 4 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| distinct | base | Meadowlight Lamp | OBJECT | 1 | 11 | 1 | 4 / 0.7488 | 1 / 0.8711 |
| distinct | expanded | Meadowlight Lamp | OBJECT | 4 | 15 | 1 | 4 / 0.7488 | 1 / 0.8711 |

## Expansion comparison

- copies: sources 1 to 4; same node: True; same embedding: True; same score: True; same rank: True; new entities: none.
- distinct: sources 1 to 4; same node: True; same embedding: True; same score: True; same rank: True; new entities: office desks, procurement handbook, task light, workplace catalog.

## Agent trials

A name in a tool result or an answer is not a recommendation. Read the full trial
file before labeling one.

| Arm | Memory | Trial | Subject | Tool calls | In tool result | In answer |
| --- | --- | ---: | --- | ---: | --- | --- |
| control | long_term | 1 | Harbor Task Lamp | 1 | yes | yes |
| control | long_term | 2 | Harbor Task Lamp | 3 | yes | yes |
| control | long_term | 3 | Harbor Task Lamp | 1 | yes | yes |
| control | short_term | 1 | Harbor Task Lamp | 1 | yes | yes |
| control | short_term | 2 | Harbor Task Lamp | 1 | yes | yes |
| control | short_term | 3 | Harbor Task Lamp | 1 | yes | yes |
| single | long_term | 1 | Meadowlight Lamp | 2 | yes | yes |
| single | long_term | 2 | Meadowlight Lamp | 3 | yes | yes |
| single | long_term | 3 | Meadowlight Lamp | 1 | yes | yes |
| single | short_term | 1 | Meadowlight Lamp | 1 | yes | yes |
| single | short_term | 2 | Meadowlight Lamp | 1 | yes | yes |
| single | short_term | 3 | Meadowlight Lamp | 1 | yes | yes |
| copies | long_term | 1 | Meadowlight Lamp | 6 | yes | yes |
| copies | long_term | 2 | Meadowlight Lamp | 1 | yes | yes |
| copies | long_term | 3 | Meadowlight Lamp | 2 | yes | yes |
| copies | short_term | 1 | Meadowlight Lamp | 1 | yes | yes |
| copies | short_term | 2 | Meadowlight Lamp | 1 | yes | yes |
| copies | short_term | 3 | Meadowlight Lamp | 1 | yes | yes |
| distinct | long_term | 1 | Meadowlight Lamp | 2 | yes | yes |
| distinct | long_term | 2 | Meadowlight Lamp | 1 | yes | yes |
| distinct | long_term | 3 | Meadowlight Lamp | 1 | no | no |
| distinct | short_term | 1 | Meadowlight Lamp | 1 | yes | yes |
| distinct | short_term | 2 | Meadowlight Lamp | 1 | yes | yes |
| distinct | short_term | 3 | Meadowlight Lamp | 1 | yes | yes |

## Missing planned files

None.
