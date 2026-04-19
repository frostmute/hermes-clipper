document.getElementById('clipBtn').addEventListener('click', () => sendToBridge('/clip'));
document.getElementById('agentBtn').addEventListener('click', () => sendToBridge('/agent/clip'));

// Auto-discovery of API Key via Native Messaging
window.addEventListener('DOMContentLoaded', async () => {
  const status = document.getElementById('status');
  const apiKey = localStorage.getItem('hermes_api_key');
  
  if (!apiKey) {
    status.textContent = "Syncing with Hermes...";
    try {
      chrome.runtime.sendNativeMessage('com.frostmute.hermes_clipper', { action: 'get_config' }, (response) => {
        if (chrome.runtime.lastError) {
          status.textContent = "Auto-sync failed. Set 'hermes_api_key' in localStorage.";
          return;
        }
        if (response && response.api_key) {
          localStorage.setItem('hermes_api_key', response.api_key);
          status.textContent = "Hermes Linked. Grunt.";
        } else {
          status.textContent = "Setup bridge via CLI first.";
        }
      });
    } catch (err) {
      status.textContent = "Set 'hermes_api_key' in localStorage.";
    }
  }
});

async function sendToBridge(endpoint) {
  const status = document.getElementById('status');
  const btn = endpoint === '/clip' ? document.getElementById('clipBtn') : document.getElementById('agentBtn');
  
  const apiKey = localStorage.getItem('hermes_api_key');
  if (!apiKey) {
    status.textContent = "API Key missing. Link Hermes first.";
    return;
  }

  status.textContent = "Hermes is busy...";
  btn.classList.add('pulse');

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const getMeta = (name) => {
          const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"], meta[property="og:${name}"], meta[property="twitter:${name}"]`);
          return el ? el.getAttribute('content') : '';
        };
        return {
          url: window.location.href,
          title: document.title,
          content: document.documentElement.outerHTML,
          metadata: {
            description: getMeta('description') || getMeta('og:description') || '',
            author: getMeta('author') || getMeta('article:author') || '',
            site_name: getMeta('site_name') || getMeta('og:site_name') || '',
            published_date: getMeta('published_time') || getMeta('article:published_time') || getMeta('date') || '',
            banner: getMeta('og:image') || getMeta('twitter:image') || ''
          }
        };
      }
    });

    const pageData = results[0].result;
    const body = endpoint === '/clip' 
      ? JSON.stringify({ 
          url: pageData.url, 
          title: pageData.title, 
          content: pageData.content, 
          tags: ["web-clip"],
          metadata: pageData.metadata
        })
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
    } else if (data.status === 'exists') {
      status.textContent = "Already exists. Stop hoarding.";
      btn.classList.remove('pulse');
    } else {
      let errorMessage = data.detail || data.message || data.error || `HTTP ${response.status}`;
      if (typeof errorMessage !== 'string') errorMessage = JSON.stringify(errorMessage);
      status.textContent = "Rejected: " + errorMessage;
      btn.classList.remove('pulse');
    }
  } catch (err) {
    status.textContent = "Bridge error: " + err.message;
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
