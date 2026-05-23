import requests

routes = [
    "http://127.0.0.1:5000/",
    "http://127.0.0.1:5000/login",
    "http://127.0.0.1:5000/register",
    "http://127.0.0.1:5000/student?demo=1"
]

def check_routes():
    success = True
    for route in routes:
        try:
            print(f"Checking {route}...")
            r = requests.get(route, timeout=10)
            if r.status_code != 200:
                print(f"FAIL: {route} returned status {r.status_code}")
                success = False
                continue
            
            # Check for Jinja/Python errors in HTML
            content = r.text.lower()
            error_keywords = ["typeerror", "undefinederror", "internal server error", "jinja2", "traceback"]
            found_errors = [k for k in error_keywords if k in content]
            
            if found_errors:
                print(f"FAIL: {route} contains error keywords: {found_errors}")
                # Print a snippet of the error
                idx = content.find(found_errors[0])
                print(f"Snippet: {r.text[idx-50:idx+200]}")
                success = False
            else:
                print(f"SUCCESS: {route} rendered correctly.")
        except Exception as e:
            print(f"ERROR: Could not connect to {route}: {e}")
            success = False
    
    if success:
        print("\nALL ROUTES PASSED VERIFICATION.")
    else:
        print("\nVERIFICATION FAILED.")

if __name__ == "__main__":
    check_routes()
