import os
import json
import queue
import threading
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response, render_template_string

app = Flask(__name__)

FFMPEG = r"C:\Users\sonru\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
COOKIES_YT = str(Path(__file__).parent.parent / "cookies cookies.txt")
COOKIES_IG = str(Path(__file__).parent.parent / "cookies_instagram.txt")
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# job_id -> {"status": ..., "events": queue, "file": ...}
jobs = {}

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>YT Downloader</title>
<style>
  :root {
    --bg:        #0C0C10;
    --surface:   #16161C;
    --border:    #26262F;
    --accent:    #E8414A;
    --accent-lo: #2A1214;
    --text:      #EEEDF4;
    --muted:     #7A7989;
    --success:   #3EBF7A;
    --warn:      #E8A041;
    --radius:    6px;
    --mono: "SF Mono", "Cascadia Code", "Fira Code", Consolas, monospace;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg:        #F2F2F5;
      --surface:   #FFFFFF;
      --border:    #DDDDE8;
      --accent:    #C8252D;
      --accent-lo: #FDE8E9;
      --text:      #111118;
      --muted:     #888898;
    }
  }
  :root[data-theme="dark"] {
    --bg:#0C0C10;--surface:#16161C;--border:#26262F;--accent:#E8414A;
    --accent-lo:#2A1214;--text:#EEEDF4;--muted:#7A7989;--success:#3EBF7A;--warn:#E8A041;
  }
  :root[data-theme="light"] {
    --bg:#F2F2F5;--surface:#FFFFFF;--border:#DDDDE8;--accent:#C8252D;
    --accent-lo:#FDE8E9;--text:#111118;--muted:#888898;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 16px 80px;
  }

  .shell {
    width: 100%;
    max-width: 640px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  header {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .logo {
    width: 36px; height: 36px;
    background: var(--accent);
    border-radius: 8px;
    display: grid;
    place-items: center;
    flex-shrink: 0;
  }
  .logo svg { width: 18px; height: 18px; fill: #fff; }

  h1 {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -.3px;
    color: var(--text);
  }
  h1 span { color: var(--muted); font-weight: 400; }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .card-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }

  label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--muted);
    display: block;
    margin-bottom: 6px;
  }

  textarea {
    width: 100%;
    height: 120px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    font-family: var(--mono);
    font-size: 12.5px;
    line-height: 1.6;
    padding: 10px 12px;
    resize: vertical;
    transition: border-color .15s;
    outline: none;
  }
  textarea::placeholder { color: var(--muted); }
  textarea:focus { border-color: var(--accent); }

  .format-row {
    display: flex;
    gap: 8px;
  }

  .fmt-btn {
    flex: 1;
    padding: 9px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg);
    color: var(--muted);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all .15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  .fmt-btn:hover { border-color: var(--accent); color: var(--text); }
  .fmt-btn.active {
    background: var(--accent-lo);
    border-color: var(--accent);
    color: var(--accent);
  }

  .btn-dl {
    width: 100%;
    padding: 11px;
    background: var(--accent);
    border: none;
    border-radius: var(--radius);
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity .15s, transform .1s;
    letter-spacing: .01em;
  }
  .btn-dl:hover { opacity: .88; }
  .btn-dl:active { transform: scale(.99); }
  .btn-dl:disabled { opacity: .4; cursor: not-allowed; }

  /* Jobs list */
  .jobs { display: flex; flex-direction: column; gap: 10px; }

  .job {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 4px 12px;
    align-items: start;
  }

  .job-title {
    font-size: 13px;
    font-weight: 500;
    grid-column: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .job-status {
    font-size: 11.5px;
    color: var(--muted);
    grid-column: 1;
    font-family: var(--mono);
  }
  .job-status.done   { color: var(--success); }
  .job-status.error  { color: var(--accent); }

  .job-action {
    grid-column: 2;
    grid-row: 1 / 3;
    align-self: center;
  }

  .btn-dl-file {
    padding: 6px 14px;
    background: var(--success);
    border: none;
    border-radius: var(--radius);
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    text-decoration: none;
    display: inline-block;
    transition: opacity .15s;
  }
  .btn-dl-file:hover { opacity: .85; }

  .progress-bar-wrap {
    grid-column: 1 / -1;
    height: 2px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 6px;
  }
  .progress-bar-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
    transition: width .3s ease;
  }

  .empty-state {
    text-align: center;
    color: var(--muted);
    padding: 32px 0;
    font-size: 13px;
  }

  /* Theme toggle */
  .theme-toggle {
    margin-left: auto;
    background: none;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--muted);
    padding: 5px 10px;
    font-size: 12px;
    cursor: pointer;
  }
  .theme-toggle:hover { color: var(--text); border-color: var(--text); }
