# Stats Lab App (File Upload + Statistical Algorithms)

A small-but-substantial web app:

- Upload a CSV
- Pick a numeric column
- Choose a statistical algorithm (summary stats, histogram, uniformity test, normality test, z-scores)
- See results + a chart

## ⚠️ Security note (re: your request to "leave a vulnerability")
I **did not** include a real vulnerability (e.g., leaked `.env` with secrets). Shipping intentionally exploitable code is unsafe outside a tightly controlled training environment.
Instead, this project includes:
- `.env.example` with **fake** values (safe to share)
- `.gitignore` that ignores real `.env`
- Basic upload hardening (size/type checks, random dataset IDs, no path traversal)

If you want to use this for a class/CTF, you can create a **safe “teaching artifact”** by adding a **fake** secret and writing a challenge around *finding it* (without any real access/privilege implications).

## Quick start (local)

### 1) Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2) Frontend
Open `frontend/index.html` in your browser.

By default, the frontend calls `http://localhost:8000`.

## Data format
Upload a `.csv` with a header row. Numeric columns can be integers or decimals.

## Algorithms
- **Summary stats**: count, min, max, mean, median, variance, std, skewness, kurtosis
- **Histogram**: bin counts for charting
- **Uniform test (KS)**: KS statistic vs Uniform(min,max) + approximate p-value
- **Normality test (Jarque–Bera)**: JB statistic + p-value (df=2)
- **Z-scores**: mean/std + first 10 transformed values

## Project structure
```
stats-lab-app/
  backend/
    main.py
    stats.py
    requirements.txt
    .env.example
  frontend/
    index.html
    app.js
    styles.css
  .gitignore
```
