from fastapi import FastAPI

app = FastAPI(
    title="DraftGuard API",
    description="Shipping document review and revision tracking.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "draftguard",
    }
