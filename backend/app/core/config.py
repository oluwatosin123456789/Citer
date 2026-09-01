from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 1536

    database_url: str = "postgresql+psycopg://codeqa:codeqa@localhost:5432/codeqa"
    redis_url: str = "redis://localhost:6379/0"

    langchain_tracing_v2: bool = True
    langchain_api_key: str | None = None
    langchain_project: str = "codebase-qa"

    github_token: str | None = None
    data_dir: str = "data"

    top_k_retrieval: int = 20
    final_k: int = 8
    max_agent_iterations: int = 3


settings = Settings()