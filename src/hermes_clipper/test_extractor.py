import unittest
from hermes_clipper.extractor import extract_content_to_markdown

class TestExtractor(unittest.TestCase):
    def test_extract_content_to_markdown(self):
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <div id="content">
                    <h1>Test Title</h1>
                    <p>This is a test paragraph with enough words to satisfy the readability algorithm and make it think this is a real article worth extracting. It needs to have some length and substance to be considered the main content of the page.</p>
                    <p>Here is a list of important items that should be preserved in the markdown conversion process:</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2</li>
                        <li>Item 3 with more text to make it look like a real list item</li>
                    </ul>
                    <p>Another paragraph here to ensure the list is sandwiched between text, which often helps readability algorithms identify it as part of the content body.</p>
                    <p>This is a <b>test</b> paragraph with <i>italics</i> as well.</p>
                </div>
            </body>
        </html>
        """
        markdown = extract_content_to_markdown(html_content)
        print(f"\n--- DEBUG MARKDOWN ---\n{markdown}\n--- END DEBUG ---")
        
        self.assertIn("# Test Title", markdown)
        self.assertIn("This is a **test** paragraph", markdown)
        self.assertIn("- Item 1", markdown)
        self.assertIn("- Item 2", markdown)
        self.assertIn("- Item 3", markdown)

if __name__ == "__main__":
    unittest.main()
