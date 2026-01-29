import requests

API = "https://graphql.anilist.co"

MEDIA_FIELDS = """
id
siteUrl
title { romaji english native }
description(asHtml: true)
averageScore
meanScore
popularity
favourites
status
format
chapters
volumes
season
seasonYear
startDate { year month day }
endDate { year month day }
genres
coverImage { large }
"""

def _post(query: str, variables: dict) -> dict:
    r = requests.post(API, json={"query": query, "variables": variables}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError(data["errors"][0].get("message") or "AniList error")
    return data["data"]

def trending(page: int = 1, per_page: int = 24) -> list[dict]:
    q = f"""
    query ($page:Int,$perPage:Int) {{
      Page(page:$page, perPage:$perPage) {{
        media(type:MANGA, sort:TRENDING_DESC) {{
          {MEDIA_FIELDS}
        }}
      }}
    }}
    """
    data = _post(q, {"page": page, "perPage": per_page})
    return (data.get("Page") or {}).get("media") or []

def search(query: str, page: int = 1, per_page: int = 24) -> list[dict]:
    q = f"""
    query ($search:String,$page:Int,$perPage:Int) {{
      Page(page:$page, perPage:$perPage) {{
        media(type:MANGA, search:$search, sort:SEARCH_MATCH) {{
          {MEDIA_FIELDS}
        }}
      }}
    }}
    """
    data = _post(q, {"search": query, "page": page, "perPage": per_page})
    return (data.get("Page") or {}).get("media") or []