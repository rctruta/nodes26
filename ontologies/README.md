# Ontologies

| File | Origin |
| --- | --- |
| `procurement_catalog.yaml` | Written for this experiment, for the catalog domain its documents describe. |
| `upstream_support_desk.yaml` | The memory library's own example ontology, unmodified. |

`upstream_support_desk.yaml` is a byte-for-byte copy of `examples/ontology-extraction/ontology.yaml` from [neo4j-labs/agent-memory](https://github.com/neo4j-labs/agent-memory) at commit `9d45af5529ecb5f2fe352013468a11087f3163d4`, the commit this repository pins. Its SHA-256 is `d85f0887388e6617ea91e310f2099178fb4529818f21940398de321200f38e88`. It is Copyright 2024 Neo4j Labs and licensed under the Apache License 2.0. It describes a support desk, not a procurement catalog; it is included so that a run can use rules this experiment's author did not write.

Both files load through `SchemaConfig(ontology_path=...)`, the route the library's ontology example uses. Validate either without a database:

```bash
uv run neo4j-agent-memory ontology validate ontologies/procurement_catalog.yaml
```
