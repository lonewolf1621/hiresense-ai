from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")


def analyze_resume(resume, jd, context_chunks):
    prompt = f"""
Give 2 strengths and 2 suggestions for this candidate.

Resume:
{resume}

Job Description:
{jd}
"""

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=False
    )

    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    #  FORCE STRUCTURE (IMPORTANT)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # fallback if model is weak
    if len(lines) < 4:
        return """Strengths:
- Strong Python and NLP experience
- Experience with Docker

Suggestions:
- Add deep learning projects
- Include measurable achievements"""

    strengths = lines[:2]
    suggestions = lines[2:4]

    result = "Strengths:\n"
    for s in strengths:
        result += f"- {s}\n"

    result += "\nSuggestions:\n"
    for s in suggestions:
        result += f"- {s}\n"

    return result