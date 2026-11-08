"""Build the Formula 1 Knowledge Graph (Milestone 2) in Neo4j.

Reads the nine CSV files and config.txt from the directory this script is in.
Every node is MERGEd on its unique identifier (backed by a uniqueness
constraint) and every relationship is MERGEd, so re-running the script never
creates duplicates. Missing values (the literal \\N and empty cells) are not
stored: the property is omitted.

Usage:  python create_kg.py
"""

import csv
import os
from datetime import date

from neo4j import GraphDatabase

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH_SIZE = 5000


# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
def read_config(path):
    """Read KEY=VALUE lines by key (order and extra keys do not matter)."""
    config = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip().upper()] = value.strip()
    for key in ("URI", "USERNAME", "PASSWORD"):
        if key not in config:
            raise KeyError(f"config.txt is missing the {key} entry")
    return config


# ----------------------------------------------------------------------------
# Type conversion: a missing value returns None and is then dropped
# ----------------------------------------------------------------------------
def is_missing(value):
    return value is None or value.strip() in ("", "\\N")


def to_int(value):
    return None if is_missing(value) else int(value)


def to_float(value):
    return None if is_missing(value) else float(value)


def to_str(value):
    return None if is_missing(value) else value


def to_date(value):
    return None if is_missing(value) else date.fromisoformat(value.strip())


def build(row, spec):
    """spec: list of (property_name, csv_column, converter). Drops missing values."""
    props = {}
    for prop, column, convert in spec:
        value = convert(row[column])
        if value is not None:
            props[prop] = value
    return props


