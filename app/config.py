import os

import dotenv

dotenv.load_dotenv()


class Config:
    __instance = None

    # Ensure only one instance of Config is created
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        # Load or set your configuration data here
        self.SECRET_KEY = os.getenv("SPECTACLES_SECRET_KEY")
        self.ALGORITHM = os.getenv("SPECTACLES_ALGORITHM")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 90


config_values = Config()

if not config_values.SECRET_KEY or not config_values.ALGORITHM:
    raise ValueError(
        "SPECTACLES_SECRET_KEY and SPECTACLES_ALGORITHM must be set as environmental variables"
    )
