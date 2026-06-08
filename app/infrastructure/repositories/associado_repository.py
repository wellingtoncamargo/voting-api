from typing import Optional

from app.domain.entities.models import Associado


class AssociadoRepository:
    async def criar(self, associado: Associado) -> Associado:
        await associado.insert()
        return associado

    async def buscar_por_id(self, associado_id: str) -> Optional[Associado]:
        return await Associado.find_one(Associado.id == associado_id)

    async def buscar_por_cpf(self, cpf: str) -> Optional[Associado]:
        return await Associado.find_one(Associado.cpf == cpf)

    async def listar(self, skip: int = 0, limit: int = 20) -> list[Associado]:
        return await Associado.find_all().skip(skip).limit(limit).to_list()

    async def contar(self) -> int:
        return await Associado.count()

    async def deletar(self, associado: Associado) -> None:
        await associado.delete()
