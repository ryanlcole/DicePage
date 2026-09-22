from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "apps" / "rist-world"


def load_builder():
    path = APP / "prepare_relic_observer.py"
    spec = importlib.util.spec_from_file_location("prepare_relic_observer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_relic_observer_public_seed_is_public_only_and_source_linked():
    builder = load_builder()
    seed = builder.build_seed()
    assert builder.validate_seed(seed) is True
    assert seed["datasetId"] == "shaelvien-project-knowledge"
    assert seed["sources"]
    assert seed["records"]
    ids = {source["sourceId"] for source in seed["sources"]}
    assert all(source["visibility"].startswith("public") for source in seed["sources"])
    assert all("content" not in source for source in seed["sources"])
    assert all(record["sourceIds"] for record in seed["records"])
    assert all(set(record["sourceIds"]).issubset(ids) for record in seed["records"])


def test_relic_observer_preserves_epistemic_domains():
    builder = load_builder()
    seed = builder.build_seed()
    domains = {record["truthDomain"] for record in seed["records"]}
    assert domains
    assert domains.issubset({"FACT", "HYPOTHESIS", "FICTION", "UNKNOWN"})


def test_relic_observer_is_authenticated_workspace_not_public_private_dump():
    shell = (APP / "Components" / "PublicAlphaShell.razor").read_text(encoding="utf-8")
    router = (APP / "Components" / "TaskWorkspaceRouter.razor").read_text(encoding="utf-8")
    service = (APP / "ReLiCObserverService.cs").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "RELIC_OBSERVER_ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "RELIC OBSERVER" in shell
    assert 'Mode == "observer"' in router
    assert "<ReLiCObserverWorkspace" in router
    assert 'relic-observer/corpus.v1.json' in service
    assert "DownloadJsonAsync<ObserverPrivateCorpus>" in service
    assert "UploadTextAsync(PrivateCorpusKey" in service
    assert "public repository" in architecture
    assert "A query working set is **not a SHAEP**" in architecture
    assert "eval(" not in service.lower()
