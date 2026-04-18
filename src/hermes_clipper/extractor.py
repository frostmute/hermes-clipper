from readability import Document
from markdownify import markdownify as md

def extract_content_to_markdown(html_content):
    """
    Extracts the main content from HTML and converts it to Markdown.
    Uses readability-lxml for content extraction and markdownify for conversion.
    """
    doc = Document(html_content)
    summary_html = doc.summary()
    
    # markdownify options:
    # heading_style="ATX" -> # H1, ## H2, etc.
    # bullets="-" -> use - for bullet points
    markdown = md(summary_html, heading_style="ATX", bullets="-")
    
    return markdown.strip()
