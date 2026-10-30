(function () {
  "use strict";

  const BASE = "";
  const statusPill = document.getElementById("statusPill");
  const tickerInput = document.getElementById("tickerInput");
  const loadTickerBtn = document.getElementById("loadTickerBtn");
  const chat = document.getElementById("chat");
  const questionInput = document.getElementById("questionInput");
  const askBtn = document.getElementById("askBtn");

  let currentTicker = null;

  function setStatus(label, kind) {
    statusPill.textContent = "⏳ " + label;
    statusPill.className = "status-pill " + kind;
  }

  function clearChat() {
    chat.innerHTML = '<div class="empty-state">Ask a question once a company index is loaded.</div>';
  }

  function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "msg " + role;

    const p = document.createElement("p");
    p.textContent = text;

    div.appendChild(p);
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
  }

  // Assistant answers are markdown; rendered md.js output (already escaped).
  function addMessageMarkdown(markdownText) {
    const div = document.createElement("div");
    div.className = "msg assistant";

    const md = document.createElement("div");
    md.className = "md";
    if (window.mdToHtml) {
      md.innerHTML = mdToHtml(markdownText);
    } else {
      // Renderer failed to load: keep safe plain text.
      md.textContent = markdownText;
    }

    div.appendChild(md);
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
  }

  function addError(text) {
    const div = document.createElement("div");
    div.className = "msg assistant error";
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function addSources(sources) {
    const list = document.createElement("div");
    list.className = "sources";

    (sources || []).forEach(function (s) {
      const card = document.createElement("div");
      card.className = "source-card";

      const h = document.createElement("h4");
      h.textContent = s.section || s.ticker;

      const meta = document.createElement("p");
      const bits = [];
      if (s.ticker) bits.push(s.ticker);
      if (s.company) bits.push(s.company);
      if (s.filing_type) bits.push(s.filing_type);
      if (s.filing_date) bits.push(s.filing_date);
      if (s.chunk_id !== undefined) bits.push("chunk " + s.chunk_id);
      meta.textContent = bits.join(" · ") || "no metadata";

      const snippet = document.createElement("div");
      snippet.className = "snippet";
      snippet.textContent = s.text_preview || s.text || "(no text)";

      card.appendChild(h);
      card.appendChild(meta);
      card.appendChild(snippet);
      list.appendChild(card);
    });

    chat.appendChild(list);
  }

  function stopLoading() {
    setStatus("idle", "idle");
  }

  function setIndexing() {
    setStatus("indexing...", "indexing");
  }

  function setDone() {
    setStatus("ready", "done");
  }

  function showError(ev) {
    ev.preventDefault();
    addError("Failed to reach the backend. Is the FastAPI server running?");
    stopLoading();
  }

  function postJSON(path, body) {
    return fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (res) {
      if (!res.ok) {
        return res.json().then(function (j) {
          throw new Error(j.detail || "Request failed (" + res.status + ")");
        });
      }
      return res.json();
    });
  }

  function renderSources(sources) {
    if (!sources || sources.length === 0) {
      addMessage("assistant", "(no sources returned)");
      return;
    }
    addSources(sources);
  }

  function ask() {
    if (!currentTicker) {
      addError("Please load a company ticker first (e.g. AAPL).");
      tickerInput.focus();
      return;
    }

    const question = questionInput.value.trim();
    if (!question) return;

    addMessage("user", question);
    questionInput.value = "";
    askBtn.disabled = true;
    askBtn.textContent = "waiting...";

    setIndexing();

    postJSON("ask/" + encodeURIComponent(currentTicker), {
      question: question,
      identity_email: null,
    })
      .then(function (data) {
        addMessageMarkdown(data.answer || "(empty answer)");
        renderSources(data.sources || []);
      })
      .catch(function (err) {
        addError(err.message);
      })
      .finally(function () {
        askBtn.disabled = false;
        askBtn.textContent = "Ask";
      });
  }

  function loadTicker() {
    const ticker = tickerInput.value.trim().toUpperCase();
    if (!ticker) {
      addError("Enter a ticker first.");
      tickerInput.focus();
      return;
    }

    addMessage("assistant", "Loading / indexing " + ticker + "…");
    setIndexing();

    postJSON("ingest/" + encodeURIComponent(ticker), {
      question: "index this company",
      identity_email: null,
    })
      .then(function (data) {
        currentTicker = ticker;
        setDone();
        clearChat();
        addMessage("assistant", "Indexed " + ticker + " (" + (data.chunks || "unknown") + " chunks). You can now ask questions.");
      })
      .catch(function (err) {
        addError(err.message);
        stopLoading();
      });
  }

  loadTickerBtn.addEventListener("click", loadTicker);
  askBtn.addEventListener("click", ask);
  questionInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      ask();
    }
  });

  tickerInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      loadTicker();
    }
  });
})();
