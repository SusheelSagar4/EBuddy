import os
import re
import pytest

def test_no_external_references_in_static_and_templates():
    """
    Hard Rule: Zero external outbound network calls from frontend assets.
    Verifies that no file under app/static or app/templates references http:// or https://.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))
    static_dir = os.path.join(base_dir, "static")
    templates_dir = os.path.join(base_dir, "templates")

    target_dirs = [static_dir, templates_dir]
    url_pattern = re.compile(r"https?://", re.IGNORECASE)

    violations = []
    scanned_files = 0

    for d in target_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                scanned_files += 1
                filepath = os.path.join(root, f)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    matches = url_pattern.findall(content)
                    if matches:
                        violations.append((filepath, len(matches)))

    assert scanned_files > 0, "No static or template files were found to scan!"
    assert not violations, f"Forbidden external URLs (http:// or https://) found in frontend assets: {violations}"
