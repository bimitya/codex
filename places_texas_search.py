#!/usr/bin/env python3
"""
Google Places search across Texas for prefab/modular/manufactured home builders.

Outputs a CSV with: business name, Place ID, website URL, phone, full address,
average rating, rating count.

Usage:
  python places_texas_search.py --api-key YOUR_KEY --out results.csv

You can also set environment variable GOOGLE_MAPS_API_KEY.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests


# --- Configuration ---
TEXAS_BOUNDS: Tuple[float, float, float, float] = (
    25.8371,  # min latitude
    -106.6456,  # min longitude
    36.5007,  # max latitude
    -93.5080,  # max longitude
)

DEFAULT_KEYWORDS: List[str] = [
    "prefab home builder",
    "prefabricated home builder",
    "modular home builder",
    "manufactured home builder",
]

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


@dataclass
class PlaceRecord:
    name: str
    place_id: str
    website: str
    phone: str
    address: str
    rating: Optional[float]
    rating_count: Optional[int]


def generate_texas_grid(step_degrees: float) -> Iterable[Tuple[float, float]]:
    min_lat, min_lng, max_lat, max_lng = TEXAS_BOUNDS
    lat = min_lat
    while lat <= max_lat + 1e-9:
        lng = min_lng
        while lng <= max_lng + 1e-9:
            yield (lat, lng)
            lng += step_degrees
        lat += step_degrees


def request_with_backoff(url: str, params: Dict[str, str], max_retries: int = 5) -> Dict:
    """Make a GET request with exponential backoff for rate limiting errors."""
    delay_seconds = 1.0
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            # Retry on transient HTTP errors
            time.sleep(delay_seconds)
            delay_seconds = min(delay_seconds * 2.0, 16.0)
            continue
        data = response.json()
        status = data.get("status")
        if status in {"OK", "ZERO_RESULTS"}:
            return data
        if status in {"OVER_QUERY_LIMIT", "RESOURCE_EXHAUSTED"}:
            time.sleep(delay_seconds)
            delay_seconds = min(delay_seconds * 2.0, 32.0)
            continue
        if status in {"INVALID_REQUEST"} and data.get("error_message", "").lower().find("page token") != -1:
            # next_page_token not ready; wait per API docs
            time.sleep(2.0)
            continue
        # For other statuses, return as-is to avoid infinite loops
        return data
    return {"status": "ERROR", "error_message": "Max retries exceeded"}


def text_search_all_pages(api_key: str, query: str, location: Tuple[float, float], radius_m: int, max_pages: int = 3) -> List[Dict]:
    lat, lng = location
    params: Dict[str, str] = {
        "key": api_key,
        "query": query,
        "location": f"{lat},{lng}",
        "radius": str(radius_m),
    }
    results: List[Dict] = []

    next_page_token: Optional[str] = None
    page = 0
    while page < max_pages:
        if next_page_token:
            p = dict(params)
            p["pagetoken"] = next_page_token
            # Per API, must wait a short period for token activation
            time.sleep(2.0)
            data = request_with_backoff(TEXT_SEARCH_URL, p)
        else:
            data = request_with_backoff(TEXT_SEARCH_URL, params)

        if data.get("status") not in {"OK", "ZERO_RESULTS"}:
            # Print and break; avoid hard failure
            sys.stderr.write(f"Text Search error for '{query}' at {location}: {data}\n")
            break

        results.extend(data.get("results", []))
        next_page_token = data.get("next_page_token")
        page += 1
        if not next_page_token:
            break

    return results


def is_texas_place(details: Dict) -> bool:
    components = details.get("result", {}).get("address_components", [])
    for comp in components:
        if "administrative_area_level_1" in comp.get("types", []):
            if comp.get("short_name") == "TX" or comp.get("long_name") == "Texas":
                return True
    # Fallback: formatted_address contains TX
    formatted = details.get("result", {}).get("formatted_address", "")
    return ", TX " in formatted or formatted.endswith(", TX") or formatted.endswith(", Texas")


def fetch_place_details(api_key: str, place_id: str) -> Optional[Dict]:
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "place_id,name,formatted_address,website,formatted_phone_number,rating,user_ratings_total,address_components",
    }
    data = request_with_backoff(DETAILS_URL, params)
    if data.get("status") == "OK":
        return data
    # Log and skip on error
    sys.stderr.write(f"Details error for {place_id}: {data}\n")
    return None


def collect_place_records(api_key: str, keywords: List[str], grid_step: float, radius_m: int, max_pages: int) -> List[PlaceRecord]:
    # First pass: discover unique Place IDs via Text Search across grid
    discovered_place_ids: Set[str] = set()

    for keyword in keywords:
        for lat, lng in generate_texas_grid(grid_step):
            results = text_search_all_pages(api_key, keyword, (lat, lng), radius_m, max_pages=max_pages)
            for item in results:
                pid = item.get("place_id")
                if pid:
                    discovered_place_ids.add(pid)

    # Second pass: details and TX filtering
    records: List[PlaceRecord] = []
    for pid in discovered_place_ids:
        details = fetch_place_details(api_key, pid)
        if not details:
            continue
        if not is_texas_place(details):
            continue
        result = details.get("result", {})
        record = PlaceRecord(
            name=result.get("name", ""),
            place_id=result.get("place_id", ""),
            website=result.get("website", ""),
            phone=result.get("formatted_phone_number", ""),
            address=result.get("formatted_address", ""),
            rating=result.get("rating"),
            rating_count=result.get("user_ratings_total"),
        )
        records.append(record)
    return records


def write_csv(path: str, records: List[PlaceRecord]) -> None:
    fieldnames = [
        "business name",
        "Place ID",
        "website URL",
        "phone",
        "full address",
        "average rating",
        "rating count",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "business name": r.name,
                    "Place ID": r.place_id,
                    "website URL": r.website,
                    "phone": r.phone,
                    "full address": r.address,
                    "average rating": r.rating if r.rating is not None else "",
                    "rating count": r.rating_count if r.rating_count is not None else "",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search Google Places across Texas for prefab/modular/manufactured home builders and export CSV.")
    parser.add_argument("--api-key", dest="api_key", default=os.getenv("GOOGLE_MAPS_API_KEY"), help="Google Maps API key (or set GOOGLE_MAPS_API_KEY)")
    parser.add_argument("--out", dest="out_csv", required=True, help="Output CSV file path")
    parser.add_argument("--grid-step", dest="grid_step", type=float, default=1.0, help="Grid step size in degrees (default: 1.0)")
    parser.add_argument("--radius", dest="radius", type=int, default=50000, help="Search radius in meters for each grid point (default: 50000; API max 50000)")
    parser.add_argument("--max-pages", dest="max_pages", type=int, default=3, help="Maximum pages per Text Search (max 3)")
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=DEFAULT_KEYWORDS,
        help="Override keywords list. Default includes prefab/modular/manufactured home builder variants.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        sys.stderr.write("Missing API key. Provide --api-key or set GOOGLE_MAPS_API_KEY.\n")
        sys.exit(2)

    print(f"Keywords: {args.keywords}")
    print(f"Grid step: {args.grid_step}°, radius: {args.radius} m, pages/query: {args.max_pages}")
    print("Discovering places across Texas... This may take a while and consume quota.")

    records = collect_place_records(
        api_key=args.api_key,
        keywords=args.keywords,
        grid_step=args.grid_step,
        radius_m=args.radius,
        max_pages=args.max_pages,
    )

    # Deduplicate again defensively by Place ID
    seen: Set[str] = set()
    unique_records: List[PlaceRecord] = []
    for r in records:
        if r.place_id in seen:
            continue
        seen.add(r.place_id)
        unique_records.append(r)

    write_csv(args.out_csv, unique_records)
    print(f"Wrote {len(unique_records)} records to {args.out_csv}")


if __name__ == "__main__":
    main()

