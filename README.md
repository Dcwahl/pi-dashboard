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