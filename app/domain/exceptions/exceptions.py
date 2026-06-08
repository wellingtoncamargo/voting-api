class PautaNaoEncontradaError(Exception):
    """Pauta não existe no banco de dados."""

class SessaoNaoEncontradaError(Exception):
    """Sessão não existe no banco de dados."""

class SessaoJaAtivaError(Exception):
    """A pauta já possui uma sessão ativa."""

class SessaoEncerradaError(Exception):
    """A sessão está encerrada e não aceita mais votos."""

class VotoDuplicadoError(Exception):
    """O associado já votou nesta sessão."""

class AssociadoNaoEncontradoError(Exception):
    """Associado não cadastrado."""

class AssociadoJaCadastradoError(Exception):
    """CPF já cadastrado."""

class AssociadoImpedidoError(Exception):
    """Associado não está habilitado para votar (UNABLE_TO_VOTE)."""

class CpfInvalidoError(Exception):
    """CPF inválido matematicamente ou não encontrado na API externa."""

class PautaNaoAtualizadaError(Exception):
    """Nenhum campo válido fornecido para atualização."""

class SessaoNaoPodeSerRemovidaError(Exception):
    """Sessão ativa não pode ser removida."""
