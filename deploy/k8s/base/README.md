# deploy/k8s/base

Scorpio **MVP**: scheduler, executor, python-runtime (`:local` images), API stub (`hashicorp/http-echo`), web stub (nginx + ConfigMap). Same service names/ports as `deploy/docker-compose/docker-compose.scorpio-stack.yml`.

Apply: `kubectl apply -k deploy/k8s/base` (load `scorpio-scheduler:local` etc. into the cluster first, or patch images to your registry).
