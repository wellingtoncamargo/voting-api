from typing import Optional

from app.domain.entities.models import Sessao, StatusSessao


class SessaoRepository:
    async def criar(self, sessao: Sessao) -> Sessao:
        await sessao.insert()
        return sessao

    async def buscar_por_id(self, sessao_id: str) -> Optional[Sessao]:
        return await Sessao.find_one(Sessao.id == sessao_id)

    async def buscar_sessao_ativa_por_pauta(self, pauta_id: str) -> Optional[Sessao]:
        return await Sessao.find_one(
            Sessao.pauta_id == pauta_id,
            Sessao.status == StatusSessao.OPEN,
        )

    async def buscar_ultima_sessao_por_pauta(self, pauta_id: str) -> Optional[Sessao]:
        return await Sessao.find(Sessao.pauta_id == pauta_id).sort(-Sessao.inicio).first_or_none()

    async def listar_por_pauta(self, pauta_id: str, skip: int = 0, limit: int = 20) -> list[Sessao]:
        return await Sessao.find(Sessao.pauta_id == pauta_id).skip(skip).limit(limit).to_list()

    async def contar_por_pauta(self, pauta_id: str) -> int:
        return await Sessao.find(Sessao.pauta_id == pauta_id).count()

    async def atualizar_status(self, sessao: Sessao, status: StatusSessao) -> Sessao:
        sessao.status = status
        await sessao.save()
        return sessao

    async def deletar(self, sessao: Sessao) -> None:
        await sessao.delete()
