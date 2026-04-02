from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import uvicorn
from ml_model import predictor
from database import db
from datetime import datetime

app = FastAPI(title="QueryGuard API", version="2.0.0")


class PredictRequest(BaseModel):
    query: str
    bytes_estimate_mb: Optional[int] = 10
    save_history: Optional[bool] = True


class PredictResponse(BaseModel):
    estimated_cost: float
    currency: str = "USD"
    bytes_estimate_mb: int
    timestamp: str
    request_id: str


def verify_api_key(api_key: str = Header(...)):
    user = db.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user


@app.get("/")
def root():
    return {"message": "QueryGuard API", "version": "2.0.0"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, user: dict = Depends(verify_api_key)):
    # Predict cost
    bytes_scanned = request.bytes_estimate_mb * 1024 * 1024
    cost = predictor.predict(request.query, bytes_scanned)

    # Save to history
    if request.save_history:
        db.save_query_history(
            user['id'],
            request.query,
            cost,
            status='api'
        )

    return PredictResponse(
        estimated_cost=cost,
        bytes_estimate_mb=request.bytes_estimate_mb,
        timestamp=datetime.now().isoformat(),
        request_id=f"req_{user['id']}_{int(datetime.now().timestamp())}"
    )


@app.get("/history")
def get_history(limit: int = 50, user: dict = Depends(verify_api_key)):
    history = db.get_user_history(user['id'], limit)
    return history.to_dict(orient='records')


@app.get("/stats")
def get_stats(user: dict = Depends(verify_api_key)):
    history = db.get_user_history(user['id'], limit=1000)
    return {
        "total_queries": len(history),
        "total_cost": float(history['predicted_cost'].sum()) if len(history) > 0 else 0,
        "avg_cost": float(history['predicted_cost'].mean()) if len(history) > 0 else 0,
        "max_cost": float(history['predicted_cost'].max()) if len(history) > 0 else 0
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)