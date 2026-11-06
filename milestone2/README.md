# Milestone 2 — Formula 1 Knowledge Graph

| file | what it is |
|---|---|
| `create_kg.py` | builds the KG in Neo4j from the 9 CSVs next to it (drivers, constructors, circuits, seasons, status, races, results, qualifying, pit_stops) |
| `config.txt` | Neo4j credentials, read by key (`URI`, `USERNAME`, `PASSWORD`; an optional `DATABASE` is used if present, otherwise the server default) |
| `queries.txt` | Cypher for verification questions 1–5 |

## Run

```bash
pip install neo4j
# copy the 9 CSVs from ../data into this folder (they are git-ignored)
python create_kg.py
```

Local Neo4j for testing: `docker run -d --name acl-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/your_password neo4j:5`

## Design notes

* Uniqueness constraints on every node key; nodes are `MERGE`d on the key and `SET n = props`, relationships are `MERGE`d → re-running creates no duplicates (verified: 51,113 nodes / 163,510 relationships after one and after two runs).
* Entity nodes and race links are created before fact nodes.
* Missing values (`\N`, empty `q2`/`q3`) are never stored; the property is omitted.
* Types: ids and whole numbers → integer; `points`, `lat`, `lng`, `fastestLapSpeed` → float; `dob`, `date` → Neo4j `date`; everything else (including lap times, `duration`) → string. PitStop `eventId` = `"raceId:driverId:stop"`.
* Raw values are kept as in the CSVs (no Milestone 1 cleaning), so the graph matches the expected counts.
* Q4 computes the average as `sum / count` instead of `avg()`: `avg()` adds floating-point noise (e.g. 5.250000000000001) that breaks the wins tiebreak between equal averages.
* All five answers were cross-checked against an independent pandas computation on the CSVs.
