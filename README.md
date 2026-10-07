# Campus Customs

A class shop for looking through Yale hoodies, crewnecks, and t-shirts. This is not the official Yale Bulldog Blue store.

The shop assistant is four files in `backend/`: `prompts/prompt.md`, `agent.py`, `tools.py`, and `models.py`. `backend/main.py` is the FastAPI app the page talks to.

## Data pack

The database and product photos are not in this repo. Place them next to this README before you start the API:

```
data/campus_customs.db
data/products/
```

`data/products/` holds the jpg files named in the catalogue.

## Setup

From this folder, copy the env example and put your Portkey key in `.env`. Leave `MODEL_NAME` as `gpt-5.6-lunar` unless you need a different model.

```
cp .env.example .env
```

Install the Python packages:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install the frontend packages:

```
cd frontend
npm install
```

## Run

Start the API first. From `backend/`, with the virtualenv active:

```
uvicorn main:app --reload --port 8000
```

In a second terminal, from `frontend/`:

```
npm run dev
```

Open http://127.0.0.1:5173. The page sends `/api` and `/media` to the API on port 8000.
