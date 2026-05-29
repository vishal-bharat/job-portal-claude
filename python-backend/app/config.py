from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "career_connect"
    db_user: str = "postgres"
    db_password: str = "postgres"

    jwt_secret: str = "ThisIsADemoSecretKeyForGismaCareerConnectChangeInProduction1234567890"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"


settings = Settings()
