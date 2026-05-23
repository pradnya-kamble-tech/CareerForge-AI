import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

ROUTES = [
    "/",
    "/student",
    "/recruiter",
    "/admin",
    "/register",
    "/login",
    "/explore-roles",
    "/api/status",
    "/api/demo-data",
    "/api/all-skills",
]

def audit():
    print(f"Auditing routes at {BASE_URL}...")
    for route in ROUTES:
        try:
            r = requests.get(BASE_URL + route, timeout=5)
            print(f"[{r.status_code}] {route}")
        except Exception as e:
            print(f"[ERROR] {route}: {e}")

if __name__ == "__main__":
    audit()
