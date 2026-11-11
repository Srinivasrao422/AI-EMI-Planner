# Render deployment

## Service

This repository is deployed as a Streamlit web service on Render.

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
- Health check: `/_stcore/health`
- Region: Singapore
- Persistent disk mount: `/var/data`
- SQLite database path: `/var/data/emi_planner.db`

## Required environment variable

Set `GROQ_API_KEY` in the Render service Environment page. Do not commit the key to GitHub or put it in `render.yaml`.

The SQLite database is directed to the persistent disk using `MSME_DATABASE_PATH`. The repository's existing local database is not copied to the public deployment automatically; the deployed app starts with a new database so local account data is not exposed unintentionally. Create a fresh demo account after deployment.

## Important notes

- The persistent disk requires a paid Render web-service plan. Review the Blueprint plan and current price before approving it.
- A persistent disk is mounted to one service instance and prevents horizontal scaling of this SQLite-backed app.
- Back up the database before any future migration or disk changes.
- The application provides decision-support calculations, not lender approval or audited financial advice.
