# GitHub Actions Deployment Design

Status: design only, Azure binding pending.

No active Azure deployment workflow is enabled in this branch because the Azure target has not been verified through portal access. The historical `hex-sphere` workflows referenced publish profiles, PAT refresh automation, Discord webhooks, and names that may now be stale.

Required future workflow after Azure target verification:

1. Check out `ryanlcole/DicePage`.
2. Set up Python and Node.js.
3. Run Shaelvien Lite tests.
4. Run Shaelvien Tactical Node replay and geometry tests.
5. Build `dist` with `python deployment/build_public.py`.
6. Scan `dist` with `python deployment/public_build_scan.py`.
7. Authenticate to Azure using OIDC where practical.
8. Deploy `dist` only when all gates pass.
9. Verify `/`, `/app/`, `/store/`, `/docs/`, `/lab/`, and `/build-info.json`.
10. Record the deployed commit, build ID, timestamp, and target hostname.

Authentication requirements:

- Prefer Azure OIDC with a least-privilege federated credential.
- If a publish profile is unavoidable, generate a fresh profile and store it only as a GitHub Actions secret.
- Never commit publish profiles, service principal secrets, PATs, webhook URLs, or connection strings.

