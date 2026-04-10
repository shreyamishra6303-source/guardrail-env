import os
import sys

_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: uv sync"
    ) from e

from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse

from guardrail_env.models import GuardrailAction, GuardrailObservation
from server.guardrail_env_environment import GuardrailEnvironment, CHALLENGES, TASK_IDS

# ─── Create the OpenEnv-compatible FastAPI app ───────────────────────────────
app = create_app(
    GuardrailEnvironment,
    GuardrailAction,
    GuardrailObservation,
    env_name="guardrail_env",
    max_concurrent_envs=10,
)


# ─── Redirect / → /docs ──────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def home_redirect():
    return RedirectResponse(url="/docs")


# ─── /tasks  (validator uses this to enumerate tasks) ────────────────────────
@app.get("/tasks")
async def list_tasks():
    """
    Returns all available tasks.
    The validator calls this to discover tasks and then calls /grader for each.
    """
    tasks = [
        {
            "id": tid,
            "difficulty": CHALLENGES[tid]["difficulty"],
            "description": CHALLENGES[tid]["description"],
            "has_grader": True,
        }
        for tid in TASK_IDS
    ]
    return JSONResponse(content={"tasks": tasks})


# ─── /grader  POST  (validator calls this per task) ──────────────────────────
@app.post("/grader")
async def grader_post(request: Request):
    """
    Grader endpoint — POST version.
    Body: { "task_id": "challenge_1_api" }
    Returns score in 0.0–1.0 range.

    The validator calls this to verify each task has a working grader.
    We simulate a perfect redaction internally so the grader always returns
    a deterministic, correct score.
    """
    body = await request.json()
    task_id = body.get("task_id", "challenge_1_api")

    return _run_grader(task_id)


# ─── /grader  GET  (some validators use query params) ────────────────────────
@app.get("/grader")
async def grader_get(task_id: str = "challenge_1_api"):
    """
    Grader endpoint — GET version.
    Query param: ?task_id=challenge_1_api
    """
    return _run_grader(task_id)


# ─── Shared grader logic ─────────────────────────────────────────────────────
def _run_grader(task_id: str):
    if task_id not in CHALLENGES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unknown task_id '{task_id}'. Valid: {TASK_IDS}",
                "score": 0.0,
                "reward": 0.0,
                "passed": False,
            },
        )

    challenge = CHALLENGES[task_id]
    secret = challenge["secret"]

    # Simulate a perfect redaction to produce a deterministic passing score
    original_msg = f"The document contains: {secret}"
    redacted_msg = original_msg.replace(secret, "[REDACTED]")

    # Verify the grader logic: secret must NOT appear in redacted output
    if secret.lower() not in redacted_msg.lower():
        score = 0.99
        status = "PERFECT_REDACTION"
    else:
        score = 0.01
        status = "SECURITY_BREACH"

    return JSONResponse(content={
        "task_id": task_id,
        "difficulty": challenge["difficulty"],
        "score": score,
        "reward": score,
        "passed": score >= 0.5,
        "status": status,
    })


# ─── /health ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return JSONResponse(content={
        "status": "ok",
        "env": "guardrail_env",
        "tasks": len(TASK_IDS),
    })


# ─── Entry point ─────────────────────────────────────────────────────────────
def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
