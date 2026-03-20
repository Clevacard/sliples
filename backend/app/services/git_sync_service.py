"""Git repository sync service for scenario management."""

import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from git import Repo, GitCommandError
from sqlalchemy.orm import Session

from app.models import Scenario, ScenarioRepo

logger = logging.getLogger(__name__)

# Base directory for cloned repositories
REPOS_BASE_DIR = Path("/Users/ptrk/Agantis/sliples/backend/scenarios")


@dataclass
class ParsedScenario:
    """Parsed scenario from a .feature file."""

    name: str
    feature_path: str
    content: str
    tags: list[str]


class FeatureFileParser:
    """Parser for Gherkin .feature files."""

    # Regex patterns for parsing feature files
    TAG_PATTERN = re.compile(r"@(\w+)")
    FEATURE_PATTERN = re.compile(r"^\s*Feature:\s*(.+)$", re.MULTILINE)
    SCENARIO_PATTERN = re.compile(
        r"^\s*(?:(@[\w\s@]+)\s*\n)?\s*Scenario(?:\s+Outline)?:\s*(.+)$",
        re.MULTILINE,
    )

    @classmethod
    def parse_feature_file(cls, file_path: Path, relative_path: str) -> list[ParsedScenario]:
        """
        Parse a .feature file and extract scenarios.

        Args:
            file_path: Absolute path to the .feature file
            relative_path: Path relative to the repo sync_path

        Returns:
            List of parsed scenarios
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read feature file {file_path}: {e}")
            return []

        scenarios = []

        # Extract feature-level tags
        feature_match = cls.FEATURE_PATTERN.search(content)
        feature_name = feature_match.group(1).strip() if feature_match else "Unknown Feature"

        # Find feature-level tags (tags before Feature: keyword)
        feature_start = feature_match.start() if feature_match else 0
        pre_feature_content = content[:feature_start]
        feature_tags = cls.TAG_PATTERN.findall(pre_feature_content)

        # Find all scenarios
        scenario_matches = list(cls.SCENARIO_PATTERN.finditer(content))

        for i, match in enumerate(scenario_matches):
            scenario_tags_str = match.group(1) or ""
            scenario_name = match.group(2).strip()

            # Extract tags for this scenario
            scenario_tags = cls.TAG_PATTERN.findall(scenario_tags_str)

            # Combine feature and scenario tags
            all_tags = list(set(feature_tags + scenario_tags))

            # Extract scenario content (from this scenario to the next or end)
            start_pos = match.start()
            if i + 1 < len(scenario_matches):
                end_pos = scenario_matches[i + 1].start()
            else:
                end_pos = len(content)

            scenario_content = content[start_pos:end_pos].strip()

            scenarios.append(
                ParsedScenario(
                    name=f"{feature_name}: {scenario_name}",
                    feature_path=relative_path,
                    content=scenario_content,
                    tags=all_tags,
                )
            )

        # If no scenarios found, treat the whole feature as one scenario
        if not scenarios and feature_match:
            scenarios.append(
                ParsedScenario(
                    name=feature_name,
                    feature_path=relative_path,
                    content=content,
                    tags=feature_tags,
                )
            )

        return scenarios


class GitSyncService:
    """Service for syncing git repositories and extracting scenarios."""

    def __init__(self, db: Session):
        """
        Initialize the git sync service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._ensure_base_dir()

    def _ensure_base_dir(self):
        """Ensure the base directory for repos exists."""
        REPOS_BASE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_repo_path(self, repo: ScenarioRepo) -> Path:
        """Get the local path for a repository."""
        # Use repo name as directory name (sanitized)
        safe_name = re.sub(r"[^\w\-]", "_", repo.name)
        return REPOS_BASE_DIR / safe_name

    def clone_or_pull(self, repo: ScenarioRepo) -> tuple[bool, str]:
        """
        Clone a repository or pull if it already exists.

        Args:
            repo: The ScenarioRepo to sync

        Returns:
            Tuple of (success, message)
        """
        repo_path = self._get_repo_path(repo)

        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                # Repository exists, pull latest changes
                logger.info(f"Pulling latest changes for {repo.name}")
                git_repo = Repo(repo_path)

                # Fetch and checkout the configured branch
                origin = git_repo.remotes.origin
                origin.fetch()

                # Check out the branch
                if repo.branch in git_repo.heads:
                    git_repo.heads[repo.branch].checkout()
                else:
                    # Create local tracking branch if it doesn't exist
                    git_repo.create_head(repo.branch, origin.refs[repo.branch])
                    git_repo.heads[repo.branch].checkout()

                # Pull the latest
                origin.pull(repo.branch)

                return True, f"Successfully pulled latest changes for {repo.name}"
            else:
                # Clone the repository
                logger.info(f"Cloning repository {repo.name} from {repo.git_url}")

                # Remove directory if it exists but isn't a git repo
                if repo_path.exists():
                    import shutil

                    shutil.rmtree(repo_path)

                git_repo = Repo.clone_from(
                    repo.git_url,
                    repo_path,
                    branch=repo.branch,
                )

                return True, f"Successfully cloned {repo.name}"

        except GitCommandError as e:
            error_msg = f"Git error syncing {repo.name}: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error syncing {repo.name}: {e}"
            logger.error(error_msg)
            return False, error_msg

    def find_feature_files(self, repo: ScenarioRepo) -> list[tuple[Path, str]]:
        """
        Find all .feature files in the repository's sync path.

        Args:
            repo: The ScenarioRepo to search

        Returns:
            List of tuples (absolute_path, relative_path)
        """
        repo_path = self._get_repo_path(repo)
        sync_path = repo_path / repo.sync_path

        if not sync_path.exists():
            logger.warning(f"Sync path {sync_path} does not exist for repo {repo.name}")
            return []

        feature_files = []
        for feature_file in sync_path.rglob("*.feature"):
            relative_path = str(feature_file.relative_to(sync_path))
            feature_files.append((feature_file, relative_path))

        return feature_files

    def sync_scenarios(self, repo: ScenarioRepo) -> tuple[int, int, list[str]]:
        """
        Sync scenarios from a repository to the database.

        Args:
            repo: The ScenarioRepo to sync

        Returns:
            Tuple of (created_count, updated_count, errors)
        """
        created_count = 0
        updated_count = 0
        errors = []

        feature_files = self.find_feature_files(repo)

        # Get existing scenarios for this repo
        existing_scenarios = {
            s.feature_path: s for s in self.db.query(Scenario).filter(Scenario.repo_id == repo.id).all()
        }

        processed_paths = set()

        for file_path, relative_path in feature_files:
            parsed_scenarios = FeatureFileParser.parse_feature_file(file_path, relative_path)

            for parsed in parsed_scenarios:
                # Create a unique path key for the scenario
                scenario_key = f"{parsed.feature_path}:{parsed.name}"
                processed_paths.add(scenario_key)

                # Check if scenario exists
                existing = None
                for key, scenario in existing_scenarios.items():
                    if key == parsed.feature_path and scenario.name == parsed.name:
                        existing = scenario
                        break

                if existing:
                    # Update existing scenario
                    existing.content = parsed.content
                    existing.tags = parsed.tags
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new scenario
                    new_scenario = Scenario(
                        repo_id=repo.id,
                        name=parsed.name,
                        feature_path=parsed.feature_path,
                        content=parsed.content,
                        tags=parsed.tags,
                    )
                    self.db.add(new_scenario)
                    created_count += 1

        # Remove scenarios that no longer exist in the repo
        for key, scenario in existing_scenarios.items():
            scenario_key = f"{scenario.feature_path}:{scenario.name}"
            if scenario_key not in processed_paths:
                self.db.delete(scenario)

        # Update last_synced timestamp
        repo.last_synced = datetime.utcnow()

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            errors.append(f"Database error: {e}")
            return 0, 0, errors

        return created_count, updated_count, errors

    def full_sync(self, repo: ScenarioRepo) -> dict:
        """
        Perform a full sync: clone/pull and update scenarios.

        Args:
            repo: The ScenarioRepo to sync

        Returns:
            Dict with sync results
        """
        result = {
            "repo_id": str(repo.id),
            "repo_name": repo.name,
            "success": False,
            "git_message": "",
            "created": 0,
            "updated": 0,
            "errors": [],
        }

        # Step 1: Clone or pull
        success, message = self.clone_or_pull(repo)
        result["git_message"] = message

        if not success:
            result["errors"].append(message)
            return result

        # Step 2: Sync scenarios to database
        created, updated, errors = self.sync_scenarios(repo)
        result["created"] = created
        result["updated"] = updated
        result["errors"].extend(errors)
        result["success"] = len(errors) == 0

        return result

    def sync_all_repos(self) -> list[dict]:
        """
        Sync all repositories.

        Returns:
            List of sync results for each repo
        """
        repos = self.db.query(ScenarioRepo).all()
        results = []

        for repo in repos:
            result = self.full_sync(repo)
            results.append(result)

        return results
