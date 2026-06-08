import logging
import re

import httpx

from app.core.config import settings
from app.domain.exceptions.exceptions import AssociadoImpedidoError, CpfInvalidoError

logger = logging.getLogger(__name__)


def _cpf_matematicamente_valido(cpf: str) -> bool:
    """
    Valida CPF pelo algoritmo dos dígitos verificadores (módulo 11).
    Aceita CPF com ou sem máscara (ex: 529.982.247-25 ou 52998224725).
    Rejeita sequências uniformes (ex: 111.111.111-11).
    """
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = 0 if (soma * 10 % 11) >= 10 else (soma * 10 % 11)
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = 0 if (soma * 10 % 11) >= 10 else (soma * 10 % 11)
    return d1 == int(cpf[9]) and d2 == int(cpf[10])


class VoterValidationClient:
    """
    Adapter de validação de CPF com duas camadas:

    1. Validação local (algoritmo módulo 11) — sempre executada.
       Rejeita CPFs matematicamente inválidos sem chamada de rede.

    2. API externa (Heroku) — consultada apenas se VOTER_VALIDATION_ENABLED=true.
       Opera em fail-open em caso de falha de rede ou status inesperado.
       Para habilitar: defina VOTER_VALIDATION_ENABLED=true no .env.
    """

    async def validar_cpf(self, cpf: str) -> None:
        logger.info("Iniciando validação de CPF.", extra={"event": "cpf_validation_start", "cpf": cpf})

        # Camada 1: validação matemática local (sempre ativa)
        if not _cpf_matematicamente_valido(cpf):
            logger.warning("CPF inválido matematicamente.", extra={"event": "cpf_math_invalid", "cpf": cpf})
            raise CpfInvalidoError(
                f"CPF {cpf} é matematicamente inválido. Verifique os dígitos verificadores."
            )

        logger.info("CPF válido matematicamente.", extra={"event": "cpf_math_valid", "cpf": cpf})

        # Camada 2: API externa (opcional)
        if not settings.VOTER_VALIDATION_ENABLED:
            logger.info("Validação externa desabilitada; CPF aceito.", extra={"event": "cpf_external_disabled"})
            return

        await self._validar_api_externa(cpf)

    async def _validar_api_externa(self, cpf: str) -> None:
        url = f"{settings.VOTER_VALIDATION_URL}/users/{cpf}"
        logger.info("Consultando API externa.", extra={"event": "cpf_external_start", "cpf": cpf})

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
            except httpx.RequestError as exc:
                logger.error("Falha de rede; fail-open.", extra={"event": "cpf_external_network_error", "error": str(exc)})
                return

        if response.status_code == 404:
            raise CpfInvalidoError(f"CPF {cpf} não encontrado na base de dados externa.")

        if response.status_code != 200:
            logger.error("Status inesperado na API externa; fail-open.", extra={"status": response.status_code})
            return

        data = response.json()
        if data.get("status") == "UNABLE_TO_VOTE":
            raise AssociadoImpedidoError(f"Associado com CPF {cpf} não está habilitado para votar.")

        logger.info("CPF validado pela API externa.", extra={"event": "cpf_external_ok", "cpf": cpf})
