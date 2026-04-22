def clean_text(text):
    # basic cleaning
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.strip()
    return text