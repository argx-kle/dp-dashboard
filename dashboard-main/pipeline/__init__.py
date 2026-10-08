"""dp pipeline: inbox files in, snapshot JSON out.

Modules only depend on the two contracts (inbox tables, snapshot schema) and the registries.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "registry"
SCHEMA_PATH = ROOT / "schema" / "snapshot.schema.json"
TEMPLATE_PATH = ROOT / "app" / "dist" / "template.html"
SCHEMA_VERSION = "1.0"
