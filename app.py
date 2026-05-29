from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image
import io, base64, os, uuid, json
from pathlib import Path
from datetime import datetime

# ==================================================
# CONFIG
# ==================================================
GEMINI_API_KEY = "AQ.Ab8RN6JjOt5oly8AvQ2e3lL5zYLL5W6rXXeq7qLDSALpGSUbfw"
HF_TOKEN       = "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"
OUTPUT_FOLDER  = r"D:\python_aivideos\auto-hugging-face\final"
HF_MODEL       = "Danrisi/UltraReal_FineTune_Anima_base1"
HF_STEPS       = 28
HF_GUIDANCE    = 3.5
IMAGE_WIDTH    = 1024
IMAGE_HEIGHT   = 1024

# ==================================================
# INIT
# ==================================================
app = Flask(__name__)
genai.configure(api_key=GEMINI_API_KEY)
prompt_model = genai.GenerativeModel("gemini-2.5-flash")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
print(f"✅ Output  : {OUTPUT_FOLDER}")
print(f"✅ Model   : {HF_MODEL}")

# ==================================================
# HTML
# ==================================================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Brand Video Pack Generator</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0a0a0a;
  color: #f0f0f0;
  font-family: 'Segoe UI', Arial, sans-serif;
  padding: 36px 20px;
}
.container { max-width: 980px; margin: auto; }

