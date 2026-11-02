"""应用配置。

所有环境差异通过环境变量注入，密钥不入库、不入 Git（需求 §6）。
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "xuanwu-shop"
    app_env: str = "dev"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # 全程 PostgreSQL；连接串由 .env / 环境变量注入（无默认值，缺了直接启动失败）
    database_url: str

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    bcrypt_rounds: int = 12

    order_expire_job_enabled: bool = False
    order_expire_minutes: int = 30
    order_auto_confirm_days: int = 15

    # ---------- 智能客服（可选） ----------
    # 留空 api_key 时走内置规则引擎，流程照常可跑通；填了就走 OpenAI 兼容接口。
    support_llm_base_url: str = "https://api.deepseek.com/v1"
    support_llm_api_key: str = ""
    support_llm_model: str = "deepseek-chat"
    support_llm_temperature: float = 0.3
    support_llm_timeout: float = 30.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
