# Platform API DTO Reference

Primary DTO packages:

| Area | Module |
| --- | --- |
| Shared errors / health / pagination | `api/dto/common.py` |
| Tenancy request/response | `api/dto/request/*`, `api/dto/response/*` |
| Engineering inventory | `api/dto/response/engineering.py` |
| Portfolio CRUD | `api/portfolio/dto.py` |
| Portfolio aggregation | `api/portfolio/aggregation_dto.py` |
| Ingestion | `api/ingestion/dto.py`, `intelligence_dto.py` |
| Knowledge graph | `api/knowledge_graph/dto.py`, `intelligence_dto.py` |
| Retrieval / answering | `api/retrieval/dto.py`, `api/answering/dto.py` |
| Executive / roadmap | `api/executive_*/dto.py`, `api/strategic_roadmap/dto.py` |

## Serialization

`api/contracts/serialization.to_jsonable` converts domain objects to JSON
primitives and unwraps single-field Platform ID value objects to strings.

## Validation

- Requests: FastAPI / Pydantic
- Responses (hardened paths): `api/contracts/validation.validate_response`
