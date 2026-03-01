from __future__ import annotations

import os
import io
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from stats import summary, histogram, ks_test_uniform, jarque_bera, z_scores


APP_NAME = os.getenv("APP_NAME", "Stats Lab App")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
ALLOWED_EXTS = set(x.strip().lower() for x in os.getenv("ALLOWED_EXTS", "csv").split(",") if x.strip())

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=APP_NAME)

# Frontend is usually opened from file://, so we allow localhost access for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:5500", "http://127.0.0.1:5500", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UploadResponse(BaseModel):
    dataset_id: str
    columns: List[str]


class AnalyzeRequest(BaseModel):
    dataset_id: str
    column: str
    algorithm: str  # summary | histogram | uniform_ks | normal_jb | zscores
    bins: Optional[int] = 12


class AnalyzeResponse(BaseModel):
    dataset_id: str
    column: str
    algorithm: str
    result: Dict[str, Any]


def _safe_ext(filename: str) -> str:
    parts = filename.rsplit(".", 1)
    return parts[-1].lower() if len(parts) == 2 else ""


def _enforce_size(contents: bytes) -> None:
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_UPLOAD_MB} MB.")


def _load_csv_bytes(contents: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")


def _dataset_path(dataset_id: str) -> Path:
    # Only allow UUID-like IDs
    try:
        uuid.UUID(dataset_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid dataset id.")
    return UPLOAD_DIR / f"{dataset_id}.parquet"


def _save_dataset(df: pd.DataFrame) -> str:
    dataset_id = str(uuid.uuid4())
    path = _dataset_path(dataset_id)
    df.to_parquet(path, index=False)
    return dataset_id


def _read_dataset(dataset_id: str) -> pd.DataFrame:
    path = _dataset_path(dataset_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return pd.read_parquet(path)


def _numeric_series(df: pd.DataFrame, column: str) -> List[float]:
    if column not in df.columns:
        raise HTTPException(status_code=400, detail="Column not found.")
    ser = pd.to_numeric(df[column], errors="coerce").dropna()
    if ser.empty:
        raise HTTPException(status_code=400, detail="No numeric values in that column.")
    return [float(x) for x in ser.tolist()]


@app.get("/health")
def health():
    return {"ok": True, "app": APP_NAME}


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    ext = _safe_ext(file.filename or "")
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Only {', '.join(sorted(ALLOWED_EXTS))} files allowed.")

    contents = await file.read()
    _enforce_size(contents)
    df = _load_csv_bytes(contents)

    if df.shape[1] == 0:
        raise HTTPException(status_code=400, detail="CSV has no columns.")
    # Keep columns simple
    df.columns = [str(c)[:80] for c in df.columns]

    dataset_id = _save_dataset(df)
    return UploadResponse(dataset_id=dataset_id, columns=[str(c) for c in df.columns])


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    df = _read_dataset(req.dataset_id)
    xs = _numeric_series(df, req.column)

    algo = req.algorithm.lower().strip()
    if algo == "summary":
        out = summary(xs)
    elif algo == "histogram":
        out = histogram(xs, bins=req.bins or 12)
    elif algo == "uniform_ks":
        out = ks_test_uniform(xs)
    elif algo == "normal_jb":
        out = jarque_bera(xs)
    elif algo == "zscores":
        out = z_scores(xs)
    else:
        raise HTTPException(status_code=400, detail="Unknown algorithm.")

    return AnalyzeResponse(dataset_id=req.dataset_id, column=req.column, algorithm=algo, result=out)
