from app.api.routes import (
    analysis,
    contradictions,
    documents,
    eligibility,
    health,
    planner,
    programs,
    readiness,
)

ROUTERS = [
    health.router,
    programs.router,
    documents.router,
    eligibility.router,
    contradictions.router,
    readiness.router,
    planner.router,
    analysis.router,
]

__all__ = ["ROUTERS"]
