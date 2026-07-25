from fastapi import FastAPI

from app.api import events, health, sync, tickets
from app.bootstrap.lifespan import lifespan

app = FastAPI(title="Events Aggregator", lifespan=lifespan)

app.include_router(health.router)
app.include_router(sync.router)
app.include_router(events.router)
app.include_router(tickets.router)
