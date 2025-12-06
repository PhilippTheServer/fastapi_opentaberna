from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging



app = FastAPI(title="Dev API")


# Configure logging once at the entry point
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


origins = ["*"]  # Consider restricting this in a production environment

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Example router (you can replace this with your actual router)
# app.include_router(any_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
