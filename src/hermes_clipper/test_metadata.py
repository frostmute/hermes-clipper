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

    def test_clip_replacement(self):
        # Mocking clip functionality locally
        import datetime
        import re
        
        template = """---
title: "{{title}}"
desc: "{{ description }}"
author: "{{  author  }}"
site: "{{site_name}}"
missing: "{{ missing_field }}"
---
# {{title}}
{{content}}"""
        
        replacements = {
            "title": 'Test "Title" with Quotes',
            "description": "Test Desc with \\1 backreference",
            "author": "Jane Doe",
            "site_name": "My Site",
            "content": "Test Content with \\ backslash",
            "date": str(datetime.date.today())
        }
        
        rendered = template
        for k, v in replacements.items():
            pattern = re.compile(f"\\{{\\{{\\s*{re.escape(k)}\\s*\\}}\\}}")
            val = str(v)
            if isinstance(v, str):
                val = v.replace('"', '\\"')
            rendered = pattern.sub(lambda m, val=val: val, rendered)
            
        self.assertIn('title: "Test \\"Title\\" with Quotes"', rendered)
        self.assertIn('desc: "Test Desc with \\1 backreference"', rendered)
        self.assertIn('author: "Jane Doe"', rendered)
        self.assertIn('site: "My Site"', rendered)
        self.assertIn('missing: "{{ missing_field }}"', rendered)
        self.assertIn('Test Content with \\ backslash', rendered)

if __name__ == "__main__":
    unittest.main()
