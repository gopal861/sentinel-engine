from fastapi import APIRouter, HTTPException
from sentinel.types import GovernRequest, GovernResponse, ErrorResponse
from sentinel.core.policy_engine import execute_governance
from sentinel.core.logger import log_request

router = APIRouter()


@router.post("/govern", response_model=GovernResponse)
def govern(request: GovernRequest):

    try:
        result = execute_governance(
            query=request.query,
            context=request.context,
            provider=request.provider.value,
        )

        # Logging (fail closed)
        log_request({
            "query": request.query,
            "provider": result["provider"],
            "model_used": result["model_used"],
            "estimated_cost": result["estimated_cost"],
            "actual_cost": result["actual_cost"],
            "confidence_score": result["confidence_score"],
            "refusal_flag": result["refusal"],
            "latency_ms": result["latency_ms"],
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
        })

        return GovernResponse(
            answer=result["answer"],
            refusal=result["refusal"],
            confidence_score=result["confidence_score"],
            model_used=result["model_used"],
            estimated_cost=result["estimated_cost"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            latency_ms=result["latency_ms"],
            provider=result["provider"],
        )

    except ValueError as e:
        error_type = str(e)

        raise HTTPException(
            status_code=400,
            detail={
                "error": "Governance execution failed",
                "error_type": error_type,
            },
        )

    except RuntimeError as e:
        if str(e) == "logging_failure":
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Logging failure — system integrity preserved",
                    "error_type": "internal_error",
                },
            )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "error_type": "internal_error",
            },
        )
