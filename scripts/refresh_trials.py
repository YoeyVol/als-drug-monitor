#!/usr/bin/env python3
"""Refresh tracked ALS trial records from the public ClinicalTrials.gov API.

The curated NCT ID list is deliberately not reselected here. Only those records'
registry-derived fields are refreshed; curation scope and tracked membership stay
under version control in data/trials.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://clinicaltrials.gov/api/v2/studies/{}"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_PHASES = {"EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4", "NA"}


class RefreshError(RuntimeError):
    """Raised when the registry response is unavailable or structurally invalid."""


def get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "ALS-Drug-Monitor/1.0"})
    try:
        with urlopen(request, timeout=45) as response:
            if response.status != 200:
                raise RefreshError(f"Unexpected HTTP status {response.status} for {url}")
            payload = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RefreshError(f"ClinicalTrials.gov request failed for {url}: {exc}") from exc
    try:
        result = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RefreshError(f"Invalid JSON returned for {url}: {exc}") from exc
    if not isinstance(result, dict):
        raise RefreshError(f"Expected a JSON object from {url}")
    return result


def map_study(study: dict, expected_nct: str) -> dict:
    try:
        protocol = study["protocolSection"]
        identification = protocol["identificationModule"]
        status = protocol["statusModule"]
        design = protocol["designModule"]
        interventions_module = protocol["armsInterventionsModule"]
        conditions_module = protocol["conditionsModule"]
        sponsor_module = protocol["sponsorCollaboratorsModule"]
        nct_id = identification["nctId"]
        title = identification["briefTitle"]
        overall_status = status["overallStatus"]
        updated = status["lastUpdatePostDateStruct"]["date"]
        conditions = conditions_module["conditions"]
        interventions = interventions_module["interventions"]
        phases = design.get("phases") or ["NA"]
        study_type = design["studyType"]
        sponsor = sponsor_module["leadSponsor"]["name"]
        has_results = study["hasResults"]
    except (KeyError, TypeError) as exc:
        raise RefreshError(f"Malformed ClinicalTrials.gov study for {expected_nct}: missing/invalid {exc}") from exc

    if nct_id != expected_nct:
        raise RefreshError(f"API returned {nct_id!r} for requested {expected_nct}")
    if not isinstance(title, str) or not title.strip():
        raise RefreshError(f"Missing title for {expected_nct}")
    if not isinstance(overall_status, str) or not overall_status:
        raise RefreshError(f"Missing overall status for {expected_nct}")
    if not isinstance(updated, str) or not DATE_RE.fullmatch(updated):
        raise RefreshError(f"Invalid last update date for {expected_nct}: {updated!r}")
    if not isinstance(conditions, list) or not all(isinstance(x, str) for x in conditions):
        raise RefreshError(f"Invalid conditions for {expected_nct}")
    if not isinstance(phases, list) or not phases or any(x not in VALID_PHASES for x in phases):
        raise RefreshError(f"Invalid phase value(s) for {expected_nct}: {phases!r}")
    if not isinstance(interventions, list):
        raise RefreshError(f"Invalid interventions for {expected_nct}")
    drug_interventions = list(dict.fromkeys(
        item["name"] for item in interventions
        if isinstance(item, dict)
        and item.get("type") in {"DRUG", "BIOLOGICAL"}
        and isinstance(item.get("name"), str)
        and item["name"].strip()
    ))
    if not drug_interventions:
        raise RefreshError(f"Tracked record {expected_nct} no longer has a drug/biological intervention")
    if study_type != "INTERVENTIONAL":
        raise RefreshError(f"Tracked record {expected_nct} is no longer interventional")
    if not isinstance(sponsor, str) or not sponsor.strip():
        raise RefreshError(f"Missing lead sponsor for {expected_nct}")
    if not isinstance(has_results, bool):
        raise RefreshError(f"Invalid hasResults value for {expected_nct}")

    return {
        "nctId": nct_id,
        "title": title,
        "interventions": drug_interventions,
        "conditions": conditions,
        "phase": phases,
        "status": overall_status,
        "lastUpdatePosted": updated,
        "hasResults": has_results,
        "sponsor": sponsor,
        "sourceUrl": f"https://clinicaltrials.gov/study/{nct_id}",
        "studyType": study_type,
    }


def refresh(input_path: Path, output_path: Path) -> None:
    try:
        source = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RefreshError(f"Cannot read existing curated file {input_path}: {exc}") from exc
    if not isinstance(source, dict) or source.get("schemaVersion") != 1:
        raise RefreshError("Existing curated file must be an object with schemaVersion 1")
    trials = source.get("trials")
    if not isinstance(trials, list) or not trials:
        raise RefreshError("Existing curated file must contain a non-empty trials array")
    tracked_ids = []
    for entry in trials:
        if not isinstance(entry, dict) or not isinstance(entry.get("nctId"), str):
            raise RefreshError("Every tracked trial must be an object with a string nctId")
        tracked_ids.append(entry["nctId"])
    if len(tracked_ids) != len(set(tracked_ids)):
        raise RefreshError("Duplicate nctId in curated selection")

    # Fetch and validate everything before creating/replacing the destination.
    refreshed = []
    for nct_id in tracked_ids:
        payload = get_json(API.format(nct_id))
        refreshed.append(map_study(payload, nct_id))

    result = {
        "schemaVersion": 1,
        "retrievedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": source.get("scope", "中文精选非全部；固定跟踪名单"),
        "trials": refreshed,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=output_path.parent,
            prefix=f".{output_path.name}.", suffix=".tmp", delete=False
        ) as temp:
            temp_name = temp.name
            json.dump(result, temp, ensure_ascii=False, indent=2)
            temp.write("\n")
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(temp_name, output_path)
    except OSError:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        help="destination JSON path (default: data/trials.json); temporary file is created beside it",
    )
    args = parser.parse_args()
    input_path = root / "data" / "trials.json"
    output_path = args.output.resolve() if args.output else input_path
    try:
        refresh(input_path, output_path)
    except RefreshError as exc:
        parser.exit(1, f"refresh_trials.py: error: {exc}\n")
    except OSError as exc:
        parser.exit(1, f"refresh_trials.py: error: cannot atomically write output: {exc}\n")
    print(f"Refreshed {input_path} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
