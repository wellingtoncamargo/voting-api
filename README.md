# Unicred Voting API

API REST para gerenciamento de pautas e sessões de votação em assembleias cooperativas. Desenvolvida como desafio técnico com FastAPI, MongoDB e Clean Architecture.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Stack Tecnológica](#stack-tecnológica)
- [Arquitetura](#arquitetura)
- [Como Rodar](#como-rodar)
- [Endpoints](#endpoints)
- [Validação de CPF](#validação-de-cpf)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Testes](#testes)
- [Decisões Técnicas](#decisões-técnicas)

---

## Visão Geral

No cooperativismo, cada associado possui um voto e as decisões são tomadas em assembleias por votação. Esta API gerencia todo esse fluxo:

1. Cadastro de associados (com CPF único e validação matemática)
2. Criação de pautas
3. Abertura de sessões de votação com tempo configurável
4. Registro de votos (SIM ou NÃO, um por associado por sessão)
5. Apuração automática do resultado

---

## Stack Tecnológica

| Camada      | Tecnologia                            |
|-------------|---------------------------------------|
| Runtime     | Python 3.12                           |
| Framework   | FastAPI 0.115                         |
| ODM         | Beanie 1.27 (Motor + MongoDB)         |
| Banco       | MongoDB 7.0                           |
| Mensageria  | RabbitMQ 3.13 + aio-pika              |
| HTTP Client | httpx                                 |
| Logging     | python-json-logger (JSON estruturado) |
| Containers  | Docker + Docker Compose               |
| Testes      | pytest + pytest-asyncio               |
| CI          | GitHub Actions                        |

---

## Arquitetura

Clean Architecture simplificada em 4 camadas com regra de dependência estrita:

```
api → application → domain ← infrastructure
```

```
app/
├── api/v1/
│   ├── routes/
│   │   ├── pautas.py       ← Endpoints de pautas e sessões
│   │   ├── votos.py        ← Endpoints de votos
│   │   └── associados.py   ← Endpoints de associados
│   └── schemas.py          ← Schemas Pydantic de request/response
│
├── application/use_cases/  ← Regras de negócio (um arquivo por caso de uso)
│   ├── criar_pauta.py
│   ├── listar_pautas.py
│   ├── atualizar_pauta.py
│   ├── deletar_pauta.py
│   ├── abrir_sessao.py
│   ├── listar_sessoes.py
│   ├── encerrar_sessao.py
│   ├── obter_resultado.py
│   ├── registrar_voto.py
│   ├── listar_votos.py
│   ├── cadastrar_associado.py
│   ├── listar_associados.py
│   └── deletar_associado.py
│
├── domain/
│   ├── entities/models.py      ← Documentos Beanie: Pauta, Sessao, Associado, Voto
│   └── exceptions/exceptions.py ← Exceções de domínio tipadas
│
├── infrastructure/
│   ├── database/mongodb.py          ← Conexão e init Beanie
│   ├── repositories/               ← Acesso ao banco (1 por entidade)
│   ├── external/voter_validation_client.py ← Adapter validação CPF
│   └── messaging/publisher.py      ← Publisher RabbitMQ
│
└── core/
    ├── config.py            ← Configurações via .env (pydantic-settings)
    ├── logging_config.py    ← Logging estruturado JSON
    ├── scheduler.py         ← Background task de sessões expiradas
    └── exception_handlers.py ← Mapeamento exceção → HTTP status
```

---

## Como Rodar

### Pré-requisitos

- Docker e Docker Compose instalados

### Com Docker (recomendado)

```bash
# 1. Clonar e entrar na pasta
git clone <repo>
cd DesafioUnicred

# 2. Configurar variáveis de ambiente
cp .env.example .env

# 3. Subir todos os serviços (API + MongoDB + RabbitMQ)
docker compose up --build
```

| Serviço             | URL                          |
|---------------------|------------------------------|
| API (Swagger)       | http://localhost:8000/docs   |
| API (ReDoc)         | http://localhost:8000/redoc  |
| RabbitMQ Management | http://localhost:15672        |
| MongoDB             | localhost:27017              |

### Localmente (sem Docker)

Requer MongoDB e RabbitMQ rodando localmente.

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env apontando para localhost
cp .env.example .env
# Editar MONGODB_URL=mongodb://localhost:27017
# Editar RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Rodar
uvicorn app.main:app --reload
```

---

## Endpoints

### Fluxo principal

```
1. Cadastrar associado    → POST /api/v1/associados
2. Criar pauta            → POST /api/v1/pautas
3. Abrir sessão           → POST /api/v1/pautas/{id}/sessao
4. Votar                  → POST /api/v1/votos
5. Consultar resultado    → GET  /api/v1/pautas/{id}/resultado
```

---

### Associados

#### Cadastrar associado
```bash
curl -X POST http://localhost:8000/api/v1/associados \
  -H "Content-Type: application/json" \
  -d '{"cpf": "52998224725"}'
```
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "cpf": "52998224725",
  "created_at": "2026-06-01T10:00:00"
}
```

#### Listar associados (paginado)
```bash
curl "http://localhost:8000/api/v1/associados?page=1&limit=20"
```

#### Buscar por ID
```bash
curl http://localhost:8000/api/v1/associados/{id}
```

#### Remover
```bash
curl -X DELETE http://localhost:8000/api/v1/associados/{id}
```

#### Validar CPF (diagnóstico)
```bash
curl http://localhost:8000/api/v1/associados/validar-cpf/52998224725
```
```json
{"cpf": "52998224725", "valido": true, "mensagem": "CPF válido."}
```

---

### Pautas

#### Criar pauta
```bash
curl -X POST http://localhost:8000/api/v1/pautas \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Aprovação de orçamento anual", "descricao": "Votação sobre o orçamento 2026"}'
```
```json
{
  "id": "pauta-uuid",
  "titulo": "Aprovação de orçamento anual",
  "descricao": "Votação sobre o orçamento 2026",
  "created_at": "2026-06-01T10:00:00"
}
```

#### Listar pautas
```bash
curl "http://localhost:8000/api/v1/pautas?page=1&limit=20"
```

#### Buscar pauta
```bash
curl http://localhost:8000/api/v1/pautas/{pauta_id}
```

#### Atualizar pauta
```bash
curl -X PATCH http://localhost:8000/api/v1/pautas/{pauta_id} \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Novo título"}'
```

#### Remover pauta
```bash
# Só funciona se não houver sessão ativa
curl -X DELETE http://localhost:8000/api/v1/pautas/{pauta_id}
```

---

### Sessões

#### Abrir sessão de votação
```bash
# Com duração personalizada (em segundos)
curl -X POST http://localhost:8000/api/v1/pautas/{pauta_id}/sessao \
  -H "Content-Type: application/json" \
  -d '{"duracao_segundos": 300}'

# Sem duração → usa 60 segundos por padrão
curl -X POST http://localhost:8000/api/v1/pautas/{pauta_id}/sessao \
  -H "Content-Type: application/json" \
  -d '{}'
```
```json
{
  "id": "sessao-uuid",
  "pauta_id": "pauta-uuid",
  "inicio": "2026-06-01T10:00:00",
  "fim": "2026-06-01T10:05:00",
  "status": "OPEN"
}
```

#### Listar sessões da pauta
```bash
curl "http://localhost:8000/api/v1/pautas/{pauta_id}/sessoes"
```

#### Encerrar sessão manualmente
```bash
curl -X PATCH http://localhost:8000/api/v1/pautas/{pauta_id}/sessao/{sessao_id}/encerrar
```

#### Resultado da votação
```bash
curl http://localhost:8000/api/v1/pautas/{pauta_id}/resultado
```
```json
{"sim": 42, "nao": 10, "resultado": "APROVADA"}
```

---

### Votos

#### Registrar voto
```bash
curl -X POST http://localhost:8000/api/v1/votos \
  -H "Content-Type: application/json" \
  -d '{
    "sessao_id": "sessao-uuid",
    "associado_id": "assoc-uuid",
    "voto": "SIM"
  }'
```

#### Listar votos de uma sessão
```bash
curl "http://localhost:8000/api/v1/votos/sessao/{sessao_id}?page=1&limit=50"
```

---

### Respostas de erro

| HTTP | Situação |
|------|----------|
| 400  | Sessão encerrada ou sem campos para atualização |
| 403  | Associado impedido de votar (UNABLE_TO_VOTE) |
| 404  | Recurso não encontrado |
| 409  | Conflito: voto duplicado, sessão já ativa, CPF já cadastrado |
| 422  | Dados inválidos (CPF com dígitos errados, voto inválido) |

---

## Validação de CPF

A validação ocorre em duas camadas independentes:

### Camada 1 — Matemática local (sempre ativa)

Implementa o algoritmo dos dígitos verificadores (módulo 11), que é a forma oficial de validar CPFs brasileiros. Rejeita imediatamente qualquer CPF com dígitos verificadores incorretos ou sequências uniformes (000.000.000-00, 111.111.111-11 etc.), sem nenhuma chamada de rede.

### Camada 2 — API externa Heroku (opcional)

Configurada via `VOTER_VALIDATION_ENABLED=true`. Em caso de falha de rede ou indisponibilidade da API, opera em **fail-open** — o cadastro não é bloqueado.

> **Por que a camada local foi adicionada?**
> A API do Heroku (`user-info.herokuapp.com`) estava retornando 422 para CPFs válidos em testes. A validação matemática local resolve esse problema de forma determinística, sem dependência de terceiros. A API externa passa a ser um enriquecimento opcional.

### CPFs válidos para testes

```
52998224725
11144477735
529.982.247-25   ← formato com máscara também é aceito
```

---

## Variáveis de Ambiente

| Variável                         | Padrão                              | Descrição                             |
|----------------------------------|-------------------------------------|---------------------------------------|
| `MONGODB_URL`                    | `mongodb://mongo:27017`             | URL de conexão MongoDB                |
| `MONGODB_DB_NAME`                | `unicred_voting`                    | Nome do banco                         |
| `RABBITMQ_URL`                   | `amqp://guest:guest@rabbitmq:5672/` | URL de conexão RabbitMQ               |
| `VOTER_VALIDATION_URL`           | `https://user-info.herokuapp.com`   | URL da API externa de CPF             |
| `VOTER_VALIDATION_ENABLED`       | `false`                             | `true` para consultar API externa     |
| `SESSION_CLOSE_INTERVAL_SECONDS` | `30`                                | Intervalo do scheduler em segundos    |
| `DEBUG`                          | `false`                             | Modo debug                            |

---

## Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Apenas testes unitários
pytest tests/unit/ -v

# Apenas testes de API
pytest tests/api/ -v
```

**Resultado:** 84 testes · 84 passando · 0 falhas

| Tipo       | Arquivo                           | Quantidade |
|------------|-----------------------------------|------------|
| Unitário   | `tests/unit/test_use_cases.py`    | 43         |
| API (HTTP) | `tests/api/test_endpoints.py`     | 41         |

Os testes unitários usam `AsyncMock` em todos os repositórios — sem banco, sem rede. Os testes de API usam um `test_app` com lifespan noop — sem MongoDB, sem RabbitMQ.

---

## Decisões Técnicas

### MongoDB em vez de PostgreSQL
O modelo de dados de votação é naturalmente orientado a documentos. MongoDB com Beanie ODM oferece tipagem forte via Pydantic, índices compostos para garantir unicidade de votos, e agregações nativas eficientes para contagem — sem necessidade de migrations.

### Beanie ODM
Camada thin sobre Motor (driver async oficial do MongoDB), com suporte nativo a Pydantic v2, índices declarativos e `model_construct()` para criação de entidades sem conexão ativa (fundamental para os testes unitários).

### Validação de CPF em duas camadas
A API externa do Heroku é uma dependência instável (frequentemente fora do ar). Implementar a validação matemática local como camada primária garante que o sistema funcione independentemente de terceiros. A API externa fica como enriquecimento opcional com fail-open.

### Scheduler asyncio nativo
Em vez de Celery ou APScheduler (overhead adicional), um simples `asyncio.create_task` no lifespan do FastAPI executa a checagem de sessões expiradas. Suficiente para o escopo do desafio, sem dependências externas adicionais.

### Clean Architecture simplificada
Mantém a separação de responsabilidades sem over-engineering. Controllers não contêm lógica, Use Cases não conhecem HTTP, Repositórios não conhecem regras de negócio.

### Paginação genérica
`PaginatedResponse[T]` como schema genérico Pydantic garante consistência em todos os endpoints de listagem sem duplicação de código.

### Versionamento por URL
`/api/v1/...` é a estratégia mais simples e explícita. Novas versões podem conviver no mesmo processo registrando um novo router `/api/v2`.