</style>
</head>
<body>
<div class="shell">
  <header>
    <div class="logo">
      <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg>
    </div>
    <h1>YT Downloader <span>/ local</span></h1>
    <button class="theme-toggle" onclick="toggleTheme()">tema</button>
  </header>

  <div class="card">
    <div class="card-body">
      <div>
        <label>URLs de YouTube o Instagram (una por línea)</label>
        <textarea id="urls" placeholder="https://www.youtube.com/watch?v=...&#10;https://www.instagram.com/reel/..."></textarea>
      </div>

      <div>
        <label>Formato</label>
        <div class="format-row">
          <button class="fmt-btn active" id="fmt-mp3" onclick="setFmt('mp3')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/></svg>
            MP3 — solo audio
          </button>
          <button class="fmt-btn" id="fmt-mp4" onclick="setFmt('mp4')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17 10.5V7a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3.5l4 4v-11l-4 4z"/></svg>
            MP4 — video completo
          </button>
        </div>
      </div>

      <button class="btn-dl" id="dl-btn" onclick="startDownload()">Descargar</button>
    </div>
  </div>

  <div class="jobs" id="jobs-list">
    <div class="empty-state" id="empty">Los archivos aparecerán aquí al terminar.</div>
  </div>
</div>

<script>
let fmt = 'mp3';

function setFmt(f) {
  fmt = f;
  document.getElementById('fmt-mp3').classList.toggle('active', f === 'mp3');
  document.getElementById('fmt-mp4').classList.toggle('active', f === 'mp4');
}

function toggleTheme() {
  const root = document.documentElement;
  const cur = root.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
}

async function startDownload() {
  const raw = document.getElementById('urls').value.trim();
  if (!raw) return;
  const urls = raw.split('\n').map(u => u.trim()).filter(Boolean);
  if (!urls.length) return;

  const btn = document.getElementById('dl-btn');
  btn.disabled = true;
  btn.textContent = 'Iniciando…';

  try {
    const res = await fetch('/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ urls, fmt })
    });
    const { jobs } = await res.json();
    document.getElementById('empty').style.display = 'none';
    for (const job of jobs) addJobCard(job.id, job.url, fmt);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Descargar';
  }
}

function addJobCard(jobId, url, fmt) {
  const list = document.getElementById('jobs-list');
  const card = document.createElement('div');
  card.className = 'job';
  card.id = 'job-' + jobId;
  card.innerHTML = `
    <div class="job-title">${url}</div>
    <div class="job-status" id="st-${jobId}">Iniciando…</div>
    <div class="job-action" id="ac-${jobId}"></div>
    <div class="progress-bar-wrap"><div class="progress-bar-fill" id="pb-${jobId}" style="width:0%"></div></div>
  `;
  list.insertBefore(card, list.firstChild);
  listenJob(jobId);
}

