import csv
import json
import os
import re
import sys

import requests

API_BASE = "https://www.googleapis.com/youtube/v3"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlist_sorter_config.json")

H0m3_Pa9e = "P L 4 Y L 1 S T   S 0 R T 3 R"


def clr():
    os.system("cls" if os.name == "nt" else "clear")


def get_api_key() -> str:
    # Env var takes priority so you can override without touching the config file
    env_key = os.environ.get("YOUTUBE_API_KEY")
    if env_key:
        return env_key

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f).get("api_key")
                if saved:
                    return saved
        except (json.JSONDecodeError, OSError):
            pass

    key = input("Enter your YouTube Data API v3 key (get one free at console.cloud.google.com): ").strip()
    if not key:
        sys.exit("[!] No API key entered. Exiting.")

    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"api_key": key}, f)
        print(f"[*] Saved to {CONFIG_PATH} so you won't need to enter it again.\n")
    except OSError:
        pass  # not fatal, just won't persist

    return key


def extract_playlist_id(text: str) -> str:
    """Pull a playlist ID out of a full URL, or return it if it's already an ID."""
    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", text)
    if match:
        return match.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]+", text):
        return text
    raise ValueError(f"Could not find a playlist ID in: {text}")


# -------------------------
# Playlist Fetching
# -------------------------
def fetch_playlist_items(playlist_id: str, api_key: str) -> list:
    items = []
    page_token = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(f"{API_BASE}/playlistItems", params=params, timeout=15)

        if resp.status_code != 200:
            error = resp.json().get("error", {})
            reason = error.get("errors", [{}])[0].get("reason", "unknown")
            message = error.get("message", resp.text)
            if reason == "playlistNotFound":
                raise RuntimeError("Playlist not found. Check the link and that it's public or unlisted.")
            if reason in ("quotaExceeded", "dailyLimitExceeded"):
                raise RuntimeError("YouTube API quota exceeded for this key. Try again tomorrow or use a different key.")
            if reason in ("keyInvalid", "badRequest") or resp.status_code == 400:
                raise RuntimeError(f"API request error: {message}. Check that your API key is correct and YouTube Data API v3 is enabled for it.")
            raise RuntimeError(f"YouTube API error ({resp.status_code}, {reason}): {message}")

        data = resp.json()

        for entry in data.get("items", []):
            snippet = entry["snippet"]
            content = entry.get("contentDetails", {})
            video_id = content.get("videoId") or snippet.get("resourceId", {}).get("videoId")

            items.append({
                "original_position": snippet.get("position", 0) + 1,
                "title": snippet.get("title", "Unknown"),
                "channel": snippet.get("videoOwnerChannelTitle", snippet.get("channelTitle", "Unknown")),
                "date_added": snippet.get("publishedAt"),        # date added TO THE PLAYLIST
                "video_published": content.get("videoPublishedAt"),  # video's own original upload date
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return items


# -------------------------
# Sorting
# -------------------------
def sort_items_newest_first(items: list) -> list:
    # Deleted/private videos sometimes have no date_added -- push those to the end
    dated = [i for i in items if i["date_added"]]
    undated = [i for i in items if not i["date_added"]]
    dated.sort(key=lambda i: i["date_added"], reverse=True)
    return dated + undated


# -------------------------
# Output
# -------------------------
def print_results(items: list):
    if items and items[0]["date_added"]:
        top = items[0]
        date_str = top["date_added"][:19].replace("T", " ")
        print(f"\nMost recently added to this playlist ({date_str}):")
        print(f"  \"{top['title']}\"  -  {top['url']}")

    print(f"\n{'New #':<6} {'Orig #':<7} {'Date Added':<20} {'Title'}")
    print("-" * 90)
    for idx, item in enumerate(items, start=1):
        date_str = item["date_added"][:19].replace("T", " ") if item["date_added"] else "unknown (video removed/private)"
        title = item["title"][:55]
        print(f"{idx:<6} {item['original_position']:<7} {date_str:<20} {title}")
    print(f"\nTotal videos: {len(items)}")


def write_csv(items: list, path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["new_position", "original_position", "date_added", "video_published", "title", "channel", "url"])
        for idx, item in enumerate(items, start=1):
            writer.writerow([idx, item["original_position"], item["date_added"], item["video_published"],
                              item["title"], item["channel"], item["url"]])


# -------------------------
# Entry Point
# -------------------------
def s0rt3r():
    clr()
    print("=" * 60)
    print(H0m3_Pa9e)
    print("=" * 60)

    api_key = get_api_key()

    playlist_input = input("Paste the YouTube playlist link (or ID): ").strip()
    if not playlist_input:
        sys.exit("[!] No playlist entered. Exiting.")

    try:
        playlist_id = extract_playlist_id(playlist_input)
        print(f"\n[*] Fetching playlist {playlist_id} ...")
        items = fetch_playlist_items(playlist_id, api_key)
        print(f"[*] Fetched {len(items)} videos. Sorting by date added (newest first)...")
        sorted_items = sort_items_newest_first(items)
    except (ValueError, RuntimeError) as e:
        sys.exit(f"[!] Error: {e}")

    print_results(sorted_items)

    export = input("\nExport this to a CSV file? [y/N]: ").strip().lower()
    if export == "y":
        path = input("File name (default: sorted_playlist.csv): ").strip() or "sorted_playlist.csv"
        write_csv(sorted_items, path)
        print(f"[*] CSV written to {path}")


if __name__ == "__main__":
    s0rt3r()
