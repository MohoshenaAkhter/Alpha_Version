# Emotion-Driven Cinematic Scene Engine

Type how you feel in plain language and the app turns that feeling into a
short cinematic scene — an emotion label, a 2–3 sentence scene, a camera
style, a lighting note, a 3-colour palette, and a matching image. Every
scene can be saved to a personal history and revisited later.

The project ships as **two front-ends sharing one backend**:

- **Desktop app** built with Tkinter — `python main.py`
- **Web app** built with Flask — `python app.py` and open
  `http://127.0.0.1:5000`

Both write to the same `scenes.csv` and share the same generated-image
cache, so you can produce a scene in one and view it in the other.

## Who it's for

People who use writing or moodboarding as part of their thinking:
creative writers stuck on a scene, film students wanting fast prompts,
designers playing with palettes, or anyone who wants a more interesting
way to journal a mood than a plain text note.

## How it works

1. The user's text is sent to the **Groq API** (Llama 3.3 70B). The
   model is asked for a strict JSON object with six fields: emotion,
   scene, camera style, lighting, three hex colours, and a separate
   image prompt written for an image-generation model.
2. That image prompt is sent to **Cloudflare Workers AI**
   (FLUX-1-schnell), which returns a square cinematic image.
3. Each generated image is cached on disk under `scenes/images/` by a
   hash of its prompt, so the same prompt isn't paid for twice.
4. The UI (Tkinter or browser) displays the scene fields, fills three
   colour swatches with the hex codes, and shows the image. Clicking
   the image opens it full-size in both versions — a popup window in
   the desktop app, a lightbox overlay in the browser. The web app
   also shows a spinner while it waits for the model.
5. **Save Scene** appends the scene and the image path to
   `scenes.csv`. **View History** reads the CSV back and draws a bar
   chart of how often each emotion has come up.

## Project layout

```
Alpha_Version/
├── main.py             # Desktop entry point — calls ui.run()
├── ui.py               # Tkinter UI: input, scene panel, swatches,
│                       # image panel with click-to-enlarge, history
├── app.py              # Flask web app: /, /generate, /save, /history,
│                       # and a route that serves cached images
├── templates/
│   ├── index.html      # Main page of the web app (form + result)
│   └── history.html    # Past scenes + bar chart
├── static/
│   └── style.css       # Shared styling for the web pages
├── ai_engine.py        # Sends prompt to Groq, parses the JSON response,
│                       # handles short / ambiguous inputs separately
├── image_engine.py     # Talks to Cloudflare Workers AI; on-disk cache
├── data_handler.py     # Reads / writes scenes.csv; migrates older
│                       # alpha CSVs that don't yet have image_path
├── stats.py            # Bar chart of emotion frequencies. Has a
│                       # Tkinter-friendly version and a base64 version
│                       # for the web app to embed
├── config.py           # Model name, CSV path, Groq key (from env)
├── requirements.txt    # External Python packages
└── .gitignore
```

The backend modules (`ai_engine`, `image_engine`, `data_handler`,
`stats`) know nothing about Tkinter or Flask. That's what lets the two
front-ends sit on top of the same code without duplicating logic.

## Setup

You will need Python 3.10+ and three accounts, all of them with a free
tier:

- **Groq** for the text model — https://console.groq.com/keys
- **Cloudflare** for the image model — https://dash.cloudflare.com
  - Account ID is shown in the URL after you sign in.
  - Create an API token: My Profile → API Tokens → Create Token →
    "Custom token" with `Account` → `Workers AI` → `Edit` permission.

### Install

