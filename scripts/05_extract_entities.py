"""Extract reproducible conservation entities and evidence-backed relations.

This Milestone 3A extractor intentionally uses transparent rules rather than an
LLM. Controlled vocabularies avoid treating generic words such as ``species``
or ``wildlife`` as named species. Every record is tied to one SQLite chunk and
is rebuilt deterministically on each run.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "db" / "conservation.db"
OUTPUTS = ROOT / "outputs"
ENTITIES_CSV = OUTPUTS / "entities.csv"
RELATIONS_CSV = OUTPUTS / "relations.csv"

# Visible, conservative normalization rules. Keys are normalized names and
# values are accepted textual variants. Longer variants win during matching.
AGENCIES = {
    "U.S. Fish and Wildlife Service": ["U.S. Fish and Wildlife Service", "US Fish and Wildlife Service", "USFWS", "FWS"],
    "U.S. Geological Survey": ["U.S. Geological Survey", "US Geological Survey", "USGS"],
    "Missouri Department of Conservation": ["Missouri Department of Conservation", "MDC"],
    "U.S. Environmental Protection Agency": ["U.S. Environmental Protection Agency", "US Environmental Protection Agency", "EPA"],
    "U.S. Army Corps of Engineers": ["U.S. Army Corps of Engineers", "US Army Corps of Engineers", "USACE", "Corps of Engineers"],
    "U.S. Department of the Interior": ["U.S. Department of the Interior", "Department of the Interior", "DOI"],
    "National Oceanic and Atmospheric Administration": ["National Oceanic and Atmospheric Administration", "NOAA"],
    "Ducks Unlimited": ["Ducks Unlimited"],
    "Association of Fish and Wildlife Agencies": ["Association of Fish and Wildlife Agencies", "AFWA"],
    "Environment and Climate Change Canada": ["Environment and Climate Change Canada", "ECCC"],
    "Conservation Federation of Missouri": ["Conservation Federation of Missouri"],
    "Bureau of Indian Affairs": ["Bureau of Indian Affairs", "BIA"],
}

SPECIES = {
    "invasive carp": ["invasive carp", "Asian carp"], "bighead carp": ["bighead carp"],
    "silver carp": ["silver carp"], "black carp": ["black carp"], "grass carp": ["grass carp"],
    "common carp": ["common carp"], "zebra mussel": ["zebra mussel", "zebra mussels"],
    "quagga mussel": ["quagga mussel", "quagga mussels"], "sea lamprey": ["sea lamprey"],
    "northern snakehead": ["northern snakehead"], "round goby": ["round goby"],
    "mute swan": ["mute swan"], "mallard": ["mallard", "mallards"],
    "wood duck": ["wood duck", "wood ducks"], "canvasback": ["canvasback", "canvasbacks"],
    "American black duck": ["American black duck", "black ducks"],
    "Canada goose": ["Canada goose", "Canada geese"], "piping plover": ["piping plover"],
    "bald eagle": ["bald eagle", "bald eagles"], "pallid sturgeon": ["pallid sturgeon"],
    "lake sturgeon": ["lake sturgeon"], "brook trout": ["brook trout"],
    "smallmouth bass": ["smallmouth bass"], "largemouth bass": ["largemouth bass"],
    "white-tailed deer": ["white-tailed deer", "white tailed deer"],
    "greater prairie-chicken": ["greater prairie-chicken", "greater prairie chicken"],
    "monarch butterfly": ["monarch butterfly", "monarch butterflies"],
}

HABITATS = {
    "forest": ["forest habitat", "forested habitat", "forests"],
    "grassland": ["grassland habitat", "grasslands"], "prairie": ["prairie habitat", "prairies"],
    "riparian habitat": ["riparian habitat", "riparian areas", "riparian corridor"],
    "aquatic habitat": ["aquatic habitat", "aquatic habitats"],
    "coastal habitat": ["coastal habitat", "coastal habitats"],
    "bottomland forest": ["bottomland forest", "bottomland hardwood"],
    "estuary": ["estuarine habitat", "estuaries", "estuary"],
    "coral reef": ["coral reefs", "coral reef"],
}

WETLANDS = {
    "wetland": ["wetlands", "wetland habitat", "wetland"], "marsh": ["marshes", "marsh"],
    "swamp": ["swamps", "swamp"], "bog": ["bogs", "bog"], "fen": ["fens", "fen"],
    "floodplain wetland": ["floodplain wetlands", "floodplain wetland"],
    "coastal wetland": ["coastal wetlands", "coastal wetland"],
}

THREATS = {
    "invasive species": ["invasive species", "nonindigenous species", "non-native species"],
    "habitat loss": ["habitat loss", "loss of habitat"], "habitat degradation": ["habitat degradation", "degraded habitat"],
    "climate change": ["climate change", "changing climate"], "pollution": ["pollution", "contamination"],
    "water pollution": ["water pollution", "water contamination"], "drought": ["drought", "droughts"],
    "flooding": ["flooding", "flood risk"], "fragmentation": ["habitat fragmentation", "fragmentation"],
    "overharvest": ["overharvest", "over-harvest"], "disease": ["wildlife disease", "disease"],
}

LOCATIONS = {
    "Missouri": ["Missouri"], "United States": ["United States", "U.S."], "Canada": ["Canada"],
    "Chesapeake Bay": ["Chesapeake Bay"], "Great Lakes": ["Great Lakes"],
    "Mississippi River Basin": ["Mississippi River Basin"], "Missouri River Basin": ["Missouri River Basin"],
    "Gulf of Mexico": ["Gulf of Mexico"], "North America": ["North America", "North American"],
    "Florida": ["Florida"], "Illinois": ["Illinois"], "Iowa": ["Iowa"], "Kansas": ["Kansas"],
    "Arkansas": ["Arkansas"], "Louisiana": ["Louisiana"], "Maryland": ["Maryland"],
}

PROGRAMS = {
    "North American Waterfowl Management Plan": ["North American Waterfowl Management Plan", "NAWMP"],
    "National Wetlands Inventory": ["National Wetlands Inventory", "NWI"],
    "State Wildlife Action Plan": ["State Wildlife Action Plan", "State Wildlife Action Plans", "SWAP"],
    "Aquatic Nuisance Species Task Force": ["Aquatic Nuisance Species Task Force", "ANSTF"],
    "Partners for Fish and Wildlife Program": ["Partners for Fish and Wildlife Program"],
    "Migratory Birds Program": ["Migratory Birds Program"],
    "Invasive Carp Regional Coordinating Committee": ["Invasive Carp Regional Coordinating Committee", "ICRCC"],
}

POLICIES = {
    "Clean Water Act": ["Clean Water Act", "CWA"],
    "Endangered Species Act": ["Endangered Species Act", "ESA"],
    "Migratory Bird Treaty Act": ["Migratory Bird Treaty Act", "MBTA"],
    "National Environmental Policy Act": ["National Environmental Policy Act", "NEPA"],
    "Lacey Act": ["Lacey Act"], "Executive Order 13112": ["Executive Order 13112"],
}

CONTROLLED = {
    "species": SPECIES, "habitat": HABITATS, "wetland": WETLANDS,
    "agency": AGENCIES, "location": LOCATIONS, "threat": THREATS,
    "program": PROGRAMS, "policy": POLICIES,
}
CONFIDENCE = {"species": .94, "habitat": .86, "wetland": .90, "agency": .96,
              "location": .91, "threat": .88, "program": .94, "policy": .96,
              "river": .84, "date": .93}
SENTENCES = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
RIVER = re.compile(r"\b((?:Upper |Lower |Middle )?(?:[A-Z][A-Za-z'’-]+(?:\s+|$)){1,4}(?:River|Creek))\b")
DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)?\s*(?:[0-3]?\d,\s*)?(?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)?\d{2})?\b")
PROGRAM_PATTERN = re.compile(r"\b((?:[A-Z][A-Za-z&-]+\s+){1,7}(?:Program|Initiative|Strategy))\b")
POLICY_PATTERN = re.compile(r"\b((?:[A-Z][A-Za-z&-]+\s+){1,7}(?:Act|Policy))\b")


@dataclass(frozen=True)
class Entity:
    entity_id: str; name: str; entity_type: str; doc_id: str; chunk_id: str
    page: str; evidence: str; confidence: float


@dataclass(frozen=True)
class Relation:
    relation_id: str; subject: str; relation: str; object: str; doc_id: str
    chunk_id: str; page: str; evidence: str; confidence: float


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:16].upper()
    return f"{prefix}_{digest}"


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCES.split(text) if s.strip()]


def evidence(sentence: str, limit: int = 420) -> str:
    clean = " ".join(sentence.split())
    return clean if len(clean) <= limit else clean[:limit - 1].rstrip() + "…"


def contains(text: str, variant: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(variant) + r"(?!\w)", text, re.I) is not None


def controlled_matches(sentence: str) -> list[tuple[str, str, float]]:
    found = []
    for kind, names in CONTROLLED.items():
        for normalized, variants in names.items():
            if any(contains(sentence, variant) for variant in sorted(variants, key=len, reverse=True)):
                found.append((normalized, kind, CONFIDENCE[kind]))
    return found


def pattern_matches(sentence: str) -> list[tuple[str, str, float]]:
    found = []
    for match in RIVER.finditer(sentence):
        name = " ".join(match.group(1).split())
        name = re.sub(r"^(?:The|ID|MT)\s+", "", name)
        if name not in {"River", "Creek", "This River"} and len(name.split()) <= 4:
            found.append((name, "river", CONFIDENCE["river"]))
    for match in DATE.finditer(sentence):
        found.append((" ".join(match.group(0).split()), "date", CONFIDENCE["date"]))
    for regex, kind in ((PROGRAM_PATTERN, "program"), (POLICY_PATTERN, "policy")):
        for match in regex.finditer(sentence):
            name = " ".join(match.group(1).split())
            # Generic headings and overlong sentence fragments are excluded.
            rejected = {"management program", "conservation program", "the strategy", "national strategy",
                        "restoration program", "schools program", "regulatory program", "wetland program",
                        "control act", "the act", "this act", "water act", "global policy", "planning policy"}
            if len(name.split()) <= 8 and name.lower() not in rejected and not name.startswith("Background "):
                found.append((name, kind, .78))
    return found


def extract() -> tuple[list[Entity], list[Relation]]:
    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute("SELECT chunk_id, doc_id, page, chunk_text FROM chunks ORDER BY chunk_id").fetchall()
    entities: dict[str, Entity] = {}
    relations: dict[str, Relation] = {}
    for chunk_id, doc_id, page, text in rows:
        for sentence in sentences(text):
            matches = controlled_matches(sentence) + pattern_matches(sentence)
            # One normalized entity of each type per chunk is sufficient; keep
            # the first exact evidence sentence for stable output.
            sentence_entities: dict[str, list[str]] = defaultdict(list)
            for name, kind, score in matches:
                eid = stable_id("ENT", kind, name.casefold(), doc_id, chunk_id)
                entities.setdefault(eid, Entity(eid, name, kind, doc_id, chunk_id, page, evidence(sentence), score))
                sentence_entities[kind].append(name)

            for name in set(sentence_entities["species"]):
                add_relation(relations, doc_id, "document_mentions_species", name, doc_id, chunk_id, page, sentence, .98)
            for name in set(sentence_entities["location"]):
                add_relation(relations, doc_id, "document_mentions_location", name, doc_id, chunk_id, page, sentence, .98)

            lower = sentence.casefold()
            if sentence_entities["species"] and (sentence_entities["habitat"] or sentence_entities["wetland"]):
                if re.search(r"\b(use[sd]?|utiliz\w*|depend\w*|occup\w*|nest\w*|habitat for|support\w*|provide\w* habitat)\b", lower):
                    for species in set(sentence_entities["species"]):
                        for habitat in set(sentence_entities["habitat"] + sentence_entities["wetland"]):
                            add_relation(relations, species, "species_uses_habitat", habitat, doc_id, chunk_id, page, sentence, .84)
            if sentence_entities["threat"] and sentence_entities["species"]:
                if re.search(r"\b(affect\w*|threat\w*|harm\w*|impact\w*|declin\w*|mortality|risk to|endanger\w*)\b", lower):
                    for threat in set(sentence_entities["threat"]):
                        for species in set(sentence_entities["species"]):
                            add_relation(relations, threat, "threat_affects_species", species, doc_id, chunk_id, page, sentence, .82)
            if sentence_entities["agency"] and sentence_entities["program"]:
                # Verb forms only: a program title containing "Management"
                # is not itself evidence that the nearby agency manages it.
                if re.search(r"\b(manages|managed|managing|administers|administered|leads|led|implements|implemented|coordinates|coordinated|operates|operated|oversees|responsible for)\b", lower):
                    for agency in set(sentence_entities["agency"]):
                        for program in set(sentence_entities["program"]):
                            add_relation(relations, agency, "agency_manages_program", program, doc_id, chunk_id, page, sentence, .86)
    return sorted(entities.values(), key=lambda x: (x.doc_id, x.chunk_id, x.entity_type, x.name)), sorted(relations.values(), key=lambda x: (x.doc_id, x.chunk_id, x.relation, x.subject, x.object))


def add_relation(store: dict[str, Relation], subject: str, relation: str, obj: str,
                 doc_id: str, chunk_id: str, page: str, sentence: str, confidence: float) -> None:
    rid = stable_id("REL", subject.casefold(), relation, obj.casefold(), doc_id, chunk_id)
    store.setdefault(rid, Relation(rid, subject, relation, obj, doc_id, chunk_id, page, evidence(sentence), confidence))


def write_csvs(entities: list[Entity], relations: list[Relation]) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    with ENTITIES_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(Entity.__dataclass_fields__); writer.writerows([e.__dict__.values() for e in entities])
    with RELATIONS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(Relation.__dataclass_fields__); writer.writerows([r.__dict__.values() for r in relations])


def write_database(entities: list[Entity], relations: list[Relation]) -> None:
    with sqlite3.connect(DATABASE) as connection, connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS entities (entity_id TEXT PRIMARY KEY, name TEXT, entity_type TEXT, doc_id TEXT, chunk_id TEXT, page TEXT, evidence TEXT, confidence REAL);
        CREATE TABLE IF NOT EXISTS relations (relation_id TEXT PRIMARY KEY, subject TEXT, relation TEXT, object TEXT, doc_id TEXT, chunk_id TEXT, page TEXT, evidence TEXT, confidence REAL);
        DELETE FROM relations; DELETE FROM entities;
        """)
        connection.executemany("INSERT INTO entities VALUES (?,?,?,?,?,?,?,?)", [tuple(e.__dict__.values()) for e in entities])
        connection.executemany("INSERT INTO relations VALUES (?,?,?,?,?,?,?,?,?)", [tuple(r.__dict__.values()) for r in relations])


