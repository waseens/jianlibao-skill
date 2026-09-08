from fastapi import APIRouter

from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks")
service = TaskService()


@router.post("")
async def create_task() -> dict[str, str]:
    return service.create()
