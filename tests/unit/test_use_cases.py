"""Testes unitários dos Use Cases — sem dependência de banco ou rede."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.abrir_sessao import AbrirSessaoUseCase
from app.application.use_cases.atualizar_pauta import AtualizarPautaUseCase
from app.application.use_cases.cadastrar_associado import CadastrarAssociadoUseCase
from app.application.use_cases.criar_pauta import CriarPautaUseCase
from app.application.use_cases.deletar_associado import DeletarAssociadoUseCase
from app.application.use_cases.deletar_pauta import DeletarPautaUseCase
from app.application.use_cases.encerrar_sessao import EncerrarSessaoUseCase
from app.application.use_cases.listar_associados import ListarAssociadosUseCase
from app.application.use_cases.listar_pautas import ListarPautasUseCase
from app.application.use_cases.listar_sessoes import ListarSessoesUseCase
from app.application.use_cases.listar_votos import ListarVotosUseCase
from app.application.use_cases.obter_resultado import ObterResultadoUseCase
from app.application.use_cases.registrar_voto import RegistrarVotoUseCase
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
from app.infrastructure.external.voter_validation_client import _cpf_matematicamente_valido


def _pauta(pauta_id="pauta-1"):
    m = MagicMock()
    m.id = pauta_id
    m.titulo = "Pauta Teste"
    m.descricao = "Descrição"
    m.created_at = datetime.now()
    return m


def _sessao(pauta_id="pauta-1", aberta=True):
    m = MagicMock()
    m.id = "sessao-1"
    m.pauta_id = pauta_id
    m.inicio = datetime.now()
    m.fim = datetime.now() + timedelta(minutes=1) if aberta else datetime.now() - timedelta(minutes=1)
    m.status = StatusSessao.OPEN if aberta else StatusSessao.CLOSED
    return m


def _associado(associado_id="assoc-1"):
    m = MagicMock()
    m.id = associado_id
    m.cpf = "52998224725"
    m.created_at = datetime.now()
    return m


def _voto():
    m = MagicMock()
    m.id = "voto-1"
    m.sessao_id = "sessao-1"
    m.associado_id = "assoc-1"
    m.voto = VotoEnum.SIM
    m.created_at = datetime.now()
    return m


class TestCpfValidacaoMatematica:
    def test_cpf_valido(self):
        assert _cpf_matematicamente_valido("52998224725") is True

    def test_outro_cpf_valido(self):
        assert _cpf_matematicamente_valido("11144477735") is True

    def test_cpf_com_mascara_valido(self):
        assert _cpf_matematicamente_valido("529.982.247-25") is True

    def test_cpf_invalido_digitos_errados(self):
        assert _cpf_matematicamente_valido("12345678901") is False

    def test_cpf_sequencia_uniforme_invalido(self):
        assert _cpf_matematicamente_valido("11111111111") is False

    def test_cpf_zeros_invalido(self):
        assert _cpf_matematicamente_valido("00000000000") is False

    def test_cpf_curto_invalido(self):
        assert _cpf_matematicamente_valido("1234567") is False


class TestCriarPautaUseCase:
    async def test_should_create_agenda(self):
        repo = AsyncMock()
        repo.criar.return_value = _pauta()
        result = await CriarPautaUseCase(repo).executar("Pauta Teste", "Descrição")
        repo.criar.assert_called_once()
        assert result.id == "pauta-1"

    async def test_should_create_without_descricao(self):
        repo = AsyncMock()
        repo.criar.return_value = _pauta()
        result = await CriarPautaUseCase(repo).executar("Pauta Teste", None)
        assert result.id == "pauta-1"


class TestListarPautasUseCase:
    async def test_should_list_pautas(self):
        repo = AsyncMock()
        repo.listar.return_value = [_pauta("p1"), _pauta("p2")]
        repo.contar.return_value = 2
        result = await ListarPautasUseCase(repo).executar(page=1, limit=20)
        assert len(result.items) == 2
        assert result.total == 2

    async def test_should_paginate(self):
        repo = AsyncMock()
        repo.listar.return_value = []
        repo.contar.return_value = 100
        await ListarPautasUseCase(repo).executar(page=3, limit=10)
        repo.listar.assert_called_once_with(skip=20, limit=10)


class TestAtualizarPautaUseCase:
    async def test_should_update_titulo(self):
        repo = AsyncMock()
        repo.buscar_por_id.return_value = _pauta()
        repo.atualizar.return_value = _pauta()
        result = await AtualizarPautaUseCase(repo).executar("pauta-1", titulo="Novo", descricao=None)
        repo.atualizar.assert_called_once()
        assert result.id == "pauta-1"

    async def test_should_raise_when_no_fields(self):
        repo = AsyncMock()
        with pytest.raises(PautaNaoAtualizadaError):
            await AtualizarPautaUseCase(repo).executar("pauta-1", None, None)

    async def test_should_raise_when_not_found(self):
        repo = AsyncMock()
        repo.buscar_por_id.return_value = None
        with pytest.raises(PautaNaoEncontradaError):
            await AtualizarPautaUseCase(repo).executar("x", "Titulo", None)


class TestDeletarPautaUseCase:
    async def test_should_delete(self):
        repo, sessao_repo = AsyncMock(), AsyncMock()
        repo.buscar_por_id.return_value = _pauta()
        sessao_repo.buscar_sessao_ativa_por_pauta.return_value = None
        await DeletarPautaUseCase(repo, sessao_repo).executar("pauta-1")
        repo.deletar.assert_called_once()

    async def test_should_raise_when_not_found(self):
        repo, sessao_repo = AsyncMock(), AsyncMock()
        repo.buscar_por_id.return_value = None
        with pytest.raises(PautaNaoEncontradaError):
            await DeletarPautaUseCase(repo, sessao_repo).executar("x")

    async def test_should_raise_when_has_active_session(self):
        repo, sessao_repo = AsyncMock(), AsyncMock()
        repo.buscar_por_id.return_value = _pauta()
        sessao_repo.buscar_sessao_ativa_por_pauta.return_value = _sessao()
        with pytest.raises(SessaoJaAtivaError):
            await DeletarPautaUseCase(repo, sessao_repo).executar("pauta-1")


class TestAbrirSessaoUseCase:
    async def test_should_open_session(self):
        pr, sr = AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = None
        sr.criar.return_value = _sessao()
        result = await AbrirSessaoUseCase(pr, sr).executar("pauta-1", 60)
        assert result.status == StatusSessao.OPEN

    async def test_should_use_default_duration(self):
        pr, sr = AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = None
        sr.criar.return_value = _sessao()
        await AbrirSessaoUseCase(pr, sr).executar("pauta-1", None)
        sr.criar.assert_called_once()

    async def test_should_raise_when_pauta_not_found(self):
        pr, sr = AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = None
        with pytest.raises(PautaNaoEncontradaError):
            await AbrirSessaoUseCase(pr, sr).executar("x", 60)

    async def test_should_raise_when_active_session_exists(self):
        pr, sr = AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = _sessao()
        with pytest.raises(SessaoJaAtivaError):
            await AbrirSessaoUseCase(pr, sr).executar("pauta-1", 60)


class TestListarSessoesUseCase:
    async def test_should_list_sessoes(self):
        pr, sr = AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.listar_por_pauta.return_value = [_sessao(), _sessao()]
        sr.contar_por_pauta.return_value = 2
        result = await ListarSessoesUseCase(pr, sr).executar("pauta-1", page=1, limit=20)
        assert len(result.items) == 2

    async def test_should_raise_when_pauta_not_found(self):
        pr, sr = AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = None
        with pytest.raises(PautaNaoEncontradaError):
            await ListarSessoesUseCase(pr, sr).executar("x")


class TestEncerrarSessaoUseCase:
    async def test_should_close_session(self):
        sr, vr = AsyncMock(), AsyncMock()
        sr.buscar_por_id.return_value = _sessao(aberta=True)
        sr.atualizar_status.return_value = _sessao(aberta=False)
        vr.contar_votos_por_sessao.return_value = {"SIM": 3, "NAO": 1}
        await EncerrarSessaoUseCase(sr, vr).executar("sessao-1")
        sr.atualizar_status.assert_called_once()

    async def test_should_raise_when_not_found(self):
        sr, vr = AsyncMock(), AsyncMock()
        sr.buscar_por_id.return_value = None
        with pytest.raises(SessaoNaoEncontradaError):
            await EncerrarSessaoUseCase(sr, vr).executar("x")

    async def test_should_raise_when_already_closed(self):
        sr, vr = AsyncMock(), AsyncMock()
        sr.buscar_por_id.return_value = _sessao(aberta=False)
        with pytest.raises(SessaoEncerradaError):
            await EncerrarSessaoUseCase(sr, vr).executar("sessao-1")


class TestRegistrarVotoUseCase:
    async def test_should_register_vote(self):
        sr, vr, ar = AsyncMock(), AsyncMock(), AsyncMock()
        ar.buscar_por_id.return_value = _associado()
        sr.buscar_por_id.return_value = _sessao(aberta=True)
        vr.buscar_voto_associado_na_sessao.return_value = None
        vr.criar.return_value = _voto()
        result = await RegistrarVotoUseCase(sr, vr, ar).executar("sessao-1", "assoc-1", VotoEnum.SIM)
        assert result.voto == VotoEnum.SIM

    async def test_should_not_vote_after_session_closed(self):
        sr, vr, ar = AsyncMock(), AsyncMock(), AsyncMock()
        ar.buscar_por_id.return_value = _associado()
        sr.buscar_por_id.return_value = _sessao(aberta=False)
        with pytest.raises(SessaoEncerradaError):
            await RegistrarVotoUseCase(sr, vr, ar).executar("sessao-1", "assoc-1", VotoEnum.SIM)

    async def test_should_not_allow_duplicate_vote(self):
        sr, vr, ar = AsyncMock(), AsyncMock(), AsyncMock()
        ar.buscar_por_id.return_value = _associado()
        sr.buscar_por_id.return_value = _sessao(aberta=True)
        vr.buscar_voto_associado_na_sessao.return_value = _voto()
        with pytest.raises(VotoDuplicadoError):
            await RegistrarVotoUseCase(sr, vr, ar).executar("sessao-1", "assoc-1", VotoEnum.SIM)

    async def test_should_raise_when_associate_not_found(self):
        sr, vr, ar = AsyncMock(), AsyncMock(), AsyncMock()
        ar.buscar_por_id.return_value = None
        with pytest.raises(AssociadoNaoEncontradoError):
            await RegistrarVotoUseCase(sr, vr, ar).executar("s", "x", VotoEnum.SIM)


class TestListarVotosUseCase:
    async def test_should_list_votos(self):
        sr, vr = AsyncMock(), AsyncMock()
        sr.buscar_por_id.return_value = _sessao()
        vr.listar_por_sessao.return_value = [_voto(), _voto()]
        vr.contar_por_sessao.return_value = 2
        result = await ListarVotosUseCase(sr, vr).executar("sessao-1")
        assert len(result.items) == 2

    async def test_should_raise_when_session_not_found(self):
        sr, vr = AsyncMock(), AsyncMock()
        sr.buscar_por_id.return_value = None
        with pytest.raises(SessaoNaoEncontradaError):
            await ListarVotosUseCase(sr, vr).executar("x")


class TestObterResultadoUseCase:
    async def test_should_calculate_aprovada(self):
        pr, sr, vr = AsyncMock(), AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = _sessao()
        vr.contar_votos_por_sessao.return_value = {"SIM": 10, "NAO": 3}
        result = await ObterResultadoUseCase(pr, sr, vr).executar("pauta-1")
        assert result == {"sim": 10, "nao": 3, "resultado": "APROVADA"}

    async def test_should_calculate_rejeitada(self):
        pr, sr, vr = AsyncMock(), AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = _sessao()
        vr.contar_votos_por_sessao.return_value = {"SIM": 2, "NAO": 8}
        result = await ObterResultadoUseCase(pr, sr, vr).executar("pauta-1")
        assert result["resultado"] == "REJEITADA"

    async def test_should_calculate_empate(self):
        pr, sr, vr = AsyncMock(), AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = _sessao()
        vr.contar_votos_por_sessao.return_value = {"SIM": 5, "NAO": 5}
        result = await ObterResultadoUseCase(pr, sr, vr).executar("pauta-1")
        assert result["resultado"] == "EMPATE"

    async def test_should_raise_when_pauta_not_found(self):
        pr, sr, vr = AsyncMock(), AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = None
        with pytest.raises(PautaNaoEncontradaError):
            await ObterResultadoUseCase(pr, sr, vr).executar("x")

    async def test_should_use_closed_session_when_no_active(self):
        pr, sr, vr = AsyncMock(), AsyncMock(), AsyncMock()
        pr.buscar_por_id.return_value = _pauta()
        sr.buscar_sessao_ativa_por_pauta.return_value = None
        sr.buscar_ultima_sessao_por_pauta.return_value = _sessao(aberta=False)
        vr.contar_votos_por_sessao.return_value = {"SIM": 3, "NAO": 1}
        result = await ObterResultadoUseCase(pr, sr, vr).executar("pauta-1")
        assert result["resultado"] == "APROVADA"


class TestCadastrarAssociadoUseCase:
    async def test_should_register_associate(self):
        repo, validator = AsyncMock(), AsyncMock()
        repo.buscar_por_cpf.return_value = None
        repo.criar.return_value = _associado()
        result = await CadastrarAssociadoUseCase(repo, validator).executar("52998224725")
        validator.validar_cpf.assert_called_once_with("52998224725")
        assert result.cpf == "52998224725"

    async def test_should_raise_when_cpf_already_registered(self):
        repo, validator = AsyncMock(), AsyncMock()
        repo.buscar_por_cpf.return_value = _associado()
        with pytest.raises(AssociadoJaCadastradoError):
            await CadastrarAssociadoUseCase(repo, validator).executar("52998224725")


class TestListarAssociadosUseCase:
    async def test_should_list_associados(self):
        repo = AsyncMock()
        repo.listar.return_value = [_associado("a1"), _associado("a2")]
        repo.contar.return_value = 2
        result = await ListarAssociadosUseCase(repo).executar(page=1, limit=20)
        assert len(result.items) == 2
        assert result.total == 2

    async def test_should_paginate_correctly(self):
        repo = AsyncMock()
        repo.listar.return_value = []
        repo.contar.return_value = 50
        await ListarAssociadosUseCase(repo).executar(page=2, limit=10)
        repo.listar.assert_called_once_with(skip=10, limit=10)


class TestDeletarAssociadoUseCase:
    async def test_should_delete_associado(self):
        repo = AsyncMock()
        repo.buscar_por_id.return_value = _associado()
        await DeletarAssociadoUseCase(repo).executar("assoc-1")
        repo.deletar.assert_called_once()

    async def test_should_raise_when_not_found(self):
        repo = AsyncMock()
        repo.buscar_por_id.return_value = None
        with pytest.raises(AssociadoNaoEncontradoError):
            await DeletarAssociadoUseCase(repo).executar("x")
