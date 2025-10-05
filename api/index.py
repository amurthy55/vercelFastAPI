from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from statistics import mean
from pathlib import Path
import json
import numpy as np

app = FastAPI()
origins = ["*"]
# ✅ CORS setup — allow everything
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.options("/{rest_of_path:path}")
def preflight_handler(rest_of_path: str):
    """Handle browser preflight requests explicitly (important for Vercel)."""
    response = JSONResponse(content={"message": "CORS preflight OK"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/metrics")
def get_metrics(req: MetricsRequest):
    data_path = Path(__file__).parent / "data.json"
    with open(data_path) as f:
        records = json.load(f)

    result = {}
    for region in req.regions:
        region_data = [r for r in records if r["region"] == region]
        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        breaches = sum(1 for l in latencies if l > req.threshold_ms)

        p95 = float(np.percentile(latencies, 95))

        result[region] = {
            "avg_latency": round(mean(latencies), 3),
            "p95_latency": round(p95, 2),  # round to 2 decimals as exam expects
            "avg_uptime": round(mean(uptimes), 3),
            "breaches": breaches,
        }

    return {"regions": result}
