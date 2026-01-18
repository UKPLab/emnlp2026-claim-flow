import os
import httpx
from dotenv import load_dotenv
load_dotenv()

r = httpx.get(
    "https://api.semanticscholar.org/graph/v1/paper/ACL:P17-1111",
    params={"fields": "title"},
    headers={"x-api-key": os.environ["S2_API_KEY"]},
    timeout=10.0,
)
print(r.status_code, r.text[:200])