h1 {
  font-size: 2rem;
  margin-bottom: 6px;
  background: linear-gradient(90deg, #00c896, #00a0ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle { color: #666; font-size: 0.85rem; margin-bottom: 28px; }

/* ── Cards ── */
.card {
  background: #161616;
  border: 1px solid #252525;
  border-radius: 14px;
  padding: 22px;
  margin-bottom: 16px;
}
.card-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: #777;
  margin-bottom: 12px;
}

input[type="file"] {
  width: 100%;
  padding: 14px;
  background: #0d0d0d;
  border: 1px dashed #383838;
  border-radius: 8px;
  color: #bbb;
  cursor: pointer;
  font-size: 0.9rem;
}

textarea {
  width: 100%;
  height: 110px;
  background: #0d0d0d;
  color: #e8e8e8;
  border: 1px solid #252525;
  border-radius: 8px;
  padding: 12px;
  font-size: 0.85rem;
  resize: vertical;
}

.row { display: flex; gap: 10px; }
.tbtn {
  flex: 1;
  padding: 10px 8px;
  border: 1px solid #383838;
  background: #0d0d0d;
  color: #777;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
  text-align: center;
}
.tbtn.on { border-color: #00c896; color: #00c896; background: #001a12; }

.btn-go {
  width: 100%;
  padding: 16px;
  margin-top: 8px;
  background: linear-gradient(90deg, #00c896, #0090e0);
  border: none;
  color: #fff;
  border-radius: 10px;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.3px;
  transition: opacity 0.2s;
}
.btn-go:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Pipeline progress ── */
.pipeline {
  display: none;
  margin-top: 20px;
  background: #0d0d0d;
  border: 1px solid #222;
  border-radius: 14px;
  overflow: hidden;
}
.stage {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 20px;
  border-bottom: 1px solid #1a1a1a;
  font-size: 0.88rem;
  color: #444;
  transition: all 0.3s;
}
.stage:last-child { border-bottom: none; }
.stage.active { color: #00c896; background: #001208; }
.stage.done   { color: #00ff88; }
.stage.error  { color: #ff5555; background: #1a0000; }

.stage-dot {
  width: 9px; height: 9px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.stage-tag {
  margin-left: auto;
  font-size: 0.68rem;
  padding: 2px 8px;
  border-radius: 20px;
  border: 1px solid currentColor;
  opacity: 0.8;
  white-space: nowrap;
}
.spin {
  display: inline-block;
  width: 11px; height: 11px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: sp 0.7s linear infinite;
  margin-left: 6px;
  vertical-align: middle;
}
@keyframes sp { to { transform: rotate(360deg); } }

/* ── 4-image grid ── */
.grid-wrap { display: none; margin-top: 26px; }
.grid-heading {
  font-size: 1rem;
  font-weight: 600;
  color: #ccc;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.grid-heading .count {
  background: #00c896;
  color: #000;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 20px;
}
.img-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.img-tile {
  background: #161616;
  border: 1px solid #252525;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  transition: border-color 0.3s;
}
.img-tile:hover { border-color: #00c896; }
.img-tile .shot-badge {
  position: absolute;
  top: 10px; left: 10px;
  background: rgba(0,0,0,0.8);
  color: #00c896;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid #00c896;
  z-index: 2;
}
.img-tile .loading-tile {
  width: 100%;
  aspect-ratio: 1;
  background: #111;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #444;
  font-size: 0.82rem;
}
.big-spin {
  width: 28px; height: 28px;
  border: 3px solid #00c896;
  border-top-color: transparent;
  border-radius: 50%;
  animation: sp 0.8s linear infinite;
}
.img-tile img {
  width: 100%;
  display: block;
  object-fit: cover;
}
.img-tile .tile-foot {
  padding: 10px 14px;
  font-size: 0.75rem;
  color: #555;
  border-top: 1px solid #1e1e1e;
}
.img-tile .tile-foot b { color: #00c896; }

/* ── Prompt pills ── */
.prompts-wrap { display: none; margin-top: 18px; }
.prompts-heading { font-size: 0.85rem; color: #666; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.6px; }
.pill {
  background: #0d0d0d;
  border: 1px solid #222;
  border-radius: 8px;
  padding: 11px 14px;
  font-size: 0.78rem;
  color: #888;
  line-height: 1.55;
  margin-bottom: 8px;
}
.pill .ptag { color: #00c896; font-size: 0.7rem; font-weight: 700; display: block; margin-bottom: 4px; }
</style>
</head>
<body>
<div class="container">

<h1>🎬 AI Brand Video Pack</h1>
<p class="subtitle">
  Upload product image → Avatar created automatically →
  3 more shots generated (same avatar, different angles) →
  4-image video pack ready
</p>

<!-- STEP 1: Upload -->
<div class="card">
  <div class="card-label">Step 1 · Upload Your Product Image</div>
  <input type="file" id="imgFile" accept="image/*">
</div>

<!-- STEP 2: Size -->
<div class="card">
  <div class="card-label">Step 2 · Image Size</div>
  <div class="row">
    <button class="tbtn on"  id="sz1"  onclick="setSize(1024,1024)">⬛ 1024×1024 Square</button>
    <button class="tbtn"     id="sz2"  onclick="setSize(1344,768)">🖼 1344×768 Landscape</button>
    <button class="tbtn"     id="sz3"  onclick="setSize(768,1344)">📱 768×1344 Portrait</button>
  </div>
</div>

<!-- STEP 3: Quality -->
<div class="card">
  <div class="card-label">Step 3 · Quality per Image</div>
  <div class="row">
    <button class="tbtn"    id="q20" onclick="setQ(20)">⚡ 20 Steps — Fast</button>
    <button class="tbtn on" id="q28" onclick="setQ(28)">✨ 28 Steps — Balanced</button>
    <button class="tbtn"    id="q50" onclick="setQ(50)">💎 50 Steps — Max</button>
  </div>
</div>

<button class="btn-go" id="goBtn" onclick="runAll()">
  🚀 Generate Avatar + 3 Video Shots
</button>

<!-- Pipeline progress -->
<div class="pipeline" id="pipeline">
  <div class="stage" id="st0"><div class="stage-dot"></div> Analyzing product image with Gemini…          <span class="stage-tag">Gemini</span></div>
  <div class="stage" id="st1"><div class="stage-dot"></div> Generating Avatar — Shot 1 · Hero pose          <span class="stage-tag">FLUX.1-dev</span></div>
  <div class="stage" id="st2"><div class="stage-dot"></div> Creating 3 variation prompts (pose + angle)…   <span class="stage-tag">Gemini</span></div>
  <div class="stage" id="st3"><div class="stage-dot"></div> Generating Shot 2 · Close-Up                   <span class="stage-tag">FLUX.1-dev</span></div>
  <div class="stage" id="st4"><div class="stage-dot"></div> Generating Shot 3 · Wide / Lifestyle            <span class="stage-tag">FLUX.1-dev</span></div>
  <div class="stage" id="st5"><div class="stage-dot"></div> Generating Shot 4 · Dynamic / Motion            <span class="stage-tag">FLUX.1-dev</span></div>
  <div class="stage" id="st6"><div class="stage-dot"></div> All 4 images saved to output folder ✓           <span class="stage-tag">Done</span></div>
</div>

<!-- 4-image grid (images appear as they finish) -->
<div class="grid-wrap" id="gridWrap">
  <div class="grid-heading">
    🖼 Video Pack — 4 Images
    <span class="count" id="doneCount">0 / 4</span>
  </div>
  <div class="img-grid" id="imgGrid">
    <div class="img-tile" id="tile0">
      <span class="shot-badge">🎯 Shot 1 — Hero</span>
      <div class="loading-tile"><div class="big-spin"></div>Waiting…</div>
    </div>
    <div class="img-tile" id="tile1">
      <span class="shot-badge">🔍 Shot 2 — Close-Up</span>
      <div class="loading-tile"><div class="big-spin"></div>Waiting…</div>
    </div>
    <div class="img-tile" id="tile2">
      <span class="shot-badge">🌍 Shot 3 — Wide</span>
      <div class="loading-tile"><div class="big-spin"></div>Waiting…</div>
    </div>
    <div class="img-tile" id="tile3">
      <span class="shot-badge">⚡ Shot 4 — Dynamic</span>
      <div class="loading-tile"><div class="big-spin"></div>Waiting…</div>
    </div>
  </div>
</div>

<!-- Prompts used -->
<div class="prompts-wrap" id="promptsWrap">
  <div class="prompts-heading">📝 Prompts Used</div>
  <div id="pillBox"></div>
</div>

</div><!-- /container -->

<script>
let W=1024, H=1024, Q=28, doneImages=0;

const SHOT_LABELS = [
  '🎯 Shot 1 — Hero',
  '🔍 Shot 2 — Close-Up',
  '🌍 Shot 3 — Wide / Lifestyle',
  '⚡ Shot 4 — Dynamic / Motion'
];

function setSize(w,h){
  W=w; H=h;
  ['sz1','sz2','sz3'].forEach(id=>document.getElementById(id).classList.remove('on'));
  if(w===1024) document.getElementById('sz1').classList.add('on');
  else if(w===1344) document.getElementById('sz2').classList.add('on');
  else document.getElementById('sz3').classList.add('on');
}

function setQ(q){
  Q=q;
  ['q20','q28','q50'].forEach(id=>document.getElementById(id).classList.remove('on'));
  document.getElementById('q'+q).classList.add('on');
}

function stage(id, state){
  const el = document.getElementById(id);
  el.className = 'stage ' + state;
  const sp = el.querySelector('.spin');
  if(state==='active' && !sp){
    el.insertAdjacentHTML('beforeend','<span class="spin"></span>');
  } else if(state!=='active' && sp){
    sp.remove();
  }
}

function showImage(tileIndex, b64, savePath){
  const tile = document.getElementById('tile'+tileIndex);
  tile.innerHTML = `
    <span class="shot-badge">${SHOT_LABELS[tileIndex]}</span>
    <img src="data:image/png;base64,${b64}" alt="shot ${tileIndex+1}">
    <div class="tile-foot">💾 <b>${savePath.replace(/.*[\\\\/]/,'')}</b></div>
  `;
  doneImages++;
  document.getElementById('doneCount').textContent = doneImages + ' / 4';
}

function addPill(index, promptText){
  const box = document.getElementById('pillBox');
  const div = document.createElement('div');
  div.className = 'pill';
  div.innerHTML = `<span class="ptag">${SHOT_LABELS[index]}</span>${promptText}`;
  box.appendChild(div);
}

async function runAll(){
  const fileInput = document.getElementById('imgFile');
  if(!fileInput.files.length){ alert('Please upload a product image first.'); return; }

  const btn = document.getElementById('goBtn');
  btn.disabled = true;
  doneImages = 0;

  // Reset UI
  document.getElementById('pipeline').style.display = 'block';
  document.getElementById('gridWrap').style.display = 'block';
  document.getElementById('promptsWrap').style.display = 'none';
  document.getElementById('pillBox').innerHTML = '';
  document.getElementById('doneCount').textContent = '0 / 4';
  ['st0','st1','st2','st3','st4','st5','st6'].forEach(id=>stage(id,''));

  // Reset tiles
  for(let i=0;i<4;i++){
    const tile = document.getElementById('tile'+i);
    tile.innerHTML = `
      <span class="shot-badge">${SHOT_LABELS[i]}</span>
      <div class="loading-tile"><div class="big-spin"></div>Waiting…</div>
    `;
  }

  try {

    // ── STAGE 0: Gemini base prompt ──────────────────────────
    stage('st0','active');
    const fd = new FormData();
    fd.append('image', fileInput.files[0]);
    const r0 = await fetch('/generate-prompt', {method:'POST', body:fd});
    const d0 = await r0.json();
    if(!d0.success) throw new Error('Gemini base prompt: ' + d0.error);
    stage('st0','done');

    const basePrompt = d0.prompt;

    // ── STAGE 1: FLUX — Shot 1 (Hero / Avatar) ───────────────
    stage('st1','active');
    // Mark tile 0 as generating
    document.getElementById('tile0').querySelector('.loading-tile').innerHTML =
      '<div class="big-spin"></div>Generating avatar…';

    const r1 = await fetch('/generate-image', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({prompt: basePrompt, width:W, height:H, steps:Q, index:1})
    });
    const d1 = await r1.json();
    if(!d1.success) throw new Error('Shot 1: ' + d1.error);
    stage('st1','done');
    showImage(0, d1.image_b64, d1.saved_path);
    addPill(0, basePrompt);

    // ── STAGE 2: Gemini — 3 variation prompts ────────────────
    stage('st2','active');
    const r2 = await fetch('/generate-variations', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({base_prompt: basePrompt})
    });
    const d2 = await r2.json();
    if(!d2.success) throw new Error('Variations: ' + d2.error);
    stage('st2','done');

    const varPrompts = d2.prompts; // array of 3

    // Show prompts panel
    document.getElementById('promptsWrap').style.display = 'block';
    varPrompts.forEach((p,i) => addPill(i+1, p));

    // ── STAGES 3–5: FLUX — Shots 2, 3, 4 ────────────────────
    const stageIds  = ['st3','st4','st5'];
    const tileLabels = ['Generating close-up…','Generating wide shot…','Generating dynamic shot…'];

    for(let i=0; i<3; i++){
      stage(stageIds[i],'active');
      document.getElementById('tile'+(i+1)).querySelector('.loading-tile').innerHTML =
        `<div class="big-spin"></div>${tileLabels[i]}`;

      const r = await fetch('/generate-image',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          prompt: varPrompts[i],
          width: W, height: H, steps: Q,
          index: i+2
        })
      });
      const d = await r.json();
      if(!d.success) throw new Error(`Shot ${i+2}: `+d.error);
      stage(stageIds[i],'done');
      showImage(i+1, d.image_b64, d.saved_path);
    }

    stage('st6','done');

  } catch(err){
    console.error(err);
    alert('❌ Error: '+err.message);
    ['st0','st1','st2','st3','st4','st5','st6'].forEach(id=>{
      if(document.getElementById(id).classList.contains('active')) stage(id,'error');
    });
  } finally {
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""

# ==================================================
# HOME
# ==================================================
@app.route("/")
def home():
    return render_template_string(HTML)


# ==================================================
# ROUTE 1 — Base Avatar Prompt (Gemini)
# ==================================================
@app.route("/generate-prompt", methods=["POST"])
def generate_prompt():
    try:
        print("\n=== GEMINI: BASE AVATAR PROMPT ===")
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded."})

        product_image = Image.open(request.files["image"])

        analysis_prompt = """
Analyze this product image carefully.
Create a cinematic AI advertising prompt for a photorealistic human avatar
that will model or showcase this product.

The avatar must naturally match the product's target audience.

IMPORTANT — describe these identity details precisely so they stay consistent
across multiple shots:
- Avatar: exact gender, age range, skin tone, hair color and style, clothing style and color
- Product: exact placement (held, worn, on table, etc.) and its position
- Environment: detailed background setting

Shot style for this base prompt:
HERO SHOT — avatar facing camera confidently, eye-level, product clearly visible,
luxury commercial photography, DSLR depth of field, cinematic lighting, 8K photorealistic.

Return ONLY the final image generation prompt. No labels, no explanation.
"""
        response = prompt_model.generate_content([analysis_prompt, product_image])
        prompt   = response.text.strip()
        print(f"Base prompt OK ({len(prompt)} chars)")
        return jsonify({"success": True, "prompt": prompt})

    except Exception as e:
        print(f"[ERROR] base prompt: {e}")
        return jsonify({"success": False, "error": str(e)})


# ==================================================
# ROUTE 2 — 3 Variation Prompts (Gemini)
# ==================================================
@app.route("/generate-variations", methods=["POST"])
def generate_variations():
    try:
        print("\n=== GEMINI: 3 VARIATION PROMPTS ===")
        data        = request.get_json()
        base_prompt = data.get("base_prompt", "").strip()
        if not base_prompt:
            return jsonify({"success": False, "error": "Base prompt is empty."})

        var_prompt = f"""
You are a cinematic AI image director making a 4-shot brand video sequence.

The base prompt below describes a specific avatar and product (Shot 1 — Hero).
Write exactly 3 MORE prompts for Shots 2, 3, 4.

STRICT RULES — break any of these and the video pack will be unusable:
1. SAME avatar: identical gender, skin tone, hair color/style, clothing color/style
2. SAME product: identical item, same color, logical placement
3. SAME environment / background style
4. ONLY change: camera angle, pose, framing
5. Every prompt must be fully self-contained — repeat all identity details
6. Never introduce new people, new products, or new environments

BASE PROMPT (Shot 1 — Hero):
{base_prompt}

Write prompts for:

SHOT 2 — CLOSE-UP:
Tight close-up, camera at product/face level, very shallow depth of field,
avatar face partially visible on one side, product large in foreground,
intimate luxury editorial feel.

SHOT 3 — WIDE / LIFESTYLE:
Wide shot, camera pulled back, full body visible, avatar in natural lifestyle
context with product, aspirational magazine spread composition.

SHOT 4 — DYNAMIC / MOTION:
Low-angle dynamic shot, slight motion blur on hair or fabric,
avatar mid-stride or turning toward camera, energetic commercial energy,
product clearly visible and in motion.

Return ONLY a valid JSON array of exactly 3 strings.
No markdown fences, no extra text, no labels — just the JSON array.
Example format: ["shot2 prompt here", "shot3 prompt here", "shot4 prompt here"]
"""

        response = prompt_model.generate_content(var_prompt)
        raw      = response.text.strip()

        # Clean markdown fences if Gemini wraps in ```json
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("["):
                    raw = part
                    break

        raw     = raw.strip()
        prompts = json.loads(raw)

        if not isinstance(prompts, list) or len(prompts) != 3:
            raise ValueError(f"Expected list of 3, got: {raw[:200]}")

        for i, p in enumerate(prompts, 2):
            print(f"  Shot {i}: {p[:90]}…")

        return jsonify({"success": True, "prompts": prompts})

    except Exception as e:
        print(f"[ERROR] variations: {e}")
        return jsonify({"success": False, "error": str(e)})


# ==================================================
# ROUTE 3 — Generate Single Image (FLUX.1-dev)
# ==================================================
@app.route("/generate-image", methods=["POST"])
def generate_image():
    try:
        data   = request.get_json()
        prompt = data.get("prompt", "").strip()
        width  = int(data.get("width",  IMAGE_WIDTH))
        height = int(data.get("height", IMAGE_HEIGHT))
        steps  = int(data.get("steps",  HF_STEPS))
        index  = int(data.get("index",  1))

        print(f"\n=== FLUX: SHOT {index}/4  {width}x{height}  {steps}steps ===")
        print(f"Prompt: {prompt[:120]}…")

        if not prompt:
            return jsonify({"success": False, "error": "Empty prompt."})

        client    = InferenceClient(model=HF_MODEL, token=HF_TOKEN)
        generated = client.text_to_image(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=HF_GUIDANCE,
            width=width,
            height=height,
        )

        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid       = uuid.uuid4().hex[:6]
        filename  = f"shot{index:02d}_{ts}_{uid}.png"
        save_path = Path(OUTPUT_FOLDER) / filename
        generated.save(save_path)
        print(f"✅ Saved → {save_path}")

        buf = io.BytesIO()
        generated.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        return jsonify({"success": True, "saved_path": str(save_path), "image_b64": b64})

    except Exception as e:
        print(f"[ERROR] FLUX shot {index}: {e}")
        return jsonify({"success": False, "error": str(e)})


# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  AI Brand Video Pack Generator")
    print(f"{'='*50}")
    print(f"  Output  : {OUTPUT_FOLDER}")
    print(f"  Model   : {HF_MODEL}")
    print(f"  Steps   : {HF_STEPS} default | Guidance: {HF_GUIDANCE}")
    print(f"  URL     : http://localhost:5000")
    print(f"{'='*50}\n")
    app.run(debug=True, host="0.0.0.0",port=True)
