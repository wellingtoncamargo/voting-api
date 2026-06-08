"""Testes de API — valida contratos HTTP. Lifespan mockado, sem infraestrutura."""
import pytest
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.router import router as api_v1_router
from app.core.exception_handlers import register_exception_handlers
from app.domain.entities.models import StatusSessao, VotoEnum
from app.domain.exceptions.exceptions import (
    AssociadoJaCadastradoError,
    AssociadoNaoEncontradoError,
    PautaNaoAtualizadaError,
    PautaNaoEncontradaError,
    SessaoEncerradaError,
    SessaoJaAtivaError,
    SessaoNaoEncontradaError,
    VotoDuplicadoError,
)


@asynccontextmanager
async def _noop_lifespan(app: FastAPI):
    yield


test_app = FastAPI(lifespan=_noop_lifespan)


@test_app.get("/health")
async def _health():
    return {"status": "ok", "version": "1.0.0"}


register_exception_handlers(test_app)
test_app.include_router(api_v1_router)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as c:
        yield c


def _pauta():
    m = MagicMock()
    m.id = "pauta-abc"
    m.titulo = "Pauta Teste"
    m.descricao = "Descrição"
    m.created_at = datetime.now()
    return m


def _sessao(aberta=True):
    m = MagicMock()
    m.id = "sessao-abc"
    m.pauta_id = "pauta-abc"
    m.inicio = datetime.now()
    m.fim = datetime.now() + timedelta(minutes=1) if aberta else datetime.now() - timedelta(seconds=1)
    m.status = StatusSessao.OPEN if aberta else StatusSessao.CLOSED
    return m


def _voto():
    m = MagicMock()
    m.id = "voto-abc"
    m.sessao_id = "sessao-abc"
    m.associado_id = "assoc-abc"
    m.voto = VotoEnum.SIM
    m.created_at = datetime.now()
    return m


def _associado():
    m = MagicMock()
    m.id = "assoc-abc"
    m.cpf = "52998224725"
    m.created_at = datetime.now()
    return m


def _paginated(items):
    m = MagicMock()
    m.items = items
    m.total = len(items)
    m.page = 1
    m.limit = 20
    return m


