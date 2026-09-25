from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

client = (ROOT / "DiscordAuthClient.cs").read_text(encoding="utf-8")
library = (ROOT / "Components" / "AssetLibrary.razor").read_text(encoding="utf-8")
user_assets = (ROOT / "WorldSession.UserAssets.cs").read_text(encoding="utf-8")
backend = (ROOT.parents[1] / "infra" / "aws" / "rist-discord-storage.yml").read_text(encoding="utf-8")

assert "UploadContentAddressedBytesAsync" in client
assert '"/storage/finalize"' in client
assert "SHA256.HashData(bytes)" in client
assert "UploadContentAddressedBytesAsync(key,memory.ToArray(),contentType)" in library
assert "Sha256:finalized.Sha256" in library
assert "sha256: entry.Sha256" in user_assets
assert 'Path: /storage/finalize' in backend
assert '"content/sha256/{}/{}"' in backend
assert '"rist-content-sha256"' in backend
assert 'target_key = content_object_key(sha256) if sha256 else key' in backend

print("Private asset content-addressing contract verified.")
