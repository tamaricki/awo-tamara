import requests
import json
import time
from pathlib import Path
from typing import Dict, Any

# Simplified cache handling
def load_cache(cache_path: Path) -> Dict[str, Any]:
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_cache(cache: Dict[str, Any], cache_path: Path) -> None:
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

# Simplified Overpass provider
class OverpassProvider:
    def __init__(self, base_url: str, rate_limit: int):
        self.base_url = base_url
        self.rate_limit = rate_limit
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        wait = max(0.0, 1.0 / self.rate_limit - elapsed)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()

    def search(self, query: str) -> Any:
        self._throttle()
        overpass_query = f"[out:json];node[\"name\"=\"{query}\"](50.0,8.0,52.0,14.0);out;"
        response = requests.get(self.base_url, params={"data": overpass_query}, timeout=30)
        if response.status_code == 200:
            return response.json()
        return []

# Main function
def main() -> None:
    # Configuration
    base_url = "https://overpass-api.de/api/interpreter"
    rate_limit = 1  # 1 request per second
    cache_path = Path("cache_results_overpass.json")

    # Load cache
    cache = load_cache(cache_path)

    # Initialize provider
    provider = OverpassProvider(base_url, rate_limit)

    # Example input data
    entities = ["AWO Berlin", "AWO Hamburg"]

    # Resolve entities
    results = []
    for entity in entities:
        if entity in cache:
            print(f"Cache hit for: {entity}")
            results.append(cache[entity])
            continue

        print(f"Resolving: {entity}")
        result = provider.search(entity)
        if result:
            cache[entity] = result  # Cache the result
            results.append(result)
        else:
            cache[entity] = None
            results.append(None)

    # Save cache
    save_cache(cache, cache_path)

    # Print results
    for entity, result in zip(entities, results):
        print(f"Entity: {entity}, Result: {result}")

if __name__ == "__main__":
    main()