from fastapi import APIRouter
from app.api.v1.routes import auth, business, payments, scores, system, persons 

router = APIRouter(prefix="/api/v1")

router.include_router(systems.router)
router.include_router(auth.router)
router.include_router(business.router)
router.include_router(persons.router)
router.include_router(payments.router)
router.include_router(scores.router)
