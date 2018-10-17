from mian.main import app

import os
import json
import logging.config

def setup_logging(
    default_path='logging.json',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

app.secret_key = 'Twilight Sparkle'
app.config['SESSION_TYPE'] = 'filesystem'
print("App Startup")
# app.run(debug=True, port=8080)
# app.run(host='0.0.0.0', debug=True, port=8080)
app.run(port=5001)

