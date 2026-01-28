#!/data/data/com.termux/files/usr/bin/env python3
"""
Original username-based social discovery: checks public profile URL templates
for username existence. Only public pages are checked (no private API use).
"""
import httpx
import asyncio

PLATFORMS = {
    "GitHub": "https://github.com/{u}",
    "Twitter": "https://twitter.com/{u}",
    "Instagram": "https://www.instagram.com/{u}/",
    "Reddit": "https://www.reddit.com/user/{u}",
    "LinkedIn": "https://www.linkedin.com/in/{u}",
    "Facebook": "https://www.facebook.com/{u}",
    "YouTube": "https://www.youtube.com/{u}",
    "GitLab": "https://gitlab.com/{u}",
    "Medium": "https://medium.com/@{u}",
    "Tumblr": "https://{u}.tumblr.com",
}

DEFAULT_TIMEOUT = 8.0

async def _check_one(client: httpx.AsyncClient, url: str, platform: str):
    try:
        r = await client.get(url, follow_redirects=True, timeout=DEFAULT_TIMEOUT)
        status = r.status_code
        found = status in (200, 301, 302)
        return {"platform": platform, "url": url, "status": status, "found": found}
    except Exception as e:
        return {"platform": platform, "url": url, "status": None, "found": False, "error": str(e)}

async def discover_username_async(username: str, platforms: dict = PLATFORMS, concurrency: int = 6, use_tor: bool = False):
    headers = {"User-Agent": "Termux-OSINT-Manager/1.0 (+local)"}
    proxies = None
    if use_tor:
        proxies = {"all://": "socks5h://127.0.0.1:9050"}
    async with httpx.AsyncClient(headers=headers, proxies=proxies, verify=True) as client:
        sem = asyncio.Semaphore(concurrency)
        async def bound_check(pl, tpl):
            async with sem:
                url = tpl.format(u=username)
                return await _check_one(client, url, pl)
        tasks = [bound_check(pl, tpl) for pl, tpl in platforms.items()]
        return await asyncio.gather(*tasks)

def discover_username(username: str, use_tor: bool = False):
    import asyncio
    return asyncio.run(discover_username_async(username, use_tor=use_tor))