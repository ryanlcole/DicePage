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
    assert 'TryRequestedWorkspace(out var requested)' in shell
    assert '"workspace"' in shell
    assert 'Mode == "observer"' in router
    assert "<ReLiCObserverWorkspace" in router
    assert 'relic-observer/corpus.v1.json' in service
    assert "DownloadJsonAsync<ObserverPrivateCorpus>" in service
    assert "UploadTextAsync(PrivateCorpusKey" in service
    assert "public repository" in architecture
    assert "A query working set is **not a SHAEP**" in architecture
    assert "eval(" not in service.lower()


def test_relic_observer_associative_recall_is_sparse_bounded_and_visible():
    service = (APP / "ReLiCObserverService.cs").read_text(encoding="utf-8")
    workspace = (APP / "Components" / "ReLiCObserverWorkspace.razor").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "RELIC_OBSERVER_ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "const int MaxAssociationNeighbors = 6;" in service
    assert "const int AssociationSeedCount = 6;" in service
    assert "const double AssociationExpansionFactor = 0.28;" in service
    assert "BuildAssociations();" in service
    assert "foreach(var seed in seeds)" in service
    assert "ASSOCIATED via" in service
    assert "AssociationEdgeCount" in service
    assert 'data-kind="@hit.RetrievalKind"' in workspace
    assert "@hit.RetrievalKind" in workspace
    assert "sparse associations" in workspace
    assert "There is deliberately no unrestricted recursive walk." in architecture


def test_relic_observer_seed_observes_selected_current_and_historical_repo_sources():
    builder = load_builder()
    seed = builder.build_seed()
    titles = {source["title"] for source in seed["sources"]}
    assert seed["overlaySourceCount"] > 0
    assert seed["overlayRecordCount"] > 0
    assert "relic_core.py" in titles
    assert "relic_analyzer.py" in titles
    assert "glyph_ai_core.py" in titles
    assert "shaelvien_ai_adapter.py" in titles
    assert "docs/RELIC_OBSERVER_ARCHITECTURE.md" in titles
    assert all(source["visibility"] == "public-existing-source" for source in seed["sources"])
    assert all("content" not in source for source in seed["sources"])


def test_relic_observer_evidence_packet_is_bounded_to_returned_evidence():
    service = (APP / "ReLiCObserverService.cs").read_text(encoding="utf-8")
    workspace = (APP / "Components" / "ReLiCObserverWorkspace.razor").read_text(encoding="utf-8")
    assert 'contract="relic.observer.evidence-packet"' in service
    assert "evidence=answer.Hits.Select" in service
    assert "excerpt=hit.Excerpt" in service
    assert "BuildEvidencePacket(_answer)" in workspace
    assert "COPY EVIDENCE PACKET" in workspace


def test_relic_observer_follow_up_context_is_bounded_and_explicit():
    service = (APP / "ReLiCObserverService.cs").read_text(encoding="utf-8")
    workspace = (APP / "Components" / "ReLiCObserverWorkspace.razor").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "RELIC_OBSERVER_ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "const int MaxConversationTurns = 4;" in service
    assert "const double ConversationContextFactor = 0.22;" in service
    assert "ShouldUseConversationContext" in service
    assert "BuildConversationTerms" in service
    assert "ClearConversationContext" in service
    assert 'RetrievalKind=kind' in service
    assert '"CONTEXT"' in service
    assert "CLEAR CONTEXT" in workspace
    assert "ConversationContextAvailable" in workspace
    assert "Only the last four turns are retained" in architecture


def test_relic_observer_intent_routing_and_conflict_visibility_are_deterministic():
    service = (APP / "ReLiCObserverService.cs").read_text(encoding="utf-8")
    workspace = (APP / "Components" / "ReLiCObserverWorkspace.razor").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "RELIC_OBSERVER_ARCHITECTURE.md").read_text(encoding="utf-8")

    assert 'return "SOURCE";' in service
    assert 'return "STATUS";' in service
    assert 'return "HISTORY";' in service
    assert 'return "GENERAL";' in service
    assert "ExplicitConflict=explicitConflict" in service
    assert "does not select a winner" in service
    assert "UNRESOLVED SOURCE CONFLICT PRESENT" in workspace
    assert "Deterministic intent shaping" in architecture


def test_relic_observer_evidence_scope_is_explicit_and_clears_follow_up_context():
    service = (APP / "ReLiCObserverService.cs").read_text(encoding="utf-8")
    workspace = (APP / "Components" / "ReLiCObserverWorkspace.razor").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "RELIC_OBSERVER_ARCHITECTURE.md").read_text(encoding="utf-8")

    assert 'string evidenceFilter="all"' in service
    assert '"current"=>!historical' in service
    assert '"historical"=>historical' in service
    assert '"public"=>evidence.Visibility.StartsWith("public"' in service
    assert '"private"=>evidence.Visibility.StartsWith("private"' in service
    assert 'id="observer-filter"' in workspace
    assert "Observer.ClearConversationContext();" in workspace
    assert "Explicit evidence scope" in architecture


def test_relic_observer_exposes_a_visible_bounded_chat_transcript():
    workspace = (APP / "Components" / "ReLiCObserverWorkspace.razor").read_text(encoding="utf-8")
    assert 'aria-label="ReLiC conversation"' in workspace
    assert 'MaxVisibleChatTurns=12' in workspace
    assert '_chatTurns.Add(new ObserverChatTurn(query,_answer))' in workspace
    assert 'while(_chatTurns.Count>MaxVisibleChatTurns)_chatTurns.RemoveAt(0)' in workspace
    assert 'CLEAR CHAT' in workspace
    assert '_chatTurns.Clear()' in workspace
