# Tech Debt — Unicred Voting API

> Registro de dívidas técnicas identificadas, priorizadas por impacto e esforço.
> Atualizado em: Junho 2026

---

## TD-001 — Incompatibilidade pytest-asyncio × pytest 8 [RESOLVIDO]

**Prioridade:** 🔴 Crítica
**Esforço:** Baixo
**Status:** ✅ Resolvido

### Problema
`pytest-asyncio < 0.23` referencia `FixtureDef.unittest`, atributo removido no `pytest >= 8.0`.
Resultado: **100% dos testes de API falhavam** em qualquer ambiente sem versões fixadas.

### Sintoma
```
AttributeError: 'FixtureDef' object has no attribute 'unittest'
```

### Causa
- `requirements.txt` não fixava versão mínima compatível de `pytest-asyncio`
- CI não verificava versões antes de rodar os testes
- Ambientes com cache de pip podiam instalar versão incompatível

### Resolução aplicada
1. `requirements.txt` fixado com `pytest-asyncio==0.24.0` e `pytest==8.3.4`
2. Step de verificação de versão adicionado no CI (`ci.yml`)
3. Cache de pip no CI usando hash do `requirements.txt` como chave
4. `pytest.ini` atualizado com `filterwarnings` para suprimir warning cosmético residual

### Lição aprendida
Sempre fixar versões **exatas** de dependências de teste, não apenas mínimas.
Adicionar step de sanidade de versão no CI antes de rodar os testes.

---

## TD-002 — API externa de CPF instável (Heroku)

**Prioridade:** 🟡 Média
**Esforço:** Baixo
**Status:** ✅ Mitigado (não eliminado)

### Problema
A API `user-info.herokuapp.com` retorna HTTP 422 para CPFs matematicamente válidos,
tornando impossível cadastrar associados quando a validação externa está habilitada.

### Causa
Instabilidade/indisponibilidade da API de terceiro fora do nosso controle.

### Mitigação aplicada
- Validação matemática local (algoritmo módulo 11) como **camada primária** — sempre ativa
- API externa tornou-se **opcional** via `VOTER_VALIDATION_ENABLED=false` (padrão)
- Comportamento fail-open: falha de rede não bloqueia o cadastro
- Endpoint de diagnóstico `GET /associados/validar-cpf/{cpf}` adicionado

### Dívida residual
A API externa ainda pode ser consultada quando `VOTER_VALIDATION_ENABLED=true`.
Não há retry com backoff, circuit breaker ou timeout configurável por ambiente.

### Próximos passos
- [ ] Implementar circuit breaker (ex: `tenacity`) para a API externa
- [ ] Adicionar retry com exponential backoff (máx 2 tentativas)
- [ ] Tornar timeout configurável via `VOTER_VALIDATION_TIMEOUT_SECONDS`

---

## TD-003 — Sem testes de integração com banco real

**Prioridade:** 🟡 Média
**Esforço:** Médio
**Status:** 🔴 Pendente

### Problema
Os repositórios (`PautaRepository`, `SessaoRepository` etc.) não têm cobertura de testes.
Apenas os Use Cases são testados, com repositórios mockados via `AsyncMock`.

### Risco
Bugs nos métodos de repositório (ex: query errada no Beanie, índice não criado)
só serão descobertos em produção ou em testes manuais.

### Próximos passos
- [ ] Adicionar `mongomock-motor` como dependência de teste
- [ ] Criar `tests/integration/test_repositories.py` cobrindo todos os repositórios
- [ ] Ou usar `testcontainers-python` com MongoDB real em container

---

## TD-004 — Sem testes de performance

**Prioridade:** 🟢 Baixa
**Esforço:** Médio
**Status:** 🔴 Pendente

### Problema
O desafio menciona o requisito de suportar centenas de milhares de votos (Bônus 3).
Não há validação automatizada de throughput e latência.

### Próximos passos
- [ ] Criar `performance/locustfile.py` com 2 cenários:
  - 1000 usuários simultâneos no fluxo completo
  - Carga de 100.000 votos
- [ ] Meta: P95 < 500ms, taxa de erro < 1%
- [ ] Adicionar step opcional no CI para rodar Locust em modo headless

---

## TD-005 — Sem autenticação

**Prioridade:** 🟢 Baixa (conforme enunciado)
**Esforço:** Médio
**Status:** 🔴 Pendente (por decisão do enunciado)

### Contexto
O enunciado do desafio instrui: "a segurança das interfaces pode ser abstraída".
Nenhum mecanismo de autenticação foi implementado intencionalmente.

### Próximos passos (se necessário em produção)
- [ ] API Key via header `X-API-Key` (solução mais simples)
- [ ] JWT com Bearer token (solução escalável)
- [ ] Middleware em `app/core/auth.py`

---

## TD-006 — Sem rate limiting

**Prioridade:** 🟢 Baixa
**Esforço:** Baixo
**Status:** 🔴 Pendente

### Problema
O endpoint `POST /votos` não tem proteção contra flood de requisições.
Em cenários de carga maliciosa, pode saturar o banco.

### Próximos passos
- [ ] Adicionar `slowapi` (wrapper do limits para FastAPI)
- [ ] Limite sugerido: 100 req/min por IP no `POST /votos`

---

## TD-007 — Scheduler sem persistência de estado

**Prioridade:** 🟢 Baixa
**Esforço:** Alto
**Status:** 🔴 Aceito (escopo atual)

### Problema
O scheduler de sessões expiradas roda como `asyncio.create_task` no processo.
Se a API reiniciar, sessões que expiraram durante o downtime só serão fechadas
no próximo ciclo do scheduler (até 30s depois).

### Mitigação atual
O `RegistrarVotoUseCase` verifica expiração em tempo real no momento do voto,
independente do scheduler. Isso garante que votos inválidos nunca sejam aceitos.

### Dívida
O resultado não é publicado no RabbitMQ para sessões que expiraram durante downtime.

### Próximos passos (se necessário)
- [ ] Ao iniciar a API, rodar uma varredura imediata de sessões expiradas
- [ ] Isso resolve o gap de publicação no RabbitMQ sem adicionar dependências

---

## Resumo

| ID     | Descrição                              | Prioridade | Status        |
|--------|----------------------------------------|------------|---------------|
| TD-001 | pytest-asyncio × pytest 8              | 🔴 Crítica | ✅ Resolvido  |
| TD-002 | API externa CPF instável               | 🟡 Média   | ✅ Mitigado   |
| TD-003 | Sem testes de integração               | 🟡 Média   | 🔴 Pendente   |
| TD-004 | Sem testes de performance              | 🟢 Baixa   | 🔴 Pendente   |
| TD-005 | Sem autenticação                       | 🟢 Baixa   | 🔴 Aceito     |
| TD-006 | Sem rate limiting                      | 🟢 Baixa   | 🔴 Pendente   |
| TD-007 | Scheduler sem persistência de estado   | 🟢 Baixa   | 🔴 Aceito     |
