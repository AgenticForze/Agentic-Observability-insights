import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "observability-platform-analyst"


def test_skill_has_front_matter():
    text = (SKILL / "SKILL.md").read_text()
    assert text.startswith("---\nname: observability-platform-analyst\ndescription: ")


def test_skill_references_match_data():
    for name in ("platforms.yaml", "criteria.yaml"):
        assert (SKILL / "references" / name).read_bytes() == (ROOT / "data" / name).read_bytes(), name


def test_rank_script_json():
    out = subprocess.run([sys.executable, str(SKILL / "scripts" / "rank.py"), "--preset", "startup",
                          "--must", "otel", "--json"], capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    assert data["ranking"][0]["missing"] == []
    assert len(data["ranking"]) == 9


def test_rank_script_rejects_bad_input():
    out = subprocess.run([sys.executable, str(SKILL / "scripts" / "rank.py"), "--preset", "nope"],
                         capture_output=True, text=True)
    assert out.returncode != 0 and "Unknown preset" in out.stderr


def test_site_build(tmp_path):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], check=True, capture_output=True)
    content = json.loads((ROOT / "site" / "content.json").read_text())
    assert {"platforms", "criteria", "insights", "carousels", "reports", "review", "files"} <= set(content)
    assert any(f["path"] == "README.md" for f in content["files"])