```bash
git clone <this repo>
cd Alpha_Version
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure the keys

The app reads three environment variables. None of them is ever stored
in code or in the repo.

```bash
export GROQ_API_KEY="gsk_..."
export CLOUDFLARE_ACCOUNT_ID="..."        # 32-character hex from the dashboard URL
export CLOUDFLARE_API_TOKEN="..."         # the token you just created
```

To keep them across terminal sessions, add the three `export` lines to
`~/.zshrc` (or `~/.bashrc`) and run `source ~/.zshrc`.

### Run the desktop app

```bash
python main.py
```

A window titled "Emotion-Driven Cinematic Scene Engine" opens. Type how
you're feeling, click **Generate Scene**, wait a few seconds, and the
scene and image appear.

### Run the web app

```bash
python app.py
```

Flask starts on http://127.0.0.1:5000. Open that in any browser. The
form is the same idea as the desktop app, but it works without Python
installed on the user's side — anyone on your network can hit the URL.

## Using the app

1. Type a sentence in the input box. It can be vague ("fine", "ok") or
   specific ("I miss my grandmother's kitchen").
2. Click **Generate Scene** (or press **Cmd/Ctrl+Enter** in the
   desktop app). The button shows "Generating…" while it waits for
   the model; the web app also shows a spinner.
3. The output panel fills in:
   - **Emotion** — one or two words
   - **Scene** — 2 or 3 sentences with a concrete subject and at least
     one sensory detail
   - **Camera style** — e.g. *slow tracking shot*, *low-angle close-up*
   - **Lighting** — e.g. *soft golden backlight*, *blue hour window*
   - **Colour palette** — three swatches with their hex codes
   - **Image** — a square image rendered to match the scene. Click it
     to see it bigger (popup window on the desktop, lightbox overlay
     on the web).
4. **Save Scene** writes the result to `scenes.csv` along with the
   image path.
5. **View History** in the desktop app pops up a matplotlib bar chart.
   On the web app, **View History** is a full page that lists every
   saved scene with its timestamp and shows the same bar chart inline.

## How errors are handled

The app tries to give a clear, actionable message instead of a Python
traceback.

**Groq (text generation):**

| Cause | Message shown |
|---|---|
| Missing or invalid API key | `Authentication failed. Please check your GROQ_API_KEY.` |
| Rate limit hit | `Rate limit reached. Please wait a moment and try again.` |
| No internet | `Could not reach the Groq service. Check your internet connection.` |
| JSON the model returned can't be parsed | `The model returned a response that could not be parsed as JSON.` |
| Anything else | `Unexpected error: ...` |

**Cloudflare (image generation):**

| Cause | Message shown |
|---|---|
| Missing or wrong CLOUDFLARE_API_TOKEN | `Cloudflare authentication failed. Check CLOUDFLARE_API_TOKEN.` |
| Daily quota exhausted | `Daily Cloudflare AI quota reached. Try again tomorrow.` |
| Timeout | `Image generation timed out. Try again in a moment.` |
| No internet | `Could not reach the image service. Check your connection.` |

If the image fails, the scene itself is still shown — it just carries a
short note in place of the image. Nothing in the app ever crashes
silently.

## Where files end up

| Path | What's in it | Tracked in git? |
|---|---|---|
| `scenes.csv` | One row per saved scene | No (gitignored) |
| `scenes/images/*.jpg` | Cached generated images | No (gitignored) |
| `venv/` | Virtual environment | No (gitignored) |

You can delete `scenes.csv` and `scenes/images/` at any time; the app
will just start fresh.

## Requirements

```
groq>=1.2.0
pandas>=2.0.0
matplotlib>=3.7.0
requests>=2.31.0
Pillow>=10.0.0
flask>=3.0.0
```

- `groq` — talks to the Groq API
- `pandas` — CSV history
- `matplotlib` — the emotion bar chart (uses the `Agg` non-interactive
  backend so it works under Flask without a display)
- `requests` — HTTP calls to Cloudflare
- `Pillow` — opens, resizes and displays JPEG images in the desktop UI
- `flask` — the web app

## Authors

- **Zeynep Kesim** — prompt design and scene quality, image-generation
  integration with Cloudflare Workers AI, schema design, error
  handling, the desktop UI and the layout polish.
- **Mohoshena Akhter** — the Flask web version (routes, templates,
  static files), and the `stats.py` refactor that lets the same chart
  serve both the desktop window and the web page.

## AI Usage Disclosure

In line with the principles of academic transparency, this section
documents the role of AI tools in the development of this project.

AI assistance was used in a supporting capacity for the following
purposes:

- **Language polishing.** Reviewing and refining the wording of inline
  comments, the user-facing messages displayed by the UI, and the prose
  of this README to improve clarity, grammar, and tone.
- **Documentation drafting.** Generating an initial outline of the
  README structure (sections, ordering), which was then edited and
  finalised by the authors.
- **Minor code-level suggestions.** Occasional suggestions for small
  refinements such as variable naming consistency and formatting
  choices.

All AI-generated content was reviewed, edited, and approved before being
included.
