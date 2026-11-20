# k8s/base

Deployments, Services, ConfigMap, PersistentVolumeClaim, the Postgres StatefulSet and the refresh-index CronJob. Built in #49, #50, #51, #54 and #66. Secrets are created from `.env`, never stored here.

Apply: `kubectl apply -k k8s/base`. Commands run from `searchashouses/`.
