# import json
# import re
# from typing import Optional, Tuple
# from urllib.parse import urljoin, urlparse

# import requests

import pandas as pd


# def scrape_bestbuy_rating(url: str, timeout: int = 20) -> Tuple[int, int, float]:
#     """
#     Scrape BestBuy rating info from a product page or reviews page.

#     Args:
#         url: BestBuy product or reviews URL.
#         timeout: Request timeout (seconds).

#     Returns:
#         (review_count, rating_count, rating)
#             review_count: total reviews (int)
#             rating_count: total ratings (int) (BestBuy often equates this to reviews)
#             rating: average rating (float)

#     Raises:
#         ValueError: if the URL is not bestbuy.com or if rating data can't be extracted.
#         requests.RequestException: on network issues.
#     """

#     def _get_html(u: str) -> str:
#         headers = {
#             # A realistic UA reduces the chance of basic bot blocks.
#             "User-Agent": (
#                 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                 "AppleWebKit/537.36 (KHTML, like Gecko) "
#                 "Chrome/121.0.0.0 Safari/537.36"
#             ),
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#             "Accept-Language": "en-US,en;q=0.9",
#             "Connection": "keep-alive",
#         }
#         resp = requests.get(u, headers=headers, timeout=timeout)
#         resp.raise_for_status()
#         return resp.text

#     def _parse_int(s: str) -> int:
#         return int(s.replace(",", "").strip())

#     def _extract_from_jsonld(html: str) -> Optional[Tuple[int, int, float]]:
#         # Find all JSON-LD blocks and look for Product -> aggregateRating
#         scripts = re.findall(
#             r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
#             html,
#             flags=re.DOTALL | re.IGNORECASE,
#         )
#         for block in scripts:
#             block = block.strip()
#             if not block:
#                 continue
#             try:
#                 data = json.loads(block)
#             except json.JSONDecodeError:
#                 continue

#             # JSON-LD may be dict or list
#             candidates = data if isinstance(data, list) else [data]
#             for obj in candidates:
#                 if not isinstance(obj, dict):
#                     continue

#                 # Sometimes it's an @graph container
#                 graph = obj.get("@graph")
#                 if isinstance(graph, list):
#                     candidates2 = [x for x in graph if isinstance(x, dict)]
#                 else:
#                     candidates2 = [obj]

#                 for item in candidates2:
#                     agg = item.get("aggregateRating")
#                     if not isinstance(agg, dict):
#                         continue

#                     rating_value = agg.get("ratingValue")
#                     review_count = agg.get("reviewCount")
#                     rating_count = agg.get("ratingCount")  # may be missing

#                     if rating_value is None or (review_count is None and rating_count is None):
#                         continue

#                     rating = float(str(rating_value).strip())
#                     if review_count is None:
#                         review_count = rating_count
#                     if rating_count is None:
#                         rating_count = review_count

#                     return int(review_count), int(rating_count), rating
#         return None

#     def _extract_from_text(html: str) -> Optional[Tuple[int, int, float]]:
#         # Pattern A: "User rating, 4.7 out of 5 stars with 1506 reviews."
#         m = re.search(
#             r"User\s+rating,\s*([0-9](?:\.[0-9])?)\s+out\s+of\s+5\s+stars\s+with\s+([\d,]+)\s+reviews?",
#             html,
#             flags=re.IGNORECASE,
#         )
#         if m:
#             rating = float(m.group(1))
#             reviews = _parse_int(m.group(2))
#             return reviews, reviews, rating

#         # Pattern B: "4.7 (1,506 Reviews)" or "4.8(36 reviews)"
#         m = re.search(
#             r"\b([0-9](?:\.[0-9])?)\s*\(\s*([\d,]+)\s*(?:customer\s+)?reviews?\s*\)",
#             html,
#             flags=re.IGNORECASE,
#         )
#         if m:
#             rating = float(m.group(1))
#             reviews = _parse_int(m.group(2))
#             return reviews, reviews, rating

#         # Pattern C: sometimes appears as "Rating 4.7 out of 5 stars with 1506 reviews"
#         m = re.search(
#             r"Rating\s*([0-9](?:\.[0-9])?)\s*out\s+of\s+5\s+stars\s+with\s+([\d,]+)\s+reviews?",
#             html,
#             flags=re.IGNORECASE,
#         )
#         if m:
#             rating = float(m.group(1))
#             reviews = _parse_int(m.group(2))
#             return reviews, reviews, rating

#         return None

#     def _find_reviews_link(base_url: str, html: str) -> Optional[str]:
#         # Find first /site/reviews/... link
#         m = re.search(r'href=["\']([^"\']*/site/reviews/[^"\']+)["\']', html, flags=re.IGNORECASE)
#         if m:
#             return urljoin(base_url, m.group(1))

#         # Sometimes links show up in plain text/JS
#         m = re.search(r"(https?://www\.bestbuy\.com/site/reviews/[^\s\"']+)", html, flags=re.IGNORECASE)
#         if m:
#             return m.group(1)

