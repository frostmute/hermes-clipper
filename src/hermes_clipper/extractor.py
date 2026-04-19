from readability import Document
from markdownify import markdownify as md

def extract_content_to_markdown(html_content):
    """
    Extracts the main content from HTML and converts it to Markdown.
    Uses readability-lxml for content extraction and markdownify for conversion.
    """
    try:
        doc = Document(html_content)
        summary_html = doc.summary()
        
        # If summary is very short, readability might have failed to find the main content
        if len(summary_html) < 200 and len(html_content) > 1000:
            # Fallback to a slightly more aggressive extraction or just use the whole body
            summary_html = html_content

        # markdownify options:
        # heading_style="ATX" -> # H1, ## H2, etc.
        # bullets="-" -> use - for bullet points
        markdown = md(summary_html, heading_style="ATX", bullets="-")
        
        return markdown.strip()
    except Exception:
        # Final fallback: just try to markdownify the raw input
        try:
            return md(html_content, heading_style="ATX", bullets="-").strip()
        except:
            return html_content
