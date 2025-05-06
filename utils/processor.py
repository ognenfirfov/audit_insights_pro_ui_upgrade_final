import os
import fitz  # PyMuPDF
import tempfile
from openai import OpenAI, RateLimitError, APIError
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type((RateLimitError, APIError)))
def ask_openai(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

def extract_logo_image(pdf_path):
    doc = fitz.open(pdf_path)
    largest_image = None
    max_area = 0
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            path = os.path.join(tempfile.gettempdir(), f"logo_{xref}.{image_ext}")
            with open(path, "wb") as f:
                f.write(image_bytes)
            area = base_image.get("width", 0) * base_image.get("height", 0)
            if area > max_area:
                largest_image = path
                max_area = area
    return largest_image

def summarize_audit(text, filename):
    prompt = f"""You are a senior auditor. Provide a short, structured summary (max 1 page) with:
1. Audit Topic
2. Main Findings (2–3 bullets)
3. Measures Proposed (2–3 bullets)
4. Future Steps (2–3 bullets)

Audit file: {filename}
{text[:8000]}
"""
    return ask_openai(prompt)

def extract_theme_keywords(summary):
    prompt = f"Extract 4–6 audit themes as comma-separated list:\n\n{summary}"
    return [k.strip() for k in ask_openai(prompt).split(",") if k.strip()]

def compare_audits(summaries):
    return ask_openai("Compare these audit summaries:\n\n" + "\n\n".join(summaries))

def extract_learnings(summaries):
    return ask_openai("List 3–5 lessons from these audits:\n\n" + "\n\n".join(summaries))

def analyze_audits(pdf_paths, filenames):
    summaries, logos, themes = [], [], []
    for path, name in zip(pdf_paths, filenames):
        text = extract_text(path)
        summary = summarize_audit(text, name)
        summaries.append(summary)
        logos.append(extract_logo_image(path))
        themes.append(extract_theme_keywords(summary))
    return {
        "summaries": summaries,
        "logos": logos,
        "themes": themes,
        "comparison": compare_audits(summaries),
        "learnings": extract_learnings(summaries)
    }