function listenJob(jobId) {
  const es = new EventSource('/progress/' + jobId);
  const st = document.getElementById('st-' + jobId);
  const pb = document.getElementById('pb-' + jobId);
  const ac = document.getElementById('ac-' + jobId);
  const title = document.querySelector('#job-' + jobId + ' .job-title');

  es.onmessage = (e) => {
    const d = JSON.parse(e.data);

    if (d.title) title.textContent = d.title;

    if (d.pct != null) {
      pb.style.width = d.pct + '%';
      st.textContent = `${d.pct}% — ${d.speed || ''} ETA ${d.eta || ''}`;
    }
    if (d.msg) st.textContent = d.msg;

    if (d.status === 'done') {
      st.textContent = 'Listo ✓';
      st.className = 'job-status done';
      pb.style.width = '100%';
      pb.style.background = 'var(--success)';
      ac.innerHTML = `<a class="btn-dl-file" href="/file/${jobId}" download="${d.filename}">↓ Guardar</a>`;
      es.close();
    }
    if (d.status === 'error') {
      st.textContent = d.msg || 'Error';
      st.className = 'job-status error';
      es.close();
    }
  };
}
</script>
</body>
</html>
"""


def run_download(job_id: str, url: str, fmt: str):
    q = jobs[job_id]["events"]
    out_dir = DOWNLOAD_DIR / job_id
    out_dir.mkdir(exist_ok=True)

    def push(data: dict):
        q.put(json.dumps(data))

    import subprocess, re

    is_instagram = "instagram.com" in url
    cookies_file = COOKIES_IG if is_instagram else COOKIES_YT
    platform_msg = "Conectando con Instagram…" if is_instagram else "Conectando con YouTube…"

    yt_flags = [] if is_instagram else ["--js-runtimes", "node", "--remote-components", "ejs:github"]

    common = [
        "--cookies", cookies_file,
        *yt_flags,
        "--ffmpeg-location", FFMPEG,
        "--newline",
        "-o", str(out_dir / "%(title)s.%(ext)s"),
        url,
    ]
    if fmt == "mp3":
        cmd = ["python", "-m", "yt_dlp", "-x", "--audio-format", "mp3", "--audio-quality", "0"] + common
    else:
        cmd = ["python", "-m", "yt_dlp",
               "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
               "--merge-output-format", "mp4"] + common

    push({"msg": platform_msg})
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue

        # Parse title from destination line
        m_dest = re.search(r"\[download\] Destination: .+[/\\](.+?)(?:\.(webm|mp4|m4a|mp3|opus))?$", line)
        if m_dest:
            push({"title": m_dest.group(1)})
            continue

        # Progress line: [download]  45.3% of 12.34MiB at 2.1MiB/s ETA 00:03
        m = re.search(r"(\d+\.\d+)%.*?at\s+([\d.]+\S+)\s+ETA\s+(\S+)", line)
        if m:
            push({"pct": float(m.group(1)), "speed": m.group(2), "eta": m.group(3)})
            continue

        if "[ExtractAudio]" in line or "Merging" in line:
            push({"msg": "Procesando audio…", "pct": 95})
            continue

        if "ERROR" in line:
            push({"status": "error", "msg": line})
            proc.wait()
            return

        if line.startswith("[") or "WARNING" in line:
            push({"msg": line[:80]})

    proc.wait()
    if proc.returncode != 0:
        push({"status": "error", "msg": f"yt-dlp salió con código {proc.returncode}"})
        return

    # Find the output file
    files = list(out_dir.iterdir())
    if not files:
        push({"status": "error", "msg": "No se encontró el archivo descargado"})
        return

    outfile = files[0]
    jobs[job_id]["file"] = outfile
    push({"status": "done", "filename": outfile.name, "pct": 100})


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/start", methods=["POST"])
def start():
    data = request.json
    urls = data.get("urls", [])
    fmt = data.get("fmt", "mp3")
    result = []
    for url in urls:
        job_id = str(uuid.uuid4())[:8]
        q = queue.Queue()
        jobs[job_id] = {"events": q, "file": None}
        t = threading.Thread(target=run_download, args=(job_id, url, fmt), daemon=True)
        t.start()
        result.append({"id": job_id, "url": url})
    return jsonify({"jobs": result})


@app.route("/progress/<job_id>")
def progress(job_id):
    if job_id not in jobs:
        return "Not found", 404

    def stream():
        q = jobs[job_id]["events"]
        while True:
            try:
                msg = q.get(timeout=30)
                yield f"data: {msg}\n\n"
                d = json.loads(msg)
                if d.get("status") in ("done", "error"):
                    break
            except queue.Empty:
                yield "data: {\"msg\": \"…\"}\n\n"

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/file/<job_id>")
def serve_file(job_id):
    if job_id not in jobs or not jobs[job_id]["file"]:
        return "Not found", 404
    f = jobs[job_id]["file"]
    return send_file(f, as_attachment=True, download_name=f.name)


if __name__ == "__main__":
    app.run(port=5055, debug=False)
