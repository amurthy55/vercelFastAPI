from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json, os
from pathlib import Path
import numpy as np

app = FastAPI()

# Enable CORS for any origin (all POSTs allowed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_methods=["POST"],  # allow POST requests
    allow_headers=["*"],
)

# Load JSON data from file once at startup
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
with open(DATA_FILE, "r") as f:
    records = json.load(f)

@app.get("/")
def read_root():
    return {"Hello": "Hi"}

@app.post("/metrics")
async def get_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    response = {}

    for region in regions:
        region_data = [r for r in records if r["region"] == region]

        if not region_data:
            response[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        breaches = sum(1 for l in latencies if l > threshold)

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))

        response[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return response
