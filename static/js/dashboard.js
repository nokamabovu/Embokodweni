// Staff dashboard: checks for new notifications every 30 seconds,
// updates the bell and shows a pop-up when something new arrives.
(function () {
  var api = document.body.dataset.api;
  if (!api) return;

  var bell = document.getElementById("bell");
  var count = document.getElementById("bell-count");
  var list = document.getElementById("bell-list");
  var toasts = document.getElementById("toasts");
  var baseTitle = document.title;
  var lastId = null;

  function esc(text) {
    var d = document.createElement("div");
    d.textContent = text || "";
    return d.innerHTML;
  }

  function showToast(item) {
    var t = document.createElement("a");
    t.className = "toast";
    t.href = item.url;
    t.innerHTML = "<b>" + esc(item.title) + "</b><small>" + esc(item.body) + "</small>";
    toasts.appendChild(t);
    setTimeout(function () { t.remove(); }, 9000);
  }

  function update(data) {
    // bell number and tab title
    count.textContent = data.count;
    count.hidden = data.count === 0;
    document.title = (data.count ? "(" + data.count + ") " : "") + baseTitle;
    document.querySelectorAll(".js-unread").forEach(function (el) { el.textContent = data.count; });

    // dropdown list
    if (data.items.length) {
      list.innerHTML = data.items.map(function (n) {
        return '<li class="' + (n.is_read ? "" : "new") + '"><a href="' + n.url + '"><b>' + esc(n.title) +
          "</b><span>" + esc(n.body) + "</span><small>" + esc(n.ago) + "</small></a></li>";
      }).join("");
    }

    // pop-ups for anything newer than last time
    if (lastId !== null && data.latest_id > lastId) {
      data.items.filter(function (n) { return n.id > lastId; }).reverse().forEach(showToast);
      bell.classList.remove("ring");
      void bell.offsetWidth;
      bell.classList.add("ring");
    }
    lastId = data.latest_id;
  }

  function poll() {
    fetch(api, { headers: { "Accept": "application/json" }, credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data) update(data); })
      .catch(function () {});
  }

  poll();
  setInterval(poll, 30000);

  // close the bell when clicking elsewhere
  document.addEventListener("click", function (e) {
    if (bell.open && !bell.contains(e.target)) bell.open = false;
  });
})();
