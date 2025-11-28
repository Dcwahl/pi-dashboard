Little monitoring dashboard for my Raspberry Pi 5

Rebuild;
`
git pull
docker compose down
docker compose build <backend/frontend>
docker compose up -d
`

or like
`
git pull && docker compose up -d --build
`

For like rolling out new stuff;
`
kubectl apply -f backend-deployment.yaml
kubectl rollout restart deployment/dashboard-backend
kubectl get pods
`

Okay now got deploy scripts too for this;

`
./deploy <frontend/backend/all>
`