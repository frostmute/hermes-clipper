import unittest
import json
from bs4 import BeautifulSoup
from .main import extract_json_ld, extract_content

class TestMetadata(unittest.TestCase):
    def test_extract_json_ld(self):
        html = """
        <html>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "author": {
                    "@type": "Person",
                    "name": "Jane Doe"
                },
                "datePublished": "2024-04-18",
                "description": "A test article"
            }
            </script>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        data = extract_json_ld(soup)
        self.assertEqual(data.get("author", {}).get("name"), "Jane Doe")
        self.assertEqual(data.get("datePublished"), "2024-04-18")
        self.assertEqual(data.get("description"), "A test article")

    def test_extract_content_live(self):
        # Testing on a live URL to verify real-world extraction
        url = "https://example.com"
        ext = extract_content(url)
        self.assertIn("Example Domain", ext["title"])
        self.assertIn("This domain is for use in documentation examples", ext["content"])
        self.assertEqual(ext["site_name"], "")

if __name__ == "__main__":
    unittest.main()
