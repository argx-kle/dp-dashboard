"""AT-SCHEMA: the Python models and schema/snapshot.schema.json never drift."""

from __future__ import annotations

from pipeline import contracts
from pipeline.snapshot import load_schema, validate

MODELS = {
    "Snapshot": contracts.Snapshot,
    "SignOff": contracts.SignOff,
    "DomainInfo": contracts.DomainInfo,
    "SourceInfo": contracts.SourceInfo,
    "RegistryInfo": contracts.RegistryInfo,
    "MetricDefinition": contracts.MetricDefinition,
    "FlagDefinition": contracts.FlagDefinition,
    "MetricValue": contracts.MetricValue,
    "GateRecord": contracts.GateRecord,
    "PlannedGate": contracts.PlannedGate,
    "PlannedGA": contracts.PlannedGA,
    "SourcedNumber": contracts.SourcedNumber,
    "SourcedDate": contracts.SourcedDate,
    "ValidationSummary": contracts.ValidationSummary,
    "ComponentScore": contracts.ComponentScore,
    "NextDataSummary": contracts.NextDataSummary,
    "NextDataDeployment": contracts.NextDataDeployment,
    "GithubSummary": contracts.GithubSummary,
    "GithubDeploy": contracts.GithubDeploy,
    "DeliveryBroken": contracts.DeliveryBroken,
    "DeliveryBypass": contracts.DeliveryBypass,
    "Delivery": contracts.Delivery,
    "DeliveryEnv": contracts.DeliveryEnv,
    "DeliveryTotals": contracts.DeliveryTotals,
    "DeliveryWeek": contracts.DeliveryWeek,
    "DeliveryTeam": contracts.DeliveryTeam,
    "RepoEnv": contracts.RepoEnv,
    "DeliveryRepo": contracts.DeliveryRepo,
    "ReportingItem": contracts.ReportingItem,
    "ProductFlag": contracts.ProductFlag,
    "ProductRow": contracts.ProductRow,
    "TrendPoint": contracts.TrendPoint,
    "HealthItem": contracts.HealthItem,
    "WeeklyPoint": contracts.WeeklyPoint,
    "QuarterProduct": contracts.QuarterProduct,
    "QuarterView": contracts.QuarterView,
    "DataQualityItem": contracts.DataQualityItem,
}


def _schema_props(name: str) -> tuple[set[str], set[str]]:
    schema = load_schema()
    node = schema if name == "Snapshot" else schema["definitions"][name]
    return set(node["properties"]), set(node.get("required", []))


def test_at_schema_01_every_definition_has_a_model():
    schema = load_schema()
    assert set(schema["definitions"]) == set(MODELS) - {"Snapshot"}


def test_at_schema_02_fields_match_schema_properties():
    for name, model in MODELS.items():
        props, required = _schema_props(name)
        fields = set(model.model_fields)
        assert fields == props, f"{name}: model fields {fields ^ props} differ from schema"
        model_required = {k for k, f in model.model_fields.items() if f.is_required()}
        assert model_required == required, f"{name}: required mismatch {model_required ^ required}"


def test_at_schema_03_golden_snapshot_validates(golden_snapshot):
    assert validate(golden_snapshot) == []


def test_at_schema_04_schema_rejects_unknown_fields(golden_snapshot):
    bad = dict(golden_snapshot)
    bad["extra"] = 1
    assert any("extra" in i.message for i in validate(bad))
