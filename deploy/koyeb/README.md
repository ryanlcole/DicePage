# Koyeb Staging Notes

Use this only for the private Shaelvien Lite staging service.

Required choices:

- Instance type: Free.
- Region: Washington, D.C. when available.
- Source repository: `https://github.com/ryanlcole/DicePage.git`.
- Branch: `deployment/koyeb-neon-staging`.
- Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 45 shaelvien_lite.wsgi:app`.
- Health check path: `/ready`.
- Scaling: one Free Instance only.
- Persistent volume: none.

Do not choose Eco, Standard, GPU, paid volume, paid database, or autoscaling beyond the free instance.

Apply environment variables from `staging.env.example` using Koyeb secrets for all secret values.
