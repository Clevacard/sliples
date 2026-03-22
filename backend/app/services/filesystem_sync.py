"""Filesystem sync service - scans /scenarios folder and syncs to database."""

import os
import re
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Scenario

logger = logging.getLogger(__name__)

# Base directory for scenarios (relative to project root)
SCENARIOS_DIR = Path("/app/scenarios")


@dataclass
class ParsedFeature:
    """Parsed feature from a .feature file."""
    name: str
    feature_path: str
    content: str
    tags: list[str]
    scenarios: list[dict]  # List of {name, tags} for each scenario in the file


class FeatureParser:
    """Parser for Gherkin .feature files."""

    TAG_PATTERN = re.compile(r"@([\w-]+)")
    FEATURE_PATTERN = re.compile(r"^\s*Feature:\s*(.+)$", re.MULTILINE)
    SCENARIO_PATTERN = re.compile(
        r"(?:^[ \t]*((?:@[\w-]+[ \t]*)+)\n)?^[ \t]*Scenario(?:\s+Outline)?:\s*(.+)$",
        re.MULTILINE,
    )

    @classmethod
    def parse_file(cls, file_path: Path, relative_path: str) -> Optional[ParsedFeature]:
        """Parse a .feature file and extract feature info and scenarios."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None

        # Extract feature name
        feature_match = cls.FEATURE_PATTERN.search(content)
        feature_name = feature_match.group(1).strip() if feature_match else file_path.stem

        # Extract file-level tags (tags before Feature:)
        file_tags = []
        feature_pos = content.find("Feature:")
        if feature_pos > 0:
            pre_feature = content[:feature_pos]
            file_tags = cls.TAG_PATTERN.findall(pre_feature)

        # Extract scenarios
        scenarios = []
        for match in cls.SCENARIO_PATTERN.finditer(content):
            scenario_tags_str = match.group(1) or ""
            scenario_name = match.group(2).strip()
            scenario_tags = cls.TAG_PATTERN.findall(scenario_tags_str)
            scenarios.append({
                "name": scenario_name,
                "tags": list(set(file_tags + scenario_tags)),
            })

        return ParsedFeature(
            name=feature_name,
            feature_path=relative_path,
            content=content,
            tags=file_tags,
            scenarios=scenarios,
        )


def sync_filesystem_to_db(db: Session, scenarios_dir: Path = SCENARIOS_DIR) -> dict:
    """
    Scan the scenarios directory and sync all .feature files to the database.

    Returns stats about what was synced.
    """
    stats = {
        "scanned": 0,
        "added": 0,
        "updated": 0,
        "deleted": 0,
        "errors": [],
    }

    if not scenarios_dir.exists():
        logger.warning(f"Scenarios directory does not exist: {scenarios_dir}")
        stats["errors"].append(f"Directory not found: {scenarios_dir}")
        return stats

    # Find all .feature files
    feature_files = list(scenarios_dir.rglob("*.feature"))
    stats["scanned"] = len(feature_files)
    logger.info(f"Found {len(feature_files)} .feature files in {scenarios_dir}")

    # Track which paths we've seen (to detect deleted files)
    seen_paths = set()

    for file_path in feature_files:
        # Calculate relative path from scenarios_dir
        relative_path = str(file_path.relative_to(scenarios_dir.parent))
        seen_paths.add(relative_path)

        # Parse the file
        parsed = FeatureParser.parse_file(file_path, relative_path)
        if not parsed:
            stats["errors"].append(f"Failed to parse: {relative_path}")
            continue

        # For each scenario in the file, create/update a database record
        if parsed.scenarios:
            for scenario_info in parsed.scenarios:
                scenario_name = scenario_info["name"]
                scenario_tags = scenario_info["tags"]

                # Look for existing scenario by feature_path + name
                existing = db.query(Scenario).filter(
                    Scenario.feature_path == relative_path,
                    Scenario.name == scenario_name,
                ).first()

                if existing:
                    # Update if content changed
                    if existing.content != parsed.content or set(existing.tags or []) != set(scenario_tags):
                        existing.content = parsed.content
                        existing.tags = scenario_tags
                        stats["updated"] += 1
                        logger.debug(f"Updated scenario: {scenario_name}")
                else:
                    # Create new scenario
                    new_scenario = Scenario(
                        name=scenario_name,
                        feature_path=relative_path,
                        content=parsed.content,
                        tags=scenario_tags,
                    )
                    db.add(new_scenario)
                    stats["added"] += 1
                    logger.debug(f"Added scenario: {scenario_name}")
        else:
            # No scenarios found, create one entry for the feature file itself
            existing = db.query(Scenario).filter(
                Scenario.feature_path == relative_path,
            ).first()

            if existing:
                if existing.content != parsed.content or existing.name != parsed.name:
                    existing.content = parsed.content
                    existing.name = parsed.name
                    existing.tags = parsed.tags
                    stats["updated"] += 1
            else:
                new_scenario = Scenario(
                    name=parsed.name,
                    feature_path=relative_path,
                    content=parsed.content,
                    tags=parsed.tags,
                )
                db.add(new_scenario)
                stats["added"] += 1

    # Delete scenarios whose files no longer exist
    all_scenarios = db.query(Scenario).all()
    for scenario in all_scenarios:
        if scenario.feature_path not in seen_paths:
            db.delete(scenario)
            stats["deleted"] += 1
            logger.debug(f"Deleted scenario (file removed): {scenario.name}")

    db.commit()
    logger.info(f"Sync complete: {stats}")
    return stats
