# Plano de Desenvolvimento e Testes - Desafio Arckwell

## Objetivo

Desenvolver uma API REST para gerenciamento de pautas e sessões de votação em assembleias cooperativas.

A solução deve seguir boas práticas de engenharia de software, arquitetura limpa, testes automatizados, observabilidade e princípios de qualidade orientados por SDET (Software Development Engineer in Test).

---

# Papel do Agente

Você é um engenheiro de software sênior especializado em:

* Python
* FastAPI
* Arquitetura Limpa
* Testes Automatizados
* Qualidade de Software
* DevOps
* Performance
* Observabilidade

Todas as decisões técnicas devem priorizar:

1. Simplicidade
2. Manutenibilidade
3. Testabilidade
4. Escalabilidade
5. Legibilidade

Evite overengineering.

---

# Requisitos Funcionais

## RF01 - Criar Pauta

Permitir cadastro de uma nova pauta.

### Endpoint

```http
POST /api/v1/pautas
```

### Request

```json
{
  "titulo": "Nova pauta",
  "descricao": "Descrição da pauta"
}
```

### Response

```json
{
  "id": "uuid",
  "titulo": "Nova pauta",
  "descricao": "Descrição da pauta"
}
```

---

## RF02 - Abrir Sessão

Permitir abertura de sessão para uma pauta.

### Endpoint

```http
POST /api/v1/pautas/{id}/sessao
```

### Request

```json
{
  "duracao_segundos": 300
}
```

### Regras

* Se duração não for informada:

  * utilizar 60 segundos
* Uma pauta pode possuir apenas uma sessão ativa

---

## RF03 - Receber Votos

Permitir que associados votem.

### Endpoint

```http
POST /api/v1/votos
```

### Request

```json
{
  "sessao_id": "uuid",
  "associado_id": "uuid",
  "voto": "SIM"
}
```

### Regras

* Apenas SIM ou NÃO
* Associado vota apenas uma vez por pauta
* Sessão deve estar aberta
* Sessão não pode estar expirada

---

## RF04 - Resultado da Votação

### Endpoint

```http
GET /api/v1/pautas/{id}/resultado
```

### Response

```json
{
  "sim": 100,
  "nao": 25,
  "resultado": "APROVADA"
}
```

---

# Requisitos Não Funcionais

## Persistência

Os dados devem sobreviver ao restart da aplicação.

Utilizar:

```text
PostgreSQL
```

---

## Observabilidade

Implementar:

* Logging estruturado
* Correlação de requisições
* Logs de erro
* Logs de negócio

Exemplo:

```json
{
  "event":"vote_registered",
  "pauta_id":"123",
  "associado_id":"456"
}
```

---

## Documentação

Disponibilizar:

```text
Swagger
OpenAPI
README.md
```

---

# Arquitetura

Utilizar Clean Architecture simplificada.

## Estrutura

```text
app/

├── api/
│   └── v1/
│
├── application/
│   └── use_cases/
│
├── domain/
│   ├── entities/
│   ├── services/
│   └── exceptions/
│
├── infrastructure/
│   ├── database/
│   ├── repositories/
│   └── external/
│
├── tests/
│
└── main.py
```

---

# Stack Tecnológica

## Backend

* Python 3.12+
* FastAPI
* SQLAlchemy
* Alembic
* Pydantic

## Banco

* PostgreSQL

## Testes

* Pytest
* pytest-asyncio
* pytest-cov
* Faker

## Qualidade

* Ruff
* Black
* MyPy

## Containers

* Docker
* Docker Compose

## Performance

* Locust

## Mensageria

* RabbitMQ

---

# Modelagem

## Pauta

```text
id
titulo
descricao
created_at
```

---

## Sessao

```text
id
pauta_id
inicio
fim
status
```

Status:

```text
OPEN
CLOSED
```

---

## Associado

```text
id
cpf
```

---

## Voto

```text
id
sessao_id
associado_id
voto
created_at
```

Constraint obrigatória:

```sql
UNIQUE(sessao_id, associado_id)
```

---

# Casos de Uso

## CriarPautaUseCase

Responsável por:

* Validar entrada
* Persistir pauta

---

## AbrirSessaoUseCase

Responsável por:

