from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_public_ai_policies_block_av_ingress_from_gameplay_authority():
    for relative in (
        "wwwroot/ai-policy.json",
        "wwwroot/.well-known/ai-policy.json",
        "wwwroot/.well-known/relic-ai-policy.json",
    ):
        policy = json.loads(text(relative))
        boot = policy["trustedBoot"]
        ingress = policy["audioVideoIngress"]

        assert boot["uefiMayEstablishDedicatedShaelvienBoot"] is True
        assert boot["gameplayMayWriteFirmware"] is False
        assert boot["aiMayWriteFirmware"] is False
        assert boot["semanticControlsMayAlterBootPolicy"] is False

        assert ingress["authoritativeForGameplay"] is False
        assert ingress["microphoneAuthoritative"] is False
        assert ingress["cameraAuthoritative"] is False
        assert ingress["speechRecognitionAuthoritative"] is False
        assert ingress["visualRecognitionAuthoritative"] is False
        assert ingress["mayTriggerGameplayActions"] is False
        assert ingress["mayMutateAuthoritativeGameState"] is False
        assert ingress["blockIfReflectedIntoGameAction"] is True
        assert ingress["approvedAuthoritativeHumanInputs"] == [
            "controller", "keyboard", "touch", "accessibility-control"
        ]


def test_ai_canon_contract_contains_trusted_boot_and_av_ingress_rules():
    access = text("ExternalAiAccess.cs")
    assert "trusted-uefi-boot-only" in access
    assert "av-ingress-non-authoritative" in access
    assert "no-robotic-embodiment" in access
    assert "simulation-is-not-reality" in access


def test_current_voice_runtime_is_output_only():
    voice = text("wwwroot/roleplay-voice.js")
    assert "speechSynthesis" in voice
    assert "SpeechSynthesisUtterance" in voice
    assert "getUserMedia" not in voice
    assert "SpeechRecognition" not in voice
    assert "webkitSpeechRecognition" not in voice


def test_media_capture_code_cannot_share_semantic_dispatch_path():
    media_markers = (
        "getUserMedia",
        "SpeechRecognition",
        "webkitSpeechRecognition",
        "MediaRecorder",
        "enumerateDevices",
    )
    semantic_markers = (
        "ReceiveUniversalInput",
        "ReceiveSemanticAction",
        "dispatchSemantic(",
    )

    violations = []
    for path in (ROOT / "wwwroot").rglob("*.js"):
        code = path.read_text(encoding="utf-8", errors="ignore")
        if any(marker in code for marker in media_markers) and any(
            marker in code for marker in semantic_markers
        ):
            violations.append(str(path.relative_to(ROOT)))

    assert violations == [], (
        "Audio/video capture must remain isolated from semantic gameplay dispatch: "
        + ", ".join(violations)
    )


def test_trusted_boot_io_contract_is_explicit_about_current_runtime_status():
    contract = text("SHAELVIEN_TRUSTED_BOOT_IO_CONTRACT.md")
    assert "UEFI" in contract
    assert "current repository still ships a Windows-hosted ShaelvienOS installer/runtime" in contract
    assert "OBSERVED_MEDIA != GAMEPLAY_AUTHORITY" in contract
    assert "no microphone or camera device capability at all" in contract
