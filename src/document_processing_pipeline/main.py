from document_processing_pipeline.api.process import router as process_router
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Claim Processing Pipeline")
    app.include_router(process_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("document_processing_pipeline.main:app", host="0.0.0.0", port=8000, reload=False)
