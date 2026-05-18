from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

ms_path = os.path.abspath("../data/Bologna_FrammentiManoscritti_BustaIX")

response = client.post(f"/manuscripts/init?manuscript_path={ms_path}")
print("Response:", response.status_code, response.json())

output_dir = os.path.join(ms_path, "OUTPUT")
print("OUTPUT directory exists:", os.path.isdir(output_dir))
