from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import yt_dlp
import requests
import re
from urllib.parse import quote

app = FastAPI()

@app.get("/download")
async def download(url: str, format: str = "mp4"):
    print(f"[REQUEST] Download Request: {url} ({format})")
    
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    try:
        # Configuration for yt-dlp
        ydl_opts = {
            'format': 'best' if format == 'mp4' else 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("[INFO] Fetching video metadata...")
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'video')
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title).strip()
            filename = f"{clean_title}.{format}"
            
            download_url = info['url']
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
            # Content-Disposition with filename* for UTF-8 support
            headers = {
                'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}",
                'Content-Type': 'video/mp4' if format == 'mp4' else 'audio/mpeg'
            }

            return StreamingResponse(iterfile(), headers=headers)

    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n==================================================")
    print("🚀 YouTube Downloader Server Running (Python)")
    print("📡 URL: http://localhost:3000")
    print("==================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=3000)
