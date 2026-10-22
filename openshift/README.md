# Sliples on OpenShift

Manifests for running Sliples (live namespace: `slipless`), plus the CI/CD wiring used by
`.github/workflows/release.yml`. Local development uses Docker Compose instead (see `docs/DEPLOYMENT.md`).

## Layout

```
openshift/
├── kustomization.yaml        # Everything below, wired together (images point at a placeholder registry)
├── namespace.yaml
├── secrets/                  # secrets-template.yaml (template only; create real secrets by hand)
├── configmaps/               # backend-config, worker-config
├── postgres/ redis/ minio/   # data services
├── browsers/                 # Playwright Chrome + Firefox
├── backend/                  # BuildConfig, ImageStream, Deployment, Service, Route
├── frontend/                 # BuildConfig, ImageStream, nginx ConfigMap, Deployment, Service, Route
├── worker/                   # Celery worker + beat Deployments, HPA
├── patches/                  # production replica/resource overrides (commented out in kustomization)
├── network-policy.yaml       # optional, commented out in kustomization
├── ci/                       # pipeline support: service account, test Job, migration Job
└── tests/                    # schedule-test-job.yaml (`make test-schedules-openshift`)
```

`postgresql-deployment.yaml` and `redis-deployment.yaml` in this directory are not part of the
kustomization, which uses `postgres/` and `redis/`.

## Manual deploy

```bash
oc login --token=<token> --server=<server>
oc apply -f namespace.yaml
# create secrets first (see secrets/secrets-template.yaml), then:
oc apply -k openshift/
oc get routes -n slipless
```

Images are built in-cluster by the BuildConfigs and pulled from the ImageStreams, which have
`lookupPolicy.local: true`, so Deployments reference plain `sliples-backend:latest`.

## CI/CD pipeline

`.github/workflows/release.yml` runs on every push to `main` (i.e. every merged PR) and can be
started by hand (`workflow_dispatch`). Runs are serialized (`concurrency: release`).

| Stage | What it does |
|-------|--------------|
| **build** | `oc start-build sliples-backend` / `sliples-frontend` with `--commit=$GITHUB_SHA`. BuildConfigs output to the `:candidate` tag, which is then tagged `:<sha>`. |
| **test** | Creates a Job (`ci/test-job.yaml`) from the `:<sha>` backend image with **Postgres and Redis as native sidecars** (`initContainers` with `restartPolicy: Always`, Kubernetes ≥ 1.29 / OpenShift ≥ 4.16). The test container runs `pytest tests` against `localhost` services, so the live database is never touched. |
| **deploy** | (GitHub environment `production`) Runs `alembic upgrade head` in a Job (`ci/migrate-job.yaml`), retags `:<sha>` as `:latest`, then restarts and waits on the backend, worker, beat and frontend Deployments. |

A failing stage stops the later ones. Because only passing builds are promoted to `:latest`, a
failed run never changes what a pod restart pulls. To roll back, retag an earlier SHA:

```bash
oc tag sliples-backend:<old-sha> sliples-backend:latest
oc rollout restart deployment/sliples-backend deployment/sliples-worker deployment/sliples-beat
```

### One-time setup

1. Create the CI service account, role and token secret (project admin):
   ```bash
   NAMESPACE=slipless envsubst < openshift/ci/serviceaccount.yaml | oc apply -n slipless -f -
   oc get secret github-actions-token -n slipless -o jsonpath='{.data.token}' | base64 -d
   ```
2. Add GitHub repository secrets:
   - `OPENSHIFT_SERVER`: cluster API URL (must be reachable from GitHub-hosted runners, otherwise use a self-hosted runner)
   - `OPENSHIFT_TOKEN`: the token from step 1
   - (optional repository variable `OPENSHIFT_NAMESPACE`, default `slipless`; set in repo settings, not by CLI)
   - `IMPERSON_WEBHOOK_URL`: see below (optional; notifications are skipped when unset)
3. Point the live BuildConfigs at `:candidate`: `oc patch bc/sliples-backend -n slipless -p '{"spec":{"output":{"to":{"name":"sliples-backend:candidate"}}}}'` (same for frontend). Plain `oc start-build` no longer updates `:latest`; only a pipeline deploy does.
4. Create the `production` environment in GitHub (add required reviewers if deploys should be gated).

### Imperson notifications

`.github/scripts/notify-imperson.sh <stage> <phase> [status]` posts at the start and end of each
stage (`build`, `test`, `deploy`). It never fails the pipeline.

Imperson has no generic CI endpoint today. The script posts Jenkins Notification-plugin JSON to
imperson's Jenkins webhook, `https://imperson.agantis.in/api/v1/webhooks/team/jenkins?token=<token>`,
using one job per stage: `job/sliples/job/build/`, `.../test/`, `.../deploy/`. Set the full URL,
including the token, as `IMPERSON_WEBHOOK_URL`. Imperson only routes a build to a team when the job is
listed in a project's `devops.jenkins_jobs` (admin-managed), so these three names must be registered
there or the events are ignored.

## Operations

```bash
oc get pods -n slipless
oc logs -f deployment/sliples-backend -n slipless
oc logs -f deployment/sliples-worker -n slipless
oc scale deployment/sliples-worker --replicas=5 -n slipless
oc rollout history deployment/sliples-backend -n slipless
oc rollout undo deployment/sliples-backend -n slipless
```

Health checks: the backend exposes `GET /health`. For WebSocket streaming, the backend route needs
`haproxy.router.openshift.io/timeout: 1h`.

## References

- Full guide: [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)
- Streaming: [../docs/STREAMING_README.md](../docs/STREAMING_README.md)
