import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.backend.api.dependencies import require_authenticated
from src.backend.application.realtime import realtime_manager
from src.backend.domain.common.auth import ActorContext

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.get("/stream")
async def stream_realtime(
    actor: ActorContext = Depends(require_authenticated),
) -> StreamingResponse:
    keys = _actor_keys(actor)
    subscription = realtime_manager.subscribe(keys)

    async def event_stream() -> AsyncIterator[str]:
        try:
            yield ": connected\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(subscription.queue.get(), timeout=25)
                except TimeoutError:
                    yield ": heartbeat\n\n"
                    continue
                yield _format_event(payload["event"], payload["data"])
        except asyncio.CancelledError:
            raise
        finally:
            realtime_manager.unsubscribe(subscription)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _actor_keys(actor: ActorContext) -> set[str]:
    if actor.is_management:
        return {"management", f"management:{actor.actor_id}"}
    if actor.resident_id:
        return {f"resident:{actor.resident_id}"}
    return set()


def _format_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
