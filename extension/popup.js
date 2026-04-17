document.getElementById('clipBtn').addEventListener('click', () => sendToBridge('/clip'));
document.getElementById('agentBtn').addEventListener('click', () => sendToBridge('/agent/clip'));

async function sendToBridge(endpoint) {
  const status = document.getElementById('status');
  const btn = endpoint === '/clip' ? document.getElementById('clipBtn') : document.getElementById('agentBtn');
  
  // Quick hack: Get API Key from localStorage (User must set this once in console or we add an input later)
  const apiKey = localStorage.getItem('hermes_api_key');
  if (!apiKey) {
    status.textContent = "Set 'hermes_api_key' in localStorage.";
    return;
  }

  status.textContent = "Hermes is busy...";
  btn.classList.add('pulse');

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
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
      ? JSON.stringify({ url: pageData.url, title: pageData.title, content: pageData.content, tags: ["web-clip"] })
      : JSON.stringify({ url: pageData.url, prompt: "Research and clip." });

    const response = await fetch(`http://127.0.0.1:8088${endpoint}`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: body
    });

    const data = await response.json();
    if (data.status === 'accepted') {
      pollTask(data.task_id, btn, apiKey);
    } else if (data.status === 'success') {
      status.textContent = "Done. Don't expect a medal.";
      btn.classList.remove('pulse');
    } else {
      status.textContent = "Rejected: " + (data.detail || data.message);
      btn.classList.remove('pulse');
    }
  } catch (err) {
    status.textContent = "Bridge missing. Wake it up.";
    btn.classList.remove('pulse');
  }
}

async function pollTask(taskId, btn, apiKey) {
  const status = document.getElementById('status');
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8088/tasks/${taskId}`, {
        headers: { 'X-API-Key': apiKey }
      });
      const task = await response.json();
      if (task.status === 'completed') {
        status.textContent = "Finished. You're welcome.";
        btn.classList.remove('pulse');
        clearInterval(interval);
      } else if (task.status === 'failed') {
        status.textContent = "I failed. Blame the internet.";
        btn.classList.remove('pulse');
        clearInterval(interval);
      }
    } catch (err) {
      clearInterval(interval);
    }
  }, 3000);
}
