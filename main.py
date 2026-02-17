from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import requests
import re
from urllib.parse import quote

app = FastAPI()

# GUIDE: Please place your 'cookies.txt' file in the root directory for authentication to work.
# This prevents "Sign in to confirm you’re not a bot" errors.

@app.get("/health")
async def health_check():
    return {"status": "active"}

@app.get("/download")
async def download(url: str, format: str = "mp4"):
    print(f"[REQUEST] Download Request: {url} ({format})")
    
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    # Configuration for yt-dlp with Cookie and User-Agent spoofing
    ydl_opts = {
        'format': 'best' if format == 'mp4' else 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',  # Required for authentication
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("[INFO] Fetching video metadata...")
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'video')
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title).strip()
            filename = f"{clean_title}.{format}"
            
            download_url = info.get('url')
            
            if not download_url:
                 raise Exception("Could not retrieve download URL.")

            print(f"[INFO] Video found: {title}")
            print(f"[INFO] Download URL: {download_url}")

            # Generator to stream the content
            def iterfile():
                try:
                    with requests.get(download_url, stream=True) as r:
                        r.raise_for_status()
                        for chunk in r.iter_content(chunk_size=8192):
                            yield chunk
                except Exception as e:
                    print(f"[ERROR] Stream error: {e}")

            # Headers for browser download
            headers = {
                'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}",
                'Content-Type': 'video/mp4' if format == 'mp4' else 'audio/mpeg'
            }

            return StreamingResponse(iterfile(), headers=headers)

    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
        print(f"[ERROR] YouTube Bot Detection/Download Error: {e}")
        return JSONResponse(
            status_code=403,
            content={"error": "YouTube Bot Detection: Please check server logs and ensure 'cookies.txt' is valid."}
        )
    except Exception as e:
        print(f"[ERROR] General Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n==================================================")
    print("🚀 YouTube Downloader Server Running (Python)")
    print("📡 URL: http://localhost:3000")
    print("🍪 Ensure 'cookies.txt' is present for authentication")
    print("==================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=3000)
