# Architecture Decision Records — Arckwell Voting API

> Registro das principais decisões técnicas e seus fundamentos.

---

## ADR-001 — MongoDB em vez de PostgreSQL

**Data:** Junho 2026
**Status:** Aceito

### Contexto
O plano original (GPT-Plan.md) especificava PostgreSQL + SQLAlchemy + Alembic.

### Decisão
Adotar MongoDB 7.0 com Beanie ODM.

### Justificativa
- Modelo de dados de votação é naturalmente orientado a documentos (votos agregados por sessão)
- Sem necessidade de migrations (schemaless elimina Alembic)
- Agregações nativas (`$group`, `$sum`) para contagem de votos sem carregar documentos em memória
- Índice único composto `(sessao_id, associado_id)` garante unicidade de voto no banco, não só na aplicação
- Beanie oferece tipagem forte via Pydantic v2 com suporte async nativo

### Consequências
- Sem transações ACID multi-documento (aceitável no escopo)
- Sem suporte a queries JOIN (não necessário no modelo de domínio)

---

## ADR-002 — Beanie ODM com model_construct()

**Data:** Junho 2026
**Status:** Aceito

### Contexto
Beanie exige `init_beanie()` antes de instanciar qualquer `Document` via `__init__()`.
Isso tornava os Use Cases impossíveis de testar unitariamente sem uma conexão MongoDB ativa.

### Decisão
Usar `Model.model_construct()` nos Use Cases para criar entidades sem chamar `__init__()`.
Repositórios recebem o objeto construído e chamam `.insert()`.

### Justificativa
`model_construct()` é o método oficial do Pydantic v2 para criar instâncias sem
validação e sem disparar hooks de inicialização. Permite criar documentos Beanie
em contextos sem banco ativo (testes unitários, fixtures, factories).

### Padrão aplicado
```python
# Use Case (sem DB)
pauta = Pauta.model_construct(titulo=titulo, descricao=descricao)
pauta = await self._repo.criar(pauta)

# Repositório (com DB)
async def criar(self, pauta: Pauta) -> Pauta:
    await pauta.insert()
    return pauta
```

---

## ADR-003 — Validação de CPF em duas camadas

**Data:** Junho 2026
**Status:** Aceito

### Contexto
A API externa `user-info.herokuapp.com` retornava HTTP 422 para CPFs válidos,
bloqueando o cadastro de associados.

### Decisão
Implementar validação em duas camadas independentes:
1. **Matemática local** (sempre ativa): algoritmo módulo 11
2. **API externa** (opcional): controlada por `VOTER_VALIDATION_ENABLED`

### Justificativa
- Validação matemática é determinística, sem latência de rede e sem dependência de terceiros
- A API externa é instável (Heroku free tier) — não pode ser bloqueante
- Fail-open em falha de rede garante disponibilidade do cadastro
- `VOTER_VALIDATION_ENABLED=false` como padrão protege contra a instabilidade atual

### Algoritmo (módulo 11)
```python
def _cpf_matematicamente_valido(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = 0 if (soma * 10 % 11) >= 10 else (soma * 10 % 11)
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = 0 if (soma * 10 % 11) >= 10 else (soma * 10 % 11)
    return d1 == int(cpf[9]) and d2 == int(cpf[10])
```

---

## ADR-004 — Scheduler asyncio nativo

**Data:** Junho 2026
**Status:** Aceito

### Contexto
Sessões de votação expiram após N segundos. É necessário fechá-las automaticamente
e publicar o resultado no RabbitMQ.

### Decisão
Usar `asyncio.create_task()` no `lifespan` do FastAPI para um loop de background.

### Alternativas consideradas
- **Celery + Redis**: overhead significativo, dependência adicional, overkill para o escopo
- **APScheduler**: dependência extra sem benefício claro sobre asyncio nativo

### Justificativa
- Zero dependências adicionais
- Integração natural com o event loop do FastAPI
- Suficiente para o escopo (checagem a cada 30s)
- Cancelamento limpo no shutdown via `asyncio.Task.cancel()`

### Limitação conhecida
Sem persistência de estado entre restarts (documentado em TD-007).
O `RegistrarVotoUseCase` valida expiração em tempo real para compensar.

---

## ADR-005 — Versionamento por prefixo de URL

**Data:** Junho 2026
**Status:** Aceito

### Decisão
Estratégia `/api/v1/...` com prefixo na URL.

### Justificativa
- Explícito, sem ambiguidade
- Suportado nativamente pelo FastAPI (`APIRouter(prefix="/api/v1")`)
- Novas versões podem coexistir no mesmo processo sem breaking change

### Exemplo de evolução
```python
# v1 (atual)
router_v1 = APIRouter(prefix="/api/v1")

# v2 (futura, sem breaking change para clientes v1)
router_v2 = APIRouter(prefix="/api/v2")

app.include_router(router_v1)
app.include_router(router_v2)
```

---

## ADR-006 — PaginatedResponse[T] genérico

**Data:** Junho 2026
**Status:** Aceito

### Decisão
Schema de paginação genérico usando `Generic[T]` do Pydantic.

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
```

### Justificativa
- Consistência de contrato em todos os endpoints de listagem
- Uma única definição sem duplicação
- Pydantic v2 suporta `Generic[T]` nativamente com documentação OpenAPI correta

---

## ADR-007 — test_app separado do app principal

**Data:** Junho 2026
**Status:** Aceito

### Contexto
Importar `app.main` em testes disparava `setup_logging()` e o lifespan real
(tentando conectar ao MongoDB), quebrando os testes de API.

### Decisão
Criar um `test_app` dedicado nos testes de API com `_noop_lifespan`.

```python
@asynccontextmanager
async def _noop_lifespan(app: FastAPI):
    yield  # sem connect_db, sem scheduler

test_app = FastAPI(lifespan=_noop_lifespan)
register_exception_handlers(test_app)
test_app.include_router(api_v1_router)
```

### Justificativa
- Testes de API testam contratos HTTP, não infraestrutura
- Use Cases são mockados via `patch`, então a lógica de negócio ainda é exercida
- Startup instantâneo dos testes (sem timeout de conexão)
