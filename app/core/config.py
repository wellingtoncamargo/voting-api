from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Arckwell Voting API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    MONGODB_URL: str = "mongodb://mongo:27017"
    MONGODB_DB_NAME: str = "arckwell_voting"

    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # Validação de CPF
    VOTER_VALIDATION_URL: str = "https://user-info.herokuapp.com"
    # False = apenas validação matemática local (padrão recomendado)
    # True  = valida localmente E consulta API externa (fail-open em falha de rede)
    VOTER_VALIDATION_ENABLED: bool = False

    SESSION_CLOSE_INTERVAL_SECONDS: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
