from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_MAP = PACKAGE_ROOT / "config" / "project_map.json"
DEFAULT_PLAYBOOKS = PACKAGE_ROOT / "config" / "playbooks.json"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="0.0.0.0", alias="OCIANA_CHATBOT_HOST")
    port: int = Field(default=8080, alias="OCIANA_CHATBOT_PORT")
    log_level: str = Field(default="INFO", alias="OCIANA_CHATBOT_LOG_LEVEL")
    api_key: str = Field(default="change-me", alias="OCIANA_CHATBOT_API_KEY")

    jira_base_url: str = Field(default="", alias="JIRA_BASE_URL")
    jira_email: str = Field(default="", alias="JIRA_EMAIL")
    jira_api_token: str = Field(default="", alias="JIRA_API_TOKEN")
    jira_default_project_key: str = Field(default="SUP", alias="JIRA_DEFAULT_PROJECT_KEY")
    jira_issue_type: str = Field(default="Task", alias="JIRA_ISSUE_TYPE")
    jira_dry_run: bool = Field(default=True, alias="JIRA_DRY_RUN")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-3-5-sonnet-latest", alias="CLAUDE_MODEL")
    use_claude_classifier: bool = Field(default=False, alias="USE_CLAUDE_CLASSIFIER")

    project_map_path: Path = Field(default=DEFAULT_PROJECT_MAP, alias="PROJECT_MAP_PATH")
    playbooks_path: Path = Field(default=DEFAULT_PLAYBOOKS, alias="PLAYBOOKS_PATH")


@lru_cache
def get_settings() -> Settings:
    return Settings()
