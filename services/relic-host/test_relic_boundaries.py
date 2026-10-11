import relic_boundaries as boundaries
import environment_advisor


def test_project_keys_isolate_owner_and_project():
    a = boundaries.ProjectScope("owner-a", "project-1")
    b = boundaries.ProjectScope("owner-a", "project-2")
    c = boundaries.ProjectScope("owner-b", "project-1")
    assert a.key != b.key
    assert a.key != c.key
    boundaries.assert_same_project(a, a.key)


def test_cross_project_access_is_denied():
    a = boundaries.ProjectScope("owner-a", "project-1")
    b = boundaries.ProjectScope("owner-a", "project-2")
    try:
        boundaries.assert_same_project(a, b.key)
    except boundaries.BoundaryViolation:
        pass
    else:
        raise AssertionError("cross-project access was not denied")


def test_universal_sanitization_removes_obvious_private_and_security_data():
    source = {
        "error": "failed at C:\\Users\\alice\\private\\build.py from 10.2.3.4; contact alice@example.com",
        "api_key": "never-share-this",
        "nested": {"authorization": "Bearer abc.def.ghi", "cause": "timeout"},
    }
    clean = boundaries.sanitize_for_universal(source)
    rendered = boundaries.canonical(clean)
    assert "alice@example.com" not in rendered
    assert "never-share-this" not in rendered
    assert "10.2.3.4" not in rendered
    assert "Bearer abc.def.ghi" not in rendered
    assert "cause" in rendered
    assert boundaries.contains_obvious_sensitive_data(source)


def test_environment_observation_remains_advisory():
    wrapped = boundaries.classify_environment_observation({"cpu_percent": 91})
    assert wrapped["domain"] == "ENVIRONMENT"
    assert wrapped["authority"] == "ADVISORY_ONLY"
    assert wrapped["hardware_harm_established"] is False
    assert wrapped["causation_established"] is False


def test_environment_thresholds_are_policy_not_hardware_truth():
    warnings = environment_advisor.analyze(
        {"memory_percent": 94, "temperature_c": 88},
        {"memory_warn_percent": 90, "temperature_warn_c": 85},
    )
    assert {w["code"] for w in warnings} == {"MEMORY_PRESSURE", "THERMAL_POLICY"}
    assert all(w["hardware_harm_established"] is False for w in warnings)
    assert all(w["threshold_source"] == "PROJECT_OR_OPERATOR_POLICY" for w in warnings)


def test_language_change_requires_benchmarking_not_telemetry_guess():
    warnings = environment_advisor.analyze({"profile_bottleneck": "CPU parser loop"})
    item = next(w for w in warnings if w["code"] == "PROFILE_BOTTLENECK")
    assert item["language_change_justified"] is False
    assert "benchmarks" in item["recommendation"]
