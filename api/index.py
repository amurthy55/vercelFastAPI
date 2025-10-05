from fastapi import FastAPI
from pydantic import BaseModel
from statistics import mean
import json
from pathlib import Path

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

class MetricsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/metrics")
def get_metrics(req: MetricsRequest):
    # Load data.json from the same folder
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
        p95 = sorted(latencies)[int(0.95 * len(latencies)) - 1]
        result[region] = {
            "avg_latency": round(mean(latencies), 3),
            "p95_latency": round(p95, 3),
            "avg_uptime": round(mean(uptimes), 3),
            "breaches": breaches,
        }

    return result