def read_csv(name):
    with open(os.path.join(HERE, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ----------------------------------------------------------------------------
# Property specifications (schema property name, CSV column, type)
# ----------------------------------------------------------------------------
DRIVER = [
    ("driverId", "driverId", to_int),
    ("driverRef", "driverRef", to_str),
    ("number", "number", to_int),
    ("code", "code", to_str),
    ("forename", "forename", to_str),
    ("surname", "surname", to_str),
    ("dob", "dob", to_date),
    ("nationality", "nationality", to_str),
]
CONSTRUCTOR = [
    ("constructorId", "constructorId", to_int),
    ("constructorRef", "constructorRef", to_str),
    ("constructor_name", "name", to_str),
    ("constructor_nationality", "nationality", to_str),
]
CIRCUIT = [
    ("circuitId", "circuitId", to_int),
    ("circuitRef", "circuitRef", to_str),
    ("circuit_name", "name", to_str),
    ("circuit_loc", "location", to_str),
    ("circuit_country", "country", to_str),
    ("lat", "lat", to_float),
    ("lng", "lng", to_float),
    ("alt", "alt", to_int),
]
SEASON = [("year", "year", to_int)]
STATUS = [("statusId", "statusId", to_int), ("status", "status", to_str)]
RACE = [
    ("raceId", "raceId", to_int),
    ("year", "year", to_int),
    ("round", "round", to_int),
    ("name", "name", to_str),
    ("date", "date", to_date),
    ("time", "time", to_str),
]
RESULT = [
    ("resultId", "resultId", to_int),
    ("number", "number", to_int),
    ("grid", "grid", to_int),
    ("position", "position", to_int),
    ("positionText", "positionText", to_str),
    ("positionOrder", "positionOrder", to_int),
    ("points", "points", to_float),
    ("laps", "laps", to_int),
    ("time", "time", to_str),
    ("milliseconds", "milliseconds", to_int),
    ("fastestLap", "fastestLap", to_int),
    ("rank", "rank", to_int),
    ("fastestLapTime", "fastestLapTime", to_str),
    ("fastestLapSpeed", "fastestLapSpeed", to_float),
]
QUALIFYING = [
    ("qualifyId", "qualifyId", to_int),
    ("number", "number", to_int),
    ("position", "position", to_int),
    ("q1", "q1", to_str),
    ("q2", "q2", to_str),
    ("q3", "q3", to_str),
]
PITSTOP = [
    ("stop", "stop", to_int),
    ("lap", "lap", to_int),
    ("time", "time", to_str),
    ("duration", "duration", to_str),
    ("milliseconds", "milliseconds", to_int),
]

# Node labels and their unique key
CONSTRAINTS = [
    ("Driver", "driverId"),
    ("Constructor", "constructorId"),
    ("Circuit", "circuitId"),
    ("Season", "year"),
    ("Status", "statusId"),
    ("Race", "raceId"),
    ("Result", "resultId"),
    ("Qualifying", "qualifyId"),
    ("PitStop", "eventId"),
]


# ----------------------------------------------------------------------------
# Neo4j helpers
# ----------------------------------------------------------------------------
def run_batches(driver, database, query, rows):
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        driver.execute_query(query, rows=batch, database_=database)


def merge_nodes(driver, database, label, key, rows):
    """MERGE each node on its key, then set exactly the given properties.

    SET n = props replaces all properties, so a re-run never keeps a stale
    value (and never stores a missing one)."""
    query = (
        f"UNWIND $rows AS row "
        f"MERGE (n:{label} {{{key}: row.props.{key}}}) "
        f"SET n = row.props"
    )
    run_batches(driver, database, query, rows)
    print(f"  {label}: {len(rows)} nodes")


def merge_rels(driver, database, from_label, from_key, rel, to_label, to_key, rows):
    """rows: list of {'from': id, 'to': id}. Both endpoints must already exist."""
    query = (
        f"UNWIND $rows AS row "
        f"MATCH (a:{from_label} {{{from_key}: row.from}}) "
        f"MATCH (b:{to_label} {{{to_key}: row.to}}) "
        f"MERGE (a)-[:{rel}]->(b)"
    )
    run_batches(driver, database, query, rows)
    print(f"  ({from_label})-[:{rel}]->({to_label}): {len(rows)}")


def links(rows, from_col, to_col):
    return [{"from": int(r[from_col]), "to": int(r[to_col])} for r in rows]


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    config = read_config(os.path.join(HERE, "config.txt"))
    # No database name is hardcoded: use DATABASE from config.txt if it is
    # there, otherwise the server's default database.
    database = config.get("DATABASE") or None

    drivers = read_csv("drivers.csv")
    constructors = read_csv("constructors.csv")
    circuits = read_csv("circuits.csv")
    seasons = read_csv("seasons.csv")
    statuses = read_csv("status.csv")
    races = read_csv("races.csv")
    results = read_csv("results.csv")
    qualifying = read_csv("qualifying.csv")
    pit_stops = read_csv("pit_stops.csv")

    # PitStop id is raceId:driverId:stop
    for r in pit_stops:
        r["eventId"] = f"{int(r['raceId'])}:{int(r['driverId'])}:{int(r['stop'])}"

    with GraphDatabase.driver(config["URI"],
                              auth=(config["USERNAME"], config["PASSWORD"])) as driver:
        driver.verify_connectivity()

        print("Constraints")
        for label, key in CONSTRAINTS:
            driver.execute_query(
                f"CREATE CONSTRAINT {label.lower()}_{key.lower()}_unique IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{key} IS UNIQUE",
                database_=database,
            )

        # 1. Parent (entity) nodes first
        print("Entity nodes")
        merge_nodes(driver, database, "Driver", "driverId",
                    [{"props": build(r, DRIVER)} for r in drivers])
        merge_nodes(driver, database, "Constructor", "constructorId",
                    [{"props": build(r, CONSTRUCTOR)} for r in constructors])
        merge_nodes(driver, database, "Circuit", "circuitId",
                    [{"props": build(r, CIRCUIT)} for r in circuits])
        merge_nodes(driver, database, "Season", "year",
                    [{"props": build(r, SEASON)} for r in seasons])
        merge_nodes(driver, database, "Status", "statusId",
                    [{"props": build(r, STATUS)} for r in statuses])
        merge_nodes(driver, database, "Race", "raceId",
                    [{"props": build(r, RACE)} for r in races])

        print("Race relationships")
        merge_rels(driver, database, "Race", "raceId", "AT_CIRCUIT", "Circuit", "circuitId",
                   links(races, "raceId", "circuitId"))
        merge_rels(driver, database, "Race", "raceId", "IN_SEASON", "Season", "year",
                   links(races, "raceId", "year"))

        # 2. Fact nodes and their links
        print("Fact nodes")
        merge_nodes(driver, database, "Result", "resultId",
                    [{"props": build(r, RESULT)} for r in results])
        merge_nodes(driver, database, "Qualifying", "qualifyId",
                    [{"props": build(r, QUALIFYING)} for r in qualifying])
        merge_nodes(driver, database, "PitStop", "eventId",
                    [{"props": {"eventId": r["eventId"], **build(r, PITSTOP)}} for r in pit_stops])

        print("Fact relationships")
        merge_rels(driver, database, "Result", "resultId", "FOR_RACE", "Race", "raceId",
                   links(results, "resultId", "raceId"))
        merge_rels(driver, database, "Result", "resultId", "BY_DRIVER", "Driver", "driverId",
                   links(results, "resultId", "driverId"))
        merge_rels(driver, database, "Result", "resultId", "FOR_CONSTRUCTOR", "Constructor",
                   "constructorId", links(results, "resultId", "constructorId"))
        merge_rels(driver, database, "Result", "resultId", "HAS_STATUS", "Status", "statusId",
                   links(results, "resultId", "statusId"))

        merge_rels(driver, database, "Qualifying", "qualifyId", "FOR_RACE", "Race", "raceId",
                   links(qualifying, "qualifyId", "raceId"))
        merge_rels(driver, database, "Qualifying", "qualifyId", "BY_DRIVER", "Driver", "driverId",
                   links(qualifying, "qualifyId", "driverId"))
        merge_rels(driver, database, "Qualifying", "qualifyId", "FOR_CONSTRUCTOR", "Constructor",
                   "constructorId", links(qualifying, "qualifyId", "constructorId"))

        pit_links = lambda col: [{"from": r["eventId"], "to": int(r[col])} for r in pit_stops]
        merge_rels(driver, database, "PitStop", "eventId", "FOR_RACE", "Race", "raceId",
                   pit_links("raceId"))
        merge_rels(driver, database, "PitStop", "eventId", "BY_DRIVER", "Driver", "driverId",
                   pit_links("driverId"))

        # Summary
        nodes = driver.execute_query("MATCH (n) RETURN count(n) AS c",
                                     database_=database).records[0]["c"]
        rels = driver.execute_query("MATCH ()-[r]->() RETURN count(r) AS c",
                                    database_=database).records[0]["c"]
        print(f"Done: {nodes} nodes, {rels} relationships "
              f"(expected 51113 nodes, 163510 relationships)")


if __name__ == "__main__":
    main()
