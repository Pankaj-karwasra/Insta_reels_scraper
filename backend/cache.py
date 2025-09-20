from cachetools import TTLCache
import os


TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))
# small cache; key by username
cache = TTLCache(maxsize=256, ttl=TTL)


def get_cached(username: str):
    return cache.get(username)


def set_cached(username: str, data):
    cache[username] = data