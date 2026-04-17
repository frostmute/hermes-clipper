document.getElementById('clipBtn').addEventListener('click', () => sendToBridge('/clip'));
document.getElementById('agentBtn').addEventListener('click', () => sendToBridge('/agent/clip'));

async function sendToBridge(endpoint) {
  const status = document.getElementById('status');
  status.textContent = "Working...";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Get content from content script
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({
        url: window.location.href,
        title: document.title,
        content: document.body.innerText
      })
    });

    const pageData = results[0].result;

    const body = endpoint === '/clip' 
      ? JSON.stringify({
          url: pageData.url,
          title: pageData.title,
          content: pageData.content,
          tags: ["web-clip"]
        })
      : JSON.stringify({
          url: pageData.url,
          prompt: "Research and clip this page."
        });

    const response = await fetch(`http://127.0.0.1:8088${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body
    });

    const data = await response.json();
    if (data.status === 'success') {
      status.textContent = "Done! Check Obsidian.";
    } else {
      status.textContent = "Error: " + data.message;
    }
  } catch (err) {
    status.textContent = "Failed to connect to bridge.";
    console.error(err);
  }
}
