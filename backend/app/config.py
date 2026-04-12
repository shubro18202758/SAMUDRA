from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    frontend_port: int = 3000
    backend_port: int = 8000
    ws_tick_rate_ms: int = 250  # 4 telemetry frames/sec (250 ms interval)

    class Config:
        env_prefix = "SAMUDRA_"


settings = Settings()
