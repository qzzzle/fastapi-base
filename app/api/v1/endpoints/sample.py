from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Say hello")
def say_hello() -> dict:
    """
    Simple public GET for manual testing.
    Reason: quick smoke test through browser/Postman without auth.
    """
    return {"message": "hello"}
