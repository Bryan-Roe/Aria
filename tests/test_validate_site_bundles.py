from __future__ import annotations

import json

from scripts.validate_site_bundles import validate_bundle


REQUIRED_BASE_FILES = {
    "index.html": "<html></html>",
    "style.css": "body{}",
    "script.js": "console.log('ok')",
}


def _write_base_bundle(tmp_path, name: str = "bundle"):
    bundle = tmp_path / name
    bundle.mkdir()
    for filename, content in REQUIRED_BASE_FILES.items():
        (bundle / filename).write_text(content, encoding="utf-8")
    return bundle


def test_validate_bundle_default_allows_missing_metadata(tmp_path):
    bundle = _write_base_bundle(tmp_path)

    errors = validate_bundle(bundle, strict_metadata=False)

    assert errors == []


def test_validate_bundle_strict_requires_metadata_file(tmp_path):
    bundle = _write_base_bundle(tmp_path)

    errors = validate_bundle(bundle, strict_metadata=True)

    assert "missing required file: metadata.json" in errors


def test_validate_bundle_reports_missing_required_base_files(tmp_path):
    bundle = tmp_path / "broken"
    bundle.mkdir()
    (bundle / "index.html").write_text("<html></html>", encoding="utf-8")

    errors = validate_bundle(bundle)

    assert any("missing required files:" in err for err in errors)
    assert any("style.css" in err and "script.js" in err for err in errors)


def test_validate_bundle_metadata_schema_enforced(tmp_path):
    bundle = _write_base_bundle(tmp_path)
    (bundle / "metadata.json").write_text(json.dumps({"name": 123}), encoding="utf-8")

    errors = validate_bundle(bundle)

    assert any("metadata key 'name' must be str" in err for err in errors)
    assert any("metadata missing key: pages" in err for err in errors)
    assert any("metadata missing key: features" in err for err in errors)
    assert any("metadata missing key: files" in err for err in errors)


def test_validate_bundle_strict_requires_metadata_list_entry(tmp_path):
    bundle = _write_base_bundle(tmp_path)
    metadata = {
        "name": "bundle",
        "pages": ["index"],
        "features": ["x"],
        "files": ["index.html", "style.css", "script.js"],
    }
    (bundle / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    errors = validate_bundle(bundle, strict_metadata=True)

    assert any("metadata.files missing required entries: metadata.json" in err for err in errors)


def test_validate_bundle_strict_passes_when_complete(tmp_path):
    bundle = _write_base_bundle(tmp_path)
    metadata = {
        "name": "bundle",
        "pages": ["index"],
        "features": ["starter"],
        "files": ["index.html", "style.css", "script.js", "metadata.json"],
    }
    (bundle / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    errors = validate_bundle(bundle, strict_metadata=True)

    assert errors == []
