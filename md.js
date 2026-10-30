// Tiny markdown renderer (no dependencies).
// Supports: headings (#..######), bold **x**, italic *x*, inline code `x`,
// bullet/numbered lists, paragraphs. Escapes HTML first, so output is safe.
// Exposed as a global (mdToHtml) for browsers and CommonJS for tests.

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.mdToHtml = factory().mdToHtml;
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Inline transforms applied AFTER escaping.
  function inline(t) {
    t = escapeHtml(t);
    // bold: **text**
    t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // italic: *text* — only when not already inside a strong tag pair
    t = t.replace(/(^|[\s("'])\*(?!\s)([^*]+?)(?<!\s)\*(?=[\s).,;:!?"']|$)/g,
      "$1<em>$2</em>");
    // inline code: `x`
    t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
    return t;
  }

  function mdToHtml(md) {
    if (md === null || md === undefined) return "";
    const lines = String(md).replace(/\r\n/g, "\n").split("\n");

    let html = "";
    let listOpen = false;
    let para = [];

    function flushPara() {
      if (para.length) {
        html += "<p>" + inline(para.join(" ")) + "</p>";
        para = [];
      }
    }

    function closeList() {
      if (listOpen) {
        html += "</ul>";
        listOpen = false;
      }
    }

    for (const raw of lines) {
      const line = raw.replace(/\s+$/, "");

      // blank line -> end paragraph and list
      if (line.trim() === "") {
        flushPara();
        closeList();
        continue;
      }

      // bullet list: -, *, •, or numbered 1. / 1)
      const li = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
      if (li) {
        flushPara();
        if (!listOpen) {
          html += "<ul>";
          listOpen = true;
        }
        html += "<li>" + inline(li[1]) + "</li>";
        continue;
      }

      // headings # .. ######
      const h = line.match(/^(#{1,6})\s+(.*)$/);
      if (h) {
        flushPara();
        closeList();
        const level = h[1].length;
        html += "<h" + level + ">" + inline(h[2].trim()) + "</h" + level + ">";
        continue;
      }

      para.push(line.trim());
    }

    flushPara();
    closeList();
    return html;
  }

  return { mdToHtml: mdToHtml, escapeHtml: escapeHtml };
});