#         m = re.search(r"(/site/reviews/[^\s\"']+)", html, flags=re.IGNORECASE)
#         if m:
#             return urljoin(base_url, m.group(1))

#         return None

#     # Basic domain validation
#     parsed = urlparse(url)
#     if "bestbuy.com" not in (parsed.netloc or "").lower():
#         raise ValueError("This function only supports bestbuy.com URLs.")

#     # Try the given page first
#     html = _get_html(url)

#     for extractor in (_extract_from_jsonld, _extract_from_text):
#         got = extractor(html)
#         if got:
#             return got

#     # If not found, try hopping to the reviews page (if linked)
#     reviews_url = _find_reviews_link(url, html)
#     if reviews_url and reviews_url != url:
#         html2 = _get_html(reviews_url)
#         for extractor in (_extract_from_jsonld, _extract_from_text):
#             got = extractor(html2)
#             if got:
#                 return got

#     raise ValueError("Could not extract rating/review counts from the provided BestBuy URL.")

import json
import random
import re
import time
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def scrape_bestbuy_rating(link: str, timeout: int = 20, debug_dump_path: Optional[str] = None) -> Tuple[int, int, float]:
    """
    BestBuy: take a product/reviews URL, return (review_count, rating_count, rating).

    Strategy:
      - Call BestBuy UGC reviews endpoint for sku
      - Extract (avg rating, counts) from:
          1) direct stats keys (when present)
          2) rating histogram/breakdown (compute weighted average)
          3) totalResults (review count) as fallback

    If extraction fails and debug_dump_path is provided, dumps JSON for inspection.

    Returns:
        (review_count:int, rating_count:int, rating:float)

    Raises:
        ValueError on extraction failure.
        requests.RequestException on network errors.
    """

    def extract_sku(url: str) -> Optional[str]:
        m = re.search(r"[?&]skuId=(\d+)", url, re.IGNORECASE)
        if m:
            return m.group(1)

        m = re.search(r"/(\d+)\.p(?:[/?]|$)", url, re.IGNORECASE)
        if m:
            return m.group(1)

        m = re.search(r"/site/reviews/[^/]+/(\d+)(?:[/?]|$)", url, re.IGNORECASE)
        if m:
            return m.group(1)

        m = re.search(r"\b(\d{6,10})\b", url)
        return m.group(1) if m else None

    def to_int(x: Any) -> Optional[int]:
        try:
            if x is None or isinstance(x, bool):
                return None
            if isinstance(x, (int, float)):
                return int(x)
            s = str(x).strip().replace(",", "")
            return int(float(s))
        except Exception:
            return None

    def to_float(x: Any) -> Optional[float]:
        try:
            if x is None or isinstance(x, bool):
                return None
            if isinstance(x, (int, float)):
                return float(x)
            return float(str(x).strip())
        except Exception:
            return None

    def walk(obj: Any) -> Iterable[Any]:
        if isinstance(obj, dict):
            yield obj
            for v in obj.values():
                yield from walk(v)
        elif isinstance(obj, list):
            for it in obj:
                yield from walk(it)

    def find_first_number(d: Dict[str, Any], keys: Tuple[str, ...], kind: str) -> Optional[float]:
        """
        Find first numeric value for any key in keys (case-sensitive), optionally nested dict.
        kind: "int" or "float"
        """
        for k in keys:
            if k in d:
                v = d.get(k)
                return to_int(v) if kind == "int" else to_float(v)
        return None

    def try_direct_stats(data: Dict[str, Any]) -> Optional[Tuple[int, int, float]]:
        # Common-ish names across different payload shapes
        rating_keys = (
            "averageRating", "avgRating", "averageOverallRating", "avgOverallRating",
            "overallRating", "ratingValue", "rating"
        )
        review_count_keys = (
            "reviewCount", "totalReviewCount", "totalReviews", "reviewsCount", "total_results", "totalResults"
        )
        rating_count_keys = (
            "ratingCount", "totalRatingCount", "totalRatings", "ratingsCount"
        )

        best: Optional[Tuple[int, int, float, int]] = None  # (reviews, ratings, avg, score)

        for node in walk(data):
            if not isinstance(node, dict):
                continue

            avg = find_first_number(node, rating_keys, "float")
            if avg is None or not (0.0 <= avg <= 5.0):
                continue

            rc = find_first_number(node, review_count_keys, "int")
            rtec = find_first_number(node, rating_count_keys, "int")

            # Accept if we have at least one count
            if rc is None and rtec is None:
                continue

            if rc is None:
                rc = rtec
            if rtec is None:
                rtec = rc

            # Score candidates: prefer bigger counts + presence of both counts
            score = 0
            if rc is not None:
                score += min(rc, 1_000_000)
            if rtec is not None:
                score += min(rtec, 1_000_000)
            if (rc is not None) and (rtec is not None):
                score += 10_000

            cand = (int(rc), int(rtec), float(avg), score)
            if best is None or cand[3] > best[3]:
                best = cand

        if best:
            return best[0], best[1], best[2]
        return None

    def try_histogram(data: Dict[str, Any]) -> Optional[Tuple[int, int, float]]:
        """
        Look for rating distributions like:
          ratingHistogram: [{"rating":5,"count":123}, ...]
          ratingBreakdown: [{"value":5,"count":...}, ...]
          distribution: [{"star":5,"count":...}, ...]
        Compute weighted average + total count.
        """
        histogram_keys = ("ratingHistogram", "ratingBreakdown", "ratingDistribution", "histogram", "distribution")

        def parse_bins(bins: Any) -> Optional[Tuple[int, float]]:
            if not isinstance(bins, list) or len(bins) == 0:
                return None

            total = 0
            weighted = 0.0

            for b in bins:
                if not isinstance(b, dict):
                    continue

                # star value key variants
                star = (
                    to_int(b.get("rating")) or
                    to_int(b.get("value")) or
                    to_int(b.get("star")) or
                    to_int(b.get("stars"))
                )
                cnt = (
                    to_int(b.get("count")) or
                    to_int(b.get("total")) or
                    to_int(b.get("n"))
                )
                if star is None or cnt is None:
                    continue
                if not (1 <= star <= 5) or cnt < 0:
                    continue

                total += cnt
                weighted += star * cnt

            if total <= 0:
                return None
            return total, (weighted / total)

        best: Optional[Tuple[int, float]] = None
        for node in walk(data):
            if not isinstance(node, dict):
                continue
            for hk in histogram_keys:
                if hk in node:
                    parsed = parse_bins(node.get(hk))
                    if parsed:
                        # pick the one with biggest total
                        if best is None or parsed[0] > best[0]:
                            best = parsed

        if best:
            rating_count = best[0]
            rating = float(best[1])
            # histogram count typically reflects ratings/reviews volume
            return rating_count, rating_count, rating

        return None

    # Domain check
    netloc = (urlparse(link).netloc or "").lower()
    if "bestbuy.com" not in netloc:
        raise ValueError("This function only supports bestbuy.com URLs.")

    sku = extract_sku(link)
    if not sku:
        raise ValueError("Could not extract skuId from the given BestBuy link.")

    # UGC endpoint (minimal payload pageSize=1)
    api_url = f"https://www.bestbuy.com/ugc/v2/reviews?page=1&pageSize=1&sku={sku}&sort=MOST_RECENT&variant=A"

    retry = Retry(
        total=6,
        connect=6,
        read=6,
        backoff_factor=0.7,
        status_forcelist=(403, 408, 429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": random.choice(user_agents),
        "referer": link,
        "origin": "https://www.bestbuy.com",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "x-client-id": "ratings-and-reviews-user-generated-content-ratings-and-reviews-v1",
    }

    last_err: Optional[Exception] = None
    data: Optional[Dict[str, Any]] = None

    for attempt in range(1, 5):
        try:
            if attempt > 1:
                time.sleep(0.6 * attempt + random.uniform(0.0, 0.4))

            resp = session.get(api_url, headers=headers, timeout=timeout)
            resp.raise_for_status()

            # Try JSON parsing even if content-type is off
            data = resp.json()
            if not isinstance(data, dict):
                raise ValueError("Unexpected JSON response shape (not a dict).")
            break

        except (requests.RequestException, ValueError) as e:
            last_err = e
            continue

    if data is None:
        raise ValueError(f"Failed to fetch BestBuy UGC JSON. Last error: {last_err}")

    # 1) direct stats
    got = try_direct_stats(data)
    if got:
        return got

    # 2) histogram-based
    got2 = try_histogram(data)
    if got2:
        # If UGC has totalResults, use it as review_count (often pagination total)
        total_results = None
        if isinstance(data.get("totalResults"), (int, float, str)):
            total_results = to_int(data.get("totalResults"))
        review_count, rating_count, rating = got2
        if total_results is not None and total_results >= 0:
            review_count = total_results
            rating_count = max(rating_count, total_results)
        return review_count, rating_count, rating

    # Optional debug dump so you can see exactly what keys exist
    if debug_dump_path:
        try:
            with open(debug_dump_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    raise ValueError(
        "Could not locate rating/review stats in the BestBuy UGC JSON payload. "
        "If you pass debug_dump_path='bb_ugc.json', it will dump the payload for inspection."
    )






# Read input
df = pd.read_csv("./scraping_script/BestBuy_SampleInput_For_Automation - Sheet1.csv")

rows = []
for index, row in df.iterrows():
    url = str(row["Link"]).strip()

    try:
        review_count, rating_count, rating = scrape_bestbuy_rating(url)
        print(url, review_count, rating_count, rating)
        rows.append({
            "Link": url,
            "Review Count": review_count,
            "Rating Count": rating_count,
            "Rating": rating
        })
    except Exception as e:
        # Keep the row, but mark as failed
        print(f"FAILED: {url} -> {e}")
        rows.append({
            "Link": url,
            "Review Count": None,
            "Rating Count": None,
            "Rating": None,
            "Error": str(e)
        })

output_df = pd.DataFrame(rows)

# Write to a NEW output file (recommended)
output_df.to_csv("./scraping_script/BestBuy_Output_2.csv", index=False)