def validate(entities: list[Entity], relations: list[Relation]) -> None:
    ec = Counter(e.entity_type for e in entities); rc = Counter(r.relation for r in relations)
    print(f"Entities: {len(entities)} | unique normalized: {len({(e.name.casefold(), e.entity_type) for e in entities})}")
    print("Entity types:", dict(sorted(ec.items())))
    print(f"Relationships: {len(relations)} | types: {dict(sorted(rc.items()))}")
    print(f"Documents represented: {len({e.doc_id for e in entities})} | chunks represented: {len({e.chunk_id for e in entities})}")
    print(f"Low-confidence entities (<0.80): {sum(e.confidence < .80 for e in entities)}")
    agency_names = {name.casefold() for name in AGENCIES}
    agency_locations = [e for e in entities if e.entity_type == "location" and e.name.casefold() in agency_names]
    generic_species = [e for e in entities if e.entity_type == "species" and e.name.casefold() in {"species", "fish", "birds", "wildlife"}]
    generic_habitats = [e for e in entities if e.entity_type == "habitat" and e.name.casefold() in {"habitat", "area", "land"}]
    date_other_types = [e for e in entities if e.entity_type != "date" and re.fullmatch(r"(?:19|20)\d{2}", e.name)]
    entity_support = {(e.name, e.doc_id, e.chunk_id) for e in entities}
    unsupported = [r for r in relations if r.relation not in {"document_mentions_location", "document_mentions_species"}
                   and ((r.subject, r.doc_id, r.chunk_id) not in entity_support or (r.object, r.doc_id, r.chunk_id) not in entity_support)]
    print("Quality checks:")
    print(f"  agencies misclassified as locations: {len(agency_locations)}")
    print(f"  generic nouns classified as species: {len(generic_species)}")
    print(f"  generic habitat-only names: {len(generic_habitats)}")
    print(f"  bare dates assigned another type: {len(date_other_types)}")
    print(f"  unsupported strong relationships: {len(unsupported)}")
    print("\nENTITY EXAMPLES")
    for kind in sorted(ec):
        sample = next(e for e in entities if e.entity_type == kind)
        print(f"{kind}: {sample.name} | {sample.doc_id} {sample.page} | {sample.evidence[:150]}")
    print("\nRELATION EXAMPLES")
    for kind in sorted(rc):
        sample = next(r for r in relations if r.relation == kind)
        print(f"{kind}: {sample.subject} -> {sample.object} | {sample.doc_id} {sample.page} | {sample.evidence[:150]}")


def main() -> int:
    entities, relations = extract()
    write_csvs(entities, relations); write_database(entities, relations); validate(entities, relations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
