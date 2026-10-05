from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from daube_bridge.model import SkillContract  # noqa: E402

SCHEMA_PATH = ROOT / "schema" / "skill.schema.json"


def build_schema() -> dict:
    schema = SkillContract.model_json_schema(mode="validation")
    schema["title"] = "D'AUBE BRIDGE² Skill"
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://daubesonntag.com/bridge/skill.schema.json",
        **schema,
    }


def main() -> int:
    SCHEMA_PATH.write_text(
        json.dumps(build_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
