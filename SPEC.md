# SPEC — Arckwell Voting API
## Estado atual da aplicação · Junho 2026

---

## 1. Visão Geral

API REST para gerenciamento de pautas e sessões de votação em assembleias cooperativas.
Cada associado possui um voto por pauta. Decisões são tomadas por maioria simples.

---

## 2. Stack

| Camada      | Tecnologia                           |
|-------------|--------------------------------------|
| Runtime     | Python 3.12                          |
| Framework   | FastAPI 0.115                        |
| ODM         | Beanie 1.27 (sobre Motor + MongoDB)  |
| Banco       | MongoDB 7.0                          |
| Mensageria  | RabbitMQ 3.13 (aio-pika)             |
| HTTP Client | httpx                                |
| Logging     | python-json-logger (JSON estruturado)|
| Containers  | Docker + Docker Compose              |
| Testes      | pytest + pytest-asyncio + anyio      |
| CI          | GitHub Actions                       |

---

## 3. Arquitetura

Clean Architecture simplificada em 4 camadas:

```
app/
├── api/v1/routes/          ← Controllers (FastAPI routers)
├── application/use_cases/  ← Regras de negócio
├── domain/
│   ├── entities/           ← Documentos Beanie (modelos MongoDB)
│   └── exceptions/         ← Exceções de domínio tipadas
└── infrastructure/
    ├── database/           ← Conexão MongoDB via Beanie
    ├── repositories/       ← Acesso ao banco (1 por entidade)
    ├── external/           ← Adapter validação CPF
    └── messaging/          ← Publisher RabbitMQ
```

**Regra de dependência:** `api → application → domain ← infrastructure`

---

## 4. Entidades (MongoDB Collections)

### Pauta
```
id          : str (UUID v4)
titulo      : str
descricao   : str | None
created_at  : datetime
```

### Sessao
```
id          : str (UUID v4)
pauta_id    : str (ref → Pauta.id)
inicio      : datetime
fim         : datetime
status      : "OPEN" | "CLOSED"
```
Índices: `(pauta_id, status)`, `(fim)`

### Associado
```
id          : str (UUID v4)
cpf         : str (11 dígitos, único)
created_at  : datetime
```
Índices: `(cpf)` unique

### Voto
```
id            : str (UUID v4)
sessao_id     : str (ref → Sessao.id)
associado_id  : str (ref → Associado.id)
voto          : "SIM" | "NAO"
created_at    : datetime
```
Índices: `(sessao_id, associado_id)` unique, `(sessao_id)`

---

## 5. Endpoints CRUD Completos

### Base URL: `/api/v1`

---

### Associados

| Método | Rota                                    | Descrição                              | Status |
|--------|-----------------------------------------|----------------------------------------|--------|
| GET    | `/associados`                           | Listar (paginado)                      | 200    |
| POST   | `/associados`                           | Cadastrar (valida CPF matematicamente) | 201    |
| GET    | `/associados/{id}`                      | Buscar por ID                          | 200    |
| DELETE | `/associados/{id}`                      | Remover                                | 204    |
| GET    | `/associados/validar-cpf/{cpf}`         | Verificar CPF (utilitário, sem persistir) | 200 |

---

### Pautas

| Método | Rota                                          | Descrição                              | Status |
|--------|-----------------------------------------------|----------------------------------------|--------|
| GET    | `/pautas`                                     | Listar (paginado)                      | 200    |
| POST   | `/pautas`                                     | Criar                                  | 201    |
| GET    | `/pautas/{id}`                                | Buscar por ID                          | 200    |
| PATCH  | `/pautas/{id}`                                | Atualizar título e/ou descrição        | 200    |
| DELETE | `/pautas/{id}`                                | Remover (apenas sem sessão ativa)      | 204    |

---

### Sessões

| Método | Rota                                              | Descrição                     | Status |
|--------|---------------------------------------------------|-------------------------------|--------|
| GET    | `/pautas/{id}/sessoes`                            | Listar sessões da pauta       | 200    |
| POST   | `/pautas/{id}/sessao`                             | Abrir sessão                  | 201    |
| PATCH  | `/pautas/{id}/sessao/{sessao_id}/encerrar`        | Encerrar sessão manualmente   | 200    |
| GET    | `/pautas/{id}/resultado`                          | Resultado da votação          | 200    |

---

### Votos

| Método | Rota                        | Descrição               | Status |
|--------|-----------------------------|-------------------------|--------|
| GET    | `/votos/sessao/{sessao_id}` | Listar votos da sessão  | 200    |
| POST   | `/votos`                    | Registrar voto          | 201    |

---

### Health

| Método | Rota      | Descrição              |
|--------|-----------|------------------------|
| GET    | `/health` | Verificação de saúde   |

---

## 6. Paginação

Todos os endpoints de listagem aceitam `page` e `limit` como query params.

**Response padrão:**
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

---

## 7. Validação de CPF

### Estratégia em duas camadas

**Camada 1 — Validação matemática local (sempre ativa)**
- Algoritmo dos dígitos verificadores (módulo 11)
- Rejeita sequências uniformes (ex: 111.111.111-11)
- Aceita CPF com ou sem máscara
- Sem chamada de rede — instantânea

