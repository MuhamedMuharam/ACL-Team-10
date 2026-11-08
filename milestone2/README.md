# Milestone 2 — Formula 1 Knowledge Graph

| file | what it is |
|---|---|
| `create_kg.py` | builds the KG in Neo4j from the 9 CSVs next to it (drivers, constructors, circuits, seasons, status, races, results, qualifying, pit_stops) |
| `config.txt` | Neo4j credentials, read by key (`URI`, `USERNAME`, `PASSWORD`; an optional `DATABASE` is used if present, otherwise the server default) |
| `queries.txt` | Cypher for verification questions 1–5 |

## Run

1. Go to https://console.neo4j.io, click **Create instance** and choose **Free**.
2. Click **Download and continue** to save the credentials file. The password is shown only once.
3. Fill in `config.txt` from that file:
   ```
   URI=<NEO4J_URI from the file>        e.g. neo4j+s://xxxxxxxx.databases.neo4j.io
   USERNAME=<NEO4J_USERNAME from the file>
   PASSWORD=<NEO4J_PASSWORD from the file>
   ```
4. Copy the 9 CSVs into this folder (they are git-ignored).
5. Install the driver and build the graph:
   ```bash
   pip install neo4j
   python create_kg.py
   ```
   The last line should read `51113 nodes, 163510 relationships`. Running it again must give the same counts.
6. In the Aura console, open the instance, go to **Query**, and run the queries from `queries.txt`.

## Design notes

* Uniqueness constraints on every node key; nodes are `MERGE`d on the key and `SET n = props`, relationships are `MERGE`d → re-running creates no duplicates (verified: 51,113 nodes / 163,510 relationships after one and after two runs).
* Entity nodes and race links are created before fact nodes.
* Missing values (`\N`, empty `q2`/`q3`) are never stored; the property is omitted.
* Types: ids and whole numbers → integer; `points`, `lat`, `lng`, `fastestLapSpeed` → float; `dob`, `date` → Neo4j `date`; everything else (including lap times, `duration`) → string. PitStop `eventId` = `"raceId:driverId:stop"`.
* Raw values are kept as in the CSVs (no Milestone 1 cleaning), so the graph matches the expected counts.
* Q4 computes the average as `sum / count` instead of `avg()`: `avg()` adds floating-point noise (e.g. 5.250000000000001) that breaks the wins tiebreak between equal averages.
* All five answers were cross-checked against an independent pandas computation on the CSVs.
