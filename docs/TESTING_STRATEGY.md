# Testing Strategy —  Voting API

## 1. Diagnóstico do Problema Identificado

### Causa Raiz
Testes falhando localmente e no GitHub Actions com:
```
AttributeError: 'FixtureDef' object has no attribute 'unittest'
```

**Por quê:** O atributo `FixtureDef.unittest` foi **removido no pytest 8.0**. Versões de
`pytest-asyncio < 0.23` ainda referenciam esse atributo no código do plugin de fixtures
assíncronas. Qualquer ambiente que instale `pytest-asyncio==0.21.x` com `pytest>=8.x` quebra
todos os testes de API que usam fixtures `async`.

**Combinações compatíveis:**

| pytest  | pytest-asyncio | Resultado          |
|---------|----------------|--------------------| 
| < 8.0   | 0.21.x         | ✓ OK               |
| >= 8.0  | 0.21.x         | ✗ QUEBRA           |
| >= 8.0  | >= 0.23.x      | ✓ OK               |

**Versão correta (fixada no `requirements.txt`):**
```
pytest==8.3.4
pytest-asyncio==0.24.0
anyio==4.7.0
```

---

## 2. Pirâmide de Testes

```
         ┌──────────────────┐
         │   E2E (futuro)   │  → docker compose up + requests reais
         └────────┬─────────┘
        ┌─────────┴──────────┐
        │  API / Integração  │  → 41 testes (httpx + FastAPI TestClient)
        └─────────┬──────────┘
      ┌───────────┴────────────┐
      │   Unitários (Use Cases)│  → 43 testes (AsyncMock, sem infra)
      └────────────────────────┘
```

---

## 3. Testes Unitários (`tests/unit/`)

### Princípios
- **Zero infraestrutura**: sem MongoDB, sem RabbitMQ, sem chamadas HTTP
- **AsyncMock** em todos os repositórios e clientes externos
- **`model_construct()`** nos Use Cases evita o `CollectionWasNotInitialized` do Beanie

### Cobertura por Use Case

| Use Case                      | Cenários testados                                              |
|-------------------------------|----------------------------------------------------------------|
| `CriarPautaUseCase`           | criação normal, sem descrição                                  |
| `ListarPautasUseCase`         | listagem, paginação (skip calculado corretamente)              |
| `AtualizarPautaUseCase`       | atualização, sem campos → erro, não encontrada → erro          |
| `DeletarPautaUseCase`         | deleção, não encontrada → erro, sessão ativa → erro            |
| `AbrirSessaoUseCase`          | abertura, duração padrão, pauta inexistente, sessão já ativa   |
| `ListarSessoesUseCase`        | listagem, pauta inexistente → erro                             |
| `EncerrarSessaoUseCase`       | encerramento, não encontrada, já encerrada                     |
| `RegistrarVotoUseCase`        | voto válido, sessão fechada, voto duplicado, associado ausente |
| `ListarVotosUseCase`          | listagem, sessão inexistente → erro                            |
| `ObterResultadoUseCase`       | APROVADA, REJEITADA, EMPATE, pauta não encontrada, sessão encerrada |
| `CadastrarAssociadoUseCase`   | cadastro, CPF duplicado                                        |
| `ListarAssociadosUseCase`     | listagem, paginação                                            |
| `DeletarAssociadoUseCase`     | deleção, não encontrado → erro                                 |
| `_cpf_matematicamente_valido` | CPF válido, com máscara, inválido, sequência uniforme, curto   |

**Total: 43 testes unitários**

### Padrão de escrita
```python
class TestCriarPautaUseCase:
    async def test_should_create_agenda(self):
        repo = AsyncMock()
        repo.criar.return_value = _pauta()
        result = await CriarPautaUseCase(repo).executar("Pauta Teste", "Descrição")
        repo.criar.assert_called_once()
        assert result.id == "pauta-1"
```

---

## 4. Testes de API (`tests/api/`)

### Princípios
- **Lifespan mockado**: `_noop_lifespan` evita conexão real ao MongoDB/RabbitMQ
- **`patch` nos Use Cases**: os controllers são testados sem instanciar infraestrutura
- **`test_app` separado** do `app` principal para não disparar `setup_logging()` na importação

### Padrão de escrita
```python
@asynccontextmanager
async def _noop_lifespan(app: FastAPI):
    yield

test_app = FastAPI(lifespan=_noop_lifespan)
register_exception_handlers(test_app)
test_app.include_router(api_v1_router)

class TestCriarPauta:
    async def test_returns_201(self, client):
        with patch("app.api.v1.routes.pautas.CriarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_pauta())
            r = await client.post("/api/v1/pautas", json={"titulo": "Teste"})
        assert r.status_code == 201
```

### Cobertura por endpoint

| Endpoint                                    | Cenários                                                       |
|---------------------------------------------|----------------------------------------------------------------|
| `GET /health`                               | 200 OK                                                         |
| `GET /pautas`                               | 200, paginação                                                 |
| `POST /pautas`                              | 201, 422 sem título                                            |
| `GET /pautas/{id}`                          | 200, 404                                                       |
| `PATCH /pautas/{id}`                        | 200, 400 sem campos, 404                                       |
| `DELETE /pautas/{id}`                       | 204, 409 com sessão ativa                                      |
| `GET /pautas/{id}/sessoes`                  | 200, 404                                                       |
| `POST /pautas/{id}/sessao`                  | 201 com/sem duração, 404, 409                                  |
| `PATCH /pautas/{id}/sessao/{id}/encerrar`   | 200, 404, 400 já encerrada                                     |
| `GET /pautas/{id}/resultado`                | 200, 404                                                       |
| `GET /votos/sessao/{id}`                    | 200, 404                                                       |
| `POST /votos`                               | 201, 422 voto inválido, 409 duplicado, 400 sessão fechada      |
| `GET /associados`                           | 200, paginação                                                 |
| `POST /associados`                          | 201, 422 CPF curto, 422 não numérico, 409 duplicado            |
| `GET /associados/{id}`                      | 200, 404                                                       |
| `DELETE /associados/{id}`                   | 204, 404                                                       |
| `GET /associados/validar-cpf/{cpf}`         | 200 válido, 200 inválido                                       |

**Total: 41 testes de API**

---

## 5. Configuração (`pytest.ini`)

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
filterwarnings =
    ignore::pytest.PytestCollectionWarning
```

**`asyncio_mode = auto`** — obrigatório para que métodos `async` em classes de teste rodem sem
`@pytest.mark.asyncio` explícito. Requer `pytest-asyncio >= 0.21`.

**`filterwarnings`** — suprime o warning cosmético de `test_app` sendo detectado como
candidato a coleta de testes pelo pytest.

---

## 6. Como Rodar os Testes

```bash
# Instalar dependências (versões fixas)
pip install -r requirements.txt

# Todos os testes
pytest tests/ -v

# Apenas unitários
pytest tests/unit/ -v

# Apenas API
pytest tests/api/ -v

# Com cobertura (requer pytest-cov)
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 7. Próximos Passos

- [ ] Testes de integração com MongoDB real (`mongomock-motor` ou `testcontainers`)
- [ ] Cobertura mínima de 90% (configurar `--cov-fail-under=90` no CI)
- [ ] Testes de performance com Locust (`performance/locustfile.py`)
- [ ] Testes E2E via `docker compose up` + chamadas HTTP reais