* Validar existência da pauta
* Criar sessão
* Definir tempo padrão

---

## RegistrarVotoUseCase

Responsável por:

* Validar sessão
* Validar voto
* Garantir unicidade do voto
* Persistir voto

---

## ObterResultadoUseCase

Responsável por:

* Somar votos
* Determinar resultado

---

# Estratégia de Testes

Seguir Pirâmide de Testes.

```text
          E2E
        /     \
      API      API
     /            \
 Integration Tests
   /            \
 Unit Tests Unit Tests
```

---

# Testes Unitários

Cobrir:

## Criar pauta

```python
test_should_create_agenda()
```

## Abrir sessão

```python
test_should_open_session()
```

## Sessão expirada

```python
test_should_not_vote_after_session_closed()
```

## Voto duplicado

```python
test_should_not_allow_duplicate_vote()
```

## Resultado

```python
test_should_calculate_result()
```

Meta:

```text
Cobertura mínima de 90%
```

---

# Testes de Integração

Validar:

* Repositories
* SQLAlchemy
* PostgreSQL

Fluxo:

```text
UseCase
↓
Repository
↓
PostgreSQL
```

Executar utilizando banco real em Docker.

---

# Testes de API

Utilizar FastAPI TestClient.

Validar:

## POST /pautas

```text
201 Created
```

## POST /votos

```text
200 OK
```

## Voto duplicado

```text
409 Conflict
```

## Sessão encerrada

```text
400 Bad Request
```

---

# Testes Contratuais

Validar:

* Schemas Request
* Schemas Response

Utilizar Pydantic.

Garantir compatibilidade da API.

---

# Testes de Performance

Utilizar Locust.

Cenários:

## Cenário 1

```text
1000 usuários simultâneos
```

Fluxo:

```text
Criar pauta
Abrir sessão
Votar
Consultar resultado
```

---

## Cenário 2

```text
100000 votos
```

Objetivo:

* Avaliar throughput
* Avaliar latência
* Avaliar uso de banco

Métricas desejadas:

```text
P95 < 500ms
Taxa de erro < 1%
```

---

# Bônus 1 - Integração Externa

Criar adapter.

```python
class VoterValidationClient
```

Responsável por consumir:

```http
GET /users/{cpf}
```

Retornos:

```text
ABLE_TO_VOTE
UNABLE_TO_VOTE
```

Não misturar chamadas HTTP dentro dos casos de uso.

---

# Bônus 2 - Mensageria

Quando a sessão encerrar:

Publicar evento.

Exemplo:

```json
{
  "pauta_id":"123",
  "sim":100,
  "nao":20,
  "resultado":"APROVADA"
}
```

Fila:

```text
voting-results
```

---

# Bônus 3 - Performance

Garantir:

* Índices adequados
* Consultas eficientes
* Paginação futura
* Escalabilidade para centenas de milhares de votos

---

# Bônus 4 - Versionamento

Estratégia:

```text
/api/v1
/api/v2
```

Exemplo:

```http
/api/v1/pautas
/api/v2/pautas
```

---

# Pipeline CI/CD

Executar automaticamente:

```text
Lint
↓
Testes Unitários
↓
Testes Integração
↓
Coverage
↓
Build Docker
```

Ferramentas:

```text
GitHub Actions
Ruff
Pytest
Docker
```

---

# Critérios de Aceite

A entrega será considerada pronta quando:

* Todos os endpoints estiverem implementados
* Persistência estiver funcionando
* Cobertura acima de 90%
* Docker Compose funcional
* Swagger disponível
* README completo
* Logs implementados
* Pipeline CI funcionando
* Testes automatizados executando com sucesso

---

# Diretrizes para o Agente

Sempre:

* Criar código limpo
* Utilizar tipagem forte
* Seguir SOLID quando fizer sentido
* Priorizar simplicidade
* Criar testes junto com a funcionalidade
* Evitar duplicação de código
* Documentar decisões arquiteturais

Nunca:

* Colocar regra de negócio dentro dos controllers
* Acessar banco diretamente nos endpoints
* Misturar responsabilidades
* Ignorar tratamento de exceções
* Ignorar testes automatizados
* Utilizar valores hardcoded sem justificativa

```
```
