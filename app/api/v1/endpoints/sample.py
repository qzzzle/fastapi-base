from fastapi import APIRouter

# Reason: In v1 we keep each feature in its own endpoint module.
# This "sample" router shows the minimal pattern without auth or DI.
router = APIRouter(
    prefix="/sample",   # final path will become /api/v1/sample
    tags=["sample"],    # visible in /docs as a group
)

@router.get("", summary="Say hello")
def say_hello() -> dict:
    """
    Simple public GET for manual testing.
    Reason: quick smoke test through browser/Postman without auth.
    """
    return {"message": "hello"}
