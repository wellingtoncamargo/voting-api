from typing import Optional

from app.domain.entities.models import Pauta


class PautaRepository:
    async def criar(self, pauta: Pauta) -> Pauta:
        await pauta.insert()
        return pauta

    async def buscar_por_id(self, pauta_id: str) -> Optional[Pauta]:
        return await Pauta.find_one(Pauta.id == pauta_id)

    async def listar(self, skip: int = 0, limit: int = 20) -> list[Pauta]:
        return await Pauta.find_all().skip(skip).limit(limit).to_list()

    async def contar(self) -> int:
        return await Pauta.count()

    async def atualizar(self, pauta: Pauta, titulo: Optional[str], descricao: Optional[str]) -> Pauta:
        if titulo is not None:
            pauta.titulo = titulo
        if descricao is not None:
            pauta.descricao = descricao
        await pauta.save()
        return pauta

    async def deletar(self, pauta: Pauta) -> None:
        await pauta.delete()
