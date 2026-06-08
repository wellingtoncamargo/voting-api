from typing import Optional

from app.domain.entities.models import Voto


class VotoRepository:
    async def criar(self, voto: Voto) -> Voto:
        await voto.insert()
        return voto

    async def buscar_por_id(self, voto_id: str) -> Optional[Voto]:
        return await Voto.find_one(Voto.id == voto_id)

    async def buscar_voto_associado_na_sessao(
        self, sessao_id: str, associado_id: str
    ) -> Optional[Voto]:
        return await Voto.find_one(
            Voto.sessao_id == sessao_id,
            Voto.associado_id == associado_id,
        )

    async def listar_por_sessao(self, sessao_id: str, skip: int = 0, limit: int = 50) -> list[Voto]:
        return await Voto.find(Voto.sessao_id == sessao_id).skip(skip).limit(limit).to_list()

    async def contar_por_sessao(self, sessao_id: str) -> int:
        return await Voto.find(Voto.sessao_id == sessao_id).count()

    async def contar_votos_por_sessao(self, sessao_id: str) -> dict:
        pipeline = [
            {"$match": {"sessao_id": sessao_id}},
            {"$group": {"_id": "$voto", "total": {"$sum": 1}}},
        ]
        resultado = await Voto.aggregate(pipeline).to_list()
        contagem: dict[str, int] = {"SIM": 0, "NAO": 0}
        for item in resultado:
            contagem[item["_id"]] = item["total"]
        return contagem
