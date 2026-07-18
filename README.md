# Playlist Sorter
A small command-line tool that pulls a YouTube playlist via the YouTube Data
API v3, sorts it by the date each video was **added to the playlist**
(newest first), and optionally exports the result to CSV.
Useful for playlists where YouTube's own ordering doesn't reflect when
videos were actually added (e.g. long-running "watch later"-style lists).
```
============================================================
P L 4 Y L 1 S T   S 0 R T 3 R
============================================================
```
## Features
- Accepts a full playlist URL or a bare playlist ID
- Paginates through the entire playlist automatically (no 50-item cap)
- Sorts by `date_added` (newest first); undated/removed videos are pushed
  to the end instead of breaking the sort
- Shows both the new position and the original playlist position, so you
  can see how much the order shifted
- Optional CSV export
- API key can come from an environment variable, a local config file, or
  a one-time prompt (saved for next time)
## Requirements
- Python 3.8+
- [`requests`](https://pypi.org/project/requests/)
```bash
pip install requests
```
## Setup
You need a free YouTube Data API v3 key:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select an existing one)
3. Enable the **YouTube Data API v3**
4. Create an API key under **Credentials**
You can provide the key in one of three ways, checked in this order:
1. Environment variable:
   ```bash
   export YOUTUBE_API_KEY="your-key-here"
   ```
2. `playlist_sorter_config.json` (created automatically next to the script
   after you enter a key once)
3. Interactive prompt on first run — the key is then saved to the config
   file above so you won't be asked again
## Usage
```bash
python playlist_sorter.py
```
You'll be prompted for:

1. **Playlist link or ID** — either works:
   - `https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxx`
   - `PLxxxxxxxxxxxxxxxx`
2. **Export to CSV?** — `y` to save results, anything else to skip
### Example output
```
Most recently added to this playlist (2026-06-30 14:22:10):
  "Some Video Title"  -  https://www.youtube.com/watch?v=xxxxxxxxxxx

New #  Orig #  Date Added           Title
------------------------------------------------------------------------------------------
1      42      2026-06-30 14:22:10  Some Video Title
2      12      2026-06-14 09:03:41  Another Video
...
Total videos: 87
```
### CSV columns

| Column              | Description                                   |
|---------------------|------------------------------------------------|
| `new_position`      | Position after sorting by date added           |
| `original_position` | Position in the playlist as YouTube shows it    |
| `date_added`         | When the video was added to the playlist        |
| `video_published`   | The video's own original upload date            |
| `title`              | Video title                                     |
| `channel`            | Uploading channel                               |
| `url`                | Direct link to the video                        |

## Notes
- Private/deleted videos have no `date_added` and are listed at the end
  with an `unknown (video removed/private)` marker.
- API quota: the default free tier is 10,000 units/day; fetching a
  playlist costs a handful of units per page of 50 items, so this comfortably
  handles even very large playlists.

## License
MIT — do whatever you want with it.
