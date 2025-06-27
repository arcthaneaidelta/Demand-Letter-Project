from fastapi import APIRouter

from app.api.routes import auth, excel, template_rendering

api_router = APIRouter()
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(excel.router, tags=["Excel"])
api_router.include_router(template_rendering.router, tags=["Template Rendering"])
# api_router.include_router(generate.router, tags=["Generate"])