**Camada 2 — API externa Heroku (opcional)**
- Habilitada via `VOTER_VALIDATION_ENABLED=true`
- Opera em fail-open: falha de rede não bloqueia o cadastro
- `UNABLE_TO_VOTE` → HTTP 403
- CPF não encontrado → HTTP 422

**CPFs válidos para teste:** `52998224725`, `11144477735`

**Endpoint de diagnóstico:**
```
GET /api/v1/associados/validar-cpf/{cpf}
```

---

## 8. Regras de Negócio

| Regra | Descrição |
|-------|-----------|
| RN01 | Uma pauta pode ter apenas uma sessão ativa por vez |
| RN02 | Sessão sem duração informada usa 60 segundos |
| RN03 | Associado vota apenas uma vez por sessão |
| RN04 | Votos só são aceitos enquanto a sessão está OPEN e não expirou |
| RN05 | Expiração verificada em tempo real no momento do voto |
| RN06 | Resultado: SIM > NAO = APROVADA; NAO > SIM = REJEITADA; empate = EMPATE |
| RN07 | Pauta com sessão ativa não pode ser removida |
| RN08 | Sessão pode ser encerrada manualmente antes do prazo |

---

## 9. Bônus Implementados

### Bônus 1 — Integração Externa + Validação Local
- Validação matemática sempre ativa (algoritmo módulo 11)
- API Heroku opcional via `VOTER_VALIDATION_ENABLED=true`
- Endpoint `/validar-cpf/{cpf}` para diagnóstico

### Bônus 2 — Mensageria
- Scheduler publica resultado na fila `voting-results` ao fechar sessões
- Encerramento manual também publica na fila
- Payload: `{pauta_id, sessao_id, sim, nao, resultado}`

### Bônus 3 — Performance
- Índices MongoDB em todos os campos críticos
- Índice único `(sessao_id, associado_id)` evita duplicata no banco
- Agregação MongoDB nativa para contagem (sem carregar documentos)
- Paginação em todos os endpoints de listagem

### Bônus 4 — Versionamento
- Estratégia por prefixo: `/api/v1/...`
- Novas versões → `/api/v2/...` convivem no mesmo processo

---

## 10. Scheduler

Loop asyncio iniciado no `lifespan`. A cada `SESSION_CLOSE_INTERVAL_SECONDS` (padrão 30s):
1. Busca sessões `OPEN` com `fim <= agora`
2. Marca como `CLOSED`
3. Publica resultado no RabbitMQ

---

## 11. Observabilidade

Logs estruturados JSON. Eventos principais:

| event                        | Quando ocorre                  |
|------------------------------|--------------------------------|
| `pauta_created`              | Pauta criada                   |
| `pauta_updated`              | Pauta atualizada               |
| `pauta_deleted`              | Pauta removida                 |
| `session_opened`             | Sessão aberta                  |
| `session_closed_by_scheduler`| Sessão fechada pelo scheduler  |
| `session_closed_manual`      | Sessão encerrada manualmente   |
| `vote_registered`            | Voto registrado                |
| `result_calculated`          | Resultado calculado            |
| `associate_registered`       | Associado cadastrado           |
| `associado_deleted`          | Associado removido             |
| `cpf_math_valid`             | CPF válido matematicamente     |
| `cpf_math_invalid`           | CPF inválido matematicamente   |
| `cpf_external_ok`            | CPF validado pela API externa  |
| `voting_result_published`    | Resultado publicado no RabbitMQ|

---

## 12. Testes

| Tipo       | Arquivo                           | Qtd  |
|------------|-----------------------------------|------|
| Unitário   | `tests/unit/test_use_cases.py`    | 43   |
| API (HTTP) | `tests/api/test_endpoints.py`     | 41   |
| **Total**  |                                   | **84** |

**84/84 passando · 0 falhas**

---

## 13. Como Rodar

### Docker (recomendado)
```bash
cp .env.example .env
docker compose up --build
```

| URL | Descrição |
|-----|-----------|
| http://localhost:8000/docs  | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:15672      | RabbitMQ Management |

### Local (sem Docker)
```bash
pip install -r requirements.txt
cp .env.example .env  # ajustar URLs para localhost
uvicorn app.main:app --reload
```

### Testes
```bash
pytest tests/ -v
```

---

## 14. Variáveis de Ambiente

| Variável                         | Padrão                              | Descrição                           |
|----------------------------------|-------------------------------------|-------------------------------------|
| `MONGODB_URL`                    | `mongodb://mongo:27017`             | URL de conexão MongoDB              |
| `MONGODB_DB_NAME`                | `Arckwell_voting`                    | Nome do banco                       |
| `RABBITMQ_URL`                   | `amqp://guest:guest@rabbitmq:5672/` | URL de conexão RabbitMQ             |
| `VOTER_VALIDATION_URL`           | `https://user-info.herokuapp.com`   | URL da API externa de CPF           |
| `VOTER_VALIDATION_ENABLED`       | `false`                             | Habilitar consulta à API externa    |
| `SESSION_CLOSE_INTERVAL_SECONDS` | `30`                                | Intervalo do scheduler              |

---

## 15. Pendências / Próximos Passos

- [ ] Testes de integração com MongoDB (mongomock-motor ou testcontainers)
- [ ] Testes de performance com Locust
- [ ] Rate limiting por associado/IP
- [ ] Autenticação (JWT ou API Key)
- [ ] README.md completo com exemplos curl