class TestHealth:
    async def test_returns_ok(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestListarPautas:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.pautas.ListarPautasUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_paginated([_pauta()]))
            r = await client.get("/api/v1/pautas")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_pagination_params(self, client):
        with patch("app.api.v1.routes.pautas.ListarPautasUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_paginated([]))
            r = await client.get("/api/v1/pautas?page=2&limit=5")
        assert r.status_code == 200


class TestCriarPauta:
    async def test_returns_201(self, client):
        with patch("app.api.v1.routes.pautas.CriarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_pauta())
            r = await client.post("/api/v1/pautas", json={"titulo": "Teste"})
        assert r.status_code == 201
        assert r.json()["id"] == "pauta-abc"

    async def test_returns_422_without_titulo(self, client):
        r = await client.post("/api/v1/pautas", json={})
        assert r.status_code == 422


class TestBuscarPauta:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.pautas.PautaRepository") as M:
            M.return_value.buscar_por_id = AsyncMock(return_value=_pauta())
            r = await client.get("/api/v1/pautas/pauta-abc")
        assert r.status_code == 200

    async def test_returns_404(self, client):
        with patch("app.api.v1.routes.pautas.PautaRepository") as M:
            M.return_value.buscar_por_id = AsyncMock(return_value=None)
            r = await client.get("/api/v1/pautas/inexistente")
        assert r.status_code == 404


class TestAtualizarPauta:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.pautas.AtualizarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_pauta())
            r = await client.patch("/api/v1/pautas/pauta-abc", json={"titulo": "Novo"})
        assert r.status_code == 200

    async def test_returns_400_when_no_fields(self, client):
        with patch("app.api.v1.routes.pautas.AtualizarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=PautaNaoAtualizadaError("Sem campos."))
            r = await client.patch("/api/v1/pautas/pauta-abc", json={})
        assert r.status_code == 400

    async def test_returns_404(self, client):
        with patch("app.api.v1.routes.pautas.AtualizarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=PautaNaoEncontradaError("Não encontrada."))
            r = await client.patch("/api/v1/pautas/x", json={"titulo": "X"})
        assert r.status_code == 404


class TestDeletarPauta:
    async def test_returns_204(self, client):
        with patch("app.api.v1.routes.pautas.DeletarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=None)
            r = await client.delete("/api/v1/pautas/pauta-abc")
        assert r.status_code == 204

    async def test_returns_409_when_has_active_session(self, client):
        with patch("app.api.v1.routes.pautas.DeletarPautaUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=SessaoJaAtivaError("Sessão ativa."))
            r = await client.delete("/api/v1/pautas/pauta-abc")
        assert r.status_code == 409


class TestListarSessoes:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.pautas.ListarSessoesUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_paginated([_sessao()]))
            r = await client.get("/api/v1/pautas/pauta-abc/sessoes")
        assert r.status_code == 200

    async def test_returns_404_when_pauta_not_found(self, client):
        with patch("app.api.v1.routes.pautas.ListarSessoesUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=PautaNaoEncontradaError("Não encontrada."))
            r = await client.get("/api/v1/pautas/x/sessoes")
        assert r.status_code == 404


class TestAbrirSessao:
    async def test_returns_201_with_duration(self, client):
        with patch("app.api.v1.routes.pautas.AbrirSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_sessao())
            r = await client.post("/api/v1/pautas/pauta-abc/sessao", json={"duracao_segundos": 120})
        assert r.status_code == 201

    async def test_returns_201_without_duration(self, client):
        with patch("app.api.v1.routes.pautas.AbrirSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_sessao())
            r = await client.post("/api/v1/pautas/pauta-abc/sessao", json={})
        assert r.status_code == 201

    async def test_returns_404_when_pauta_not_found(self, client):
        with patch("app.api.v1.routes.pautas.AbrirSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=PautaNaoEncontradaError("Não encontrada."))
            r = await client.post("/api/v1/pautas/x/sessao", json={})
        assert r.status_code == 404

    async def test_returns_409_when_active_session(self, client):
        with patch("app.api.v1.routes.pautas.AbrirSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=SessaoJaAtivaError("Ativa."))
            r = await client.post("/api/v1/pautas/pauta-abc/sessao", json={})
        assert r.status_code == 409


class TestEncerrarSessao:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.pautas.EncerrarSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_sessao(aberta=False))
            r = await client.patch("/api/v1/pautas/pauta-abc/sessao/sessao-abc/encerrar")
        assert r.status_code == 200
        assert r.json()["status"] == "CLOSED"

    async def test_returns_404(self, client):
        with patch("app.api.v1.routes.pautas.EncerrarSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=SessaoNaoEncontradaError("Não encontrada."))
            r = await client.patch("/api/v1/pautas/p/sessao/x/encerrar")
        assert r.status_code == 404

    async def test_returns_400_when_already_closed(self, client):
        with patch("app.api.v1.routes.pautas.EncerrarSessaoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=SessaoEncerradaError("Já encerrada."))
            r = await client.patch("/api/v1/pautas/p/sessao/sessao-abc/encerrar")
        assert r.status_code == 400


class TestObterResultado:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.pautas.ObterResultadoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value={"sim": 5, "nao": 2, "resultado": "APROVADA"})
            r = await client.get("/api/v1/pautas/pauta-abc/resultado")
        assert r.status_code == 200
        assert r.json()["resultado"] == "APROVADA"

    async def test_returns_404(self, client):
        with patch("app.api.v1.routes.pautas.ObterResultadoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=PautaNaoEncontradaError("Não encontrada."))
            r = await client.get("/api/v1/pautas/x/resultado")
        assert r.status_code == 404


class TestListarVotos:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.votos.ListarVotosUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_paginated([_voto()]))
            r = await client.get("/api/v1/votos/sessao/sessao-abc")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    async def test_returns_404_when_session_not_found(self, client):
        with patch("app.api.v1.routes.votos.ListarVotosUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=SessaoNaoEncontradaError("Não encontrada."))
            r = await client.get("/api/v1/votos/sessao/x")
        assert r.status_code == 404


class TestRegistrarVoto:
    async def test_returns_201(self, client):
        with patch("app.api.v1.routes.votos.RegistrarVotoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_voto())
            r = await client.post("/api/v1/votos", json={"sessao_id": "s", "associado_id": "a", "voto": "SIM"})
        assert r.status_code == 201

    async def test_returns_422_invalid_voto(self, client):
        r = await client.post("/api/v1/votos", json={"sessao_id": "s", "associado_id": "a", "voto": "TALVEZ"})
        assert r.status_code == 422

    async def test_returns_409_on_duplicate(self, client):
        with patch("app.api.v1.routes.votos.RegistrarVotoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=VotoDuplicadoError("Duplicado."))
            r = await client.post("/api/v1/votos", json={"sessao_id": "s", "associado_id": "a", "voto": "SIM"})
        assert r.status_code == 409

    async def test_returns_400_on_closed_session(self, client):
        with patch("app.api.v1.routes.votos.RegistrarVotoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=SessaoEncerradaError("Encerrada."))
            r = await client.post("/api/v1/votos", json={"sessao_id": "s", "associado_id": "a", "voto": "NAO"})
        assert r.status_code == 400


class TestListarAssociados:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.associados.ListarAssociadosUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_paginated([_associado()]))
            r = await client.get("/api/v1/associados")
        assert r.status_code == 200

    async def test_pagination(self, client):
        with patch("app.api.v1.routes.associados.ListarAssociadosUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_paginated([]))
            r = await client.get("/api/v1/associados?page=2&limit=5")
        assert r.status_code == 200


class TestCadastrarAssociado:
    async def test_returns_201(self, client):
        with patch("app.api.v1.routes.associados.CadastrarAssociadoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=_associado())
            r = await client.post("/api/v1/associados", json={"cpf": "52998224725"})
        assert r.status_code == 201

    async def test_returns_422_short_cpf(self, client):
        r = await client.post("/api/v1/associados", json={"cpf": "123"})
        assert r.status_code == 422

    async def test_returns_422_non_numeric_cpf(self, client):
        r = await client.post("/api/v1/associados", json={"cpf": "1234567890a"})
        assert r.status_code == 422

    async def test_returns_409_when_duplicate_cpf(self, client):
        with patch("app.api.v1.routes.associados.CadastrarAssociadoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=AssociadoJaCadastradoError("Já cadastrado."))
            r = await client.post("/api/v1/associados", json={"cpf": "52998224725"})
        assert r.status_code == 409


class TestBuscarAssociado:
    async def test_returns_200(self, client):
        with patch("app.api.v1.routes.associados.AssociadoRepository") as M:
            M.return_value.buscar_por_id = AsyncMock(return_value=_associado())
            r = await client.get("/api/v1/associados/assoc-abc")
        assert r.status_code == 200

    async def test_returns_404(self, client):
        with patch("app.api.v1.routes.associados.AssociadoRepository") as M:
            M.return_value.buscar_por_id = AsyncMock(return_value=None)
            r = await client.get("/api/v1/associados/x")
        assert r.status_code == 404


class TestDeletarAssociado:
    async def test_returns_204(self, client):
        with patch("app.api.v1.routes.associados.DeletarAssociadoUseCase") as M:
            M.return_value.executar = AsyncMock(return_value=None)
            r = await client.delete("/api/v1/associados/assoc-abc")
        assert r.status_code == 204

    async def test_returns_404(self, client):
        with patch("app.api.v1.routes.associados.DeletarAssociadoUseCase") as M:
            M.return_value.executar = AsyncMock(side_effect=AssociadoNaoEncontradoError("Não encontrado."))
            r = await client.delete("/api/v1/associados/x")
        assert r.status_code == 404


class TestValidarCpf:
    async def test_cpf_valido(self, client):
        r = await client.get("/api/v1/associados/validar-cpf/52998224725")
        assert r.status_code == 200
        assert r.json()["valido"] is True

    async def test_cpf_invalido(self, client):
        r = await client.get("/api/v1/associados/validar-cpf/12345678901")
        assert r.status_code == 200
        assert r.json()["valido"] is False
