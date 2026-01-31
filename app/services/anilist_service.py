import requests

API = "https://graphql.anilist.co"

MEDIA_FIELDS = """
id
siteUrl
isAdult
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
tags { name isAdult }
"""

def _post(query, variables=None):
    resp = requests.post(API, json={"query": query, "variables": variables or {}}, timeout=10)
    resp.raise_for_status()
    return resp.json().get("data", {})

def trending(page=1, per_page=50):
    q = f"""
    query ($page:Int,$perPage:Int) {{ 
      Page(page:$page, perPage:$perPage) {{ 
        media(
          type:MANGA,
          sort:TRENDING_DESC,
          isAdult:false,
          genre_not_in:["Hentai"]
        ) {{ 
          {MEDIA_FIELDS}
        }} 
      }} 
    }} 
    """
    data = _post(q, {"page": page, "perPage": per_page})
    return (data.get("Page") or {}).get("media") or []

def search(query, page=1, per_page=50):
    q = f"""
    query ($search:String,$page:Int,$perPage:Int) {{ 
      Page(page:$page, perPage:$perPage) {{ 
        media(
          type:MANGA,
          search:$search,
          sort:SEARCH_MATCH,
          isAdult:false,
          genre_not_in:["Hentai"]
        ) {{ 
          {MEDIA_FIELDS}
        }} 
      }} 
    }} 
    """
    data = _post(q, {"search": query, "page": page, "perPage": per_page})
    return (data.get("Page") or {}).get("media") or []
