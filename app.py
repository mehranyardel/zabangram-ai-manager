from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid, shutil, subprocess, json

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)

app = FastAPI(title="ZABANGRAM AI MANAGER")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")

@app.post("/api/analyze-upload")
async def analyze_upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm"}:
        return {"ok": False, "message": "فرمت فایل پشتیبانی نمی‌شود. MP4، MOV یا WEBM بفرستید."}
    name = f"{uuid.uuid4().hex}{suffix}"
    target = UPLOADS / name
    with target.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    details = {"filename": file.filename, "bytes": target.stat().st_size}
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            raw = subprocess.check_output([
                ffprobe, "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(target)
            ], timeout=20)
            probe = json.loads(raw)
            details["duration_seconds"] = float(probe.get("format", {}).get("duration", 0))
            details["streams"] = [s.get("codec_type") for s in probe.get("streams", [])]
        except Exception:
            details["media_probe"] = "failed"
    return {
        "ok": True,
        "message": "فایل دریافت شد. زیرساخت آماده پردازش است؛ برای تحلیل واقعی گفتار و تصویر باید سرویس هوش مصنوعی به سرور متصل شود.",
        "details": details,
        "next": "AI_PROVIDER_NOT_CONFIGURED"
    }

@app.post("/api/analyze-url")
def analyze_url(url: str = Form(...), platform: str = Form(...)):
    if not url.startswith(("https://", "http://")):
        return {"ok": False, "message": "لینک معتبر وارد کنید."}
    if platform not in {"aparat", "instagram"}:
        return {"ok": False, "message": "پلتفرم نامعتبر است."}
    return {
        "ok": True,
        "platform": platform,
        "url": url,
        "status": "URL_RECEIVED",
        "message": "لینک ثبت شد؛ واکشی خودکار این پلتفرم هنوز به آداپتور مجاز و قابل‌دسترسی نیاز دارد. هیچ محتوایی بدون دریافت واقعی تحلیل‌شده اعلام نمی‌شود."
    }
