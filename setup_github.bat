@echo off
echo.
echo === Unicred Voting API - Setup GitHub ===
echo.

cd /d "C:\Users\welli\OneDrive\Desktop\Projetos\DesafioUnicred"

echo [1/5] Inicializando repositorio git...
git init
git branch -M main

echo.
echo [2/5] Adicionando arquivos...
git add .

echo.
echo [3/5] Criando commit inicial...
git commit -m "feat: initial commit - Unicred Voting API

- Clean Architecture (FastAPI + MongoDB + RabbitMQ)
- CRUD completo para pautas, sessoes, votos e associados
- Validacao de CPF matematica (modulo 11) + API externa opcional
- Bonus 1-4 implementados (CPF, RabbitMQ, indices, versionamento)
- 84 testes passando (unitarios + API)
- Docker Compose + CI/CD GitHub Actions"

echo.
echo [4/5] Criando repositorio no GitHub...
gh repo create voting-api --public --description "API REST de votacao cooperativa - FastAPI + MongoDB + Clean Architecture" --source . --remote origin --push

echo.
echo [5/5] Concluido!
echo.
echo Acesse: https://github.com/wellingtoncamargo/voting-api
echo.
pause
