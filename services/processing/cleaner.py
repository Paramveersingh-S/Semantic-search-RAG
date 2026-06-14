import re

def clean_text(text: str) -> str:
    """
    Apply document cleaning: remove boilerplate, normalize whitespace, etc.
    """
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove non-ascii characters if necessary
    text = text.encode("ascii", "ignore").decode()
    return text.strip()
