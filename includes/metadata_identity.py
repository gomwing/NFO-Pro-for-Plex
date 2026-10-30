"""Stable cache identity for Plex items whose optional slug is absent."""
import hashlib
import json


def ensure_metadata_slug(metadata):
    if metadata.get("slug"):
        return metadata
    identity = next((str(metadata[k]) for k in ("ratingKey", "key", "guid", "id") if metadata.get(k) is not None and str(metadata[k]) != ""), None)
    if identity is None:
        identity = json.dumps({k: metadata.get(k) for k in ("title", "year", "file", "locations")}, ensure_ascii=False, sort_keys=True)
    namespace = json.dumps([metadata.get("librarySectionID"), metadata.get("type"), identity], ensure_ascii=False)
    metadata["slug"] = "plex-" + hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:24]
    return metadata
