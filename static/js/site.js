// Embokodweni Lifestyle: scroll animations.
// Sections fade up as they come into view. Without JavaScript, or for people
// who prefer reduced motion, everything simply shows as normal.
(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) return;

  document.documentElement.classList.add("js-anim");

  var selectors = [
    ".sec-head", ".svc-card", ".why-item", ".track", ".lineup li", ".dates li",
    ".trio a", ".single", ".find-grid", ".steps li", ".quotes blockquote",
    ".pitch", ".values span", ".mission li", ".motto", ".sheet a", ".contact-card",
    ".about .copy", ".book .side", ".enquiry", ".bookband .wrap > *", ".ex-card", ".visit .wrap > *", ".row", ".contact-list div", ".wday", ".soon"
  ];
  var items = document.querySelectorAll(selectors.join(","));

  items.forEach(function (el) {
    el.classList.add("reveal");
    // small stagger for items that sit side by side
    var siblings = Array.prototype.indexOf.call(el.parentNode.children, el);
    el.style.transitionDelay = Math.min(siblings, 5) * 80 + "ms";
  });

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.01 });

  items.forEach(function (el) { observer.observe(el); });

  // Safety net: once the visitor reaches the bottom, show anything left.
  function showRest() {
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 80) {
      items.forEach(function (el) { el.classList.add("in"); });
      window.removeEventListener("scroll", showRest);
    }
  }
  window.addEventListener("scroll", showRest, { passive: true });
  // And never leave content hidden for long (e.g. a printed or saved page)
  setTimeout(function () { items.forEach(function (el) { el.classList.add("in"); }); }, 6000);
})();

// ---------------------------------------------------------------
// Availability checks
// Home page bar: checks the date without leaving the page.
// Booking page: checks again whenever the date or guests change.
// Without JavaScript both still work through the normal page.
// ---------------------------------------------------------------
(function () {
  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function askBlock(data, sendHtml) {
    if (!data.can_ask) return "";
    var ask = data.ask || {};
    var html = '<div class="ask"><span>Only part of the venue may be booked. Ask us if there\'s still space:</span><span class="ask-actions">';
    if (ask.dial) html += '<a class="ask-btn" href="tel:' + ask.dial + '">Call ' + escapeHtml(ask.phone) + "</a>";
    if (ask.whatsapp_url) html += '<a class="ask-btn" href="' + ask.whatsapp_url + '" target="_blank" rel="noopener">WhatsApp us</a>';
    return html + sendHtml + "</span></div>";
  }

  function fetchAvailability(url, date, guests, type) {
    var query = "?date=" + encodeURIComponent(date) + (guests ? "&guests=" + encodeURIComponent(guests) : "") + (type ? "&type=" + encodeURIComponent(type) : "");
    return fetch(url + query, { headers: { "Accept": "application/json" } }).then(function (r) { return r.json(); });
  }

  // ----- Home page bar -----
  var bar = document.getElementById("avail-bar");
  var box = document.getElementById("avail-result");
  if (bar && box) {
    bar.addEventListener("submit", function (e) {
      var date = bar.elements["date"].value;
      if (!date) {
        e.preventDefault();
        box.hidden = false;
        box.className = "avail-result no";
        box.innerHTML = "<strong>Choose a date first.</strong>";
        bar.elements["date"].focus();
        return;
      }
      e.preventDefault();
      var type = bar.elements["type"].value;
      var guests = bar.elements["guests"].value;
      var button = bar.querySelector("button");
      button.disabled = true;
      button.textContent = "Checking...";

      fetchAvailability(bar.dataset.availabilityUrl, date, guests, type).then(function (data) {
        box.hidden = false;
        var bookUrl = bar.action + "?type=" + encodeURIComponent(type) + "&guests=" + encodeURIComponent(guests || "");
        if (data.error) {
          box.className = "avail-result no";
          box.innerHTML = "<strong>" + escapeHtml(data.error) + "</strong>";
        } else if (data.available) {
          box.className = "avail-result yes";
          box.innerHTML = "<strong>" + escapeHtml(data.message) + "</strong>" +
            '<a class="avail-book" href="' + bookUrl + "&date=" + data.date + '">Book this date</a>';
        } else {
          var html = "<strong>" + escapeHtml(data.message) + "</strong>";
          if (data.alternatives.length) {
            html += '<span class="alt-label">Next free dates:</span><span class="alts">';
            data.alternatives.forEach(function (a) {
              html += '<a class="alt" href="' + bookUrl + "&date=" + a.date + '">' + escapeHtml(a.label) + "</a>";
            });
            html += "</span>";
          }
          html += askBlock(data, '<a class="ask-btn" href="' + bookUrl + "&date=" + data.date + '&ask=1">Ask about this date</a>');
          box.className = "avail-result no";
          box.innerHTML = html;
        }
      }).catch(function () {
        bar.submit();  // fall back to the booking page
      }).finally(function () {
        button.disabled = false;
        button.textContent = "Check availability";
      });
    });
  }

  // ----- Booking page -----
  var form = document.querySelector(".booking-form");
  var note = document.getElementById("avail-note");
  if (form && note) {
    var dateInput = form.elements["event_date"];
    var guestsInput = form.elements["guests"];
    var typeInput = form.elements["event_type"];
    var askInput = document.getElementById("id_ask");
    var askBanner = document.getElementById("ask-banner");
    var submitBtn = document.getElementById("book-submit");

    function setAsking(on) {
      askInput.value = on ? "1" : "0";
      askBanner.hidden = !on;
      submitBtn.textContent = on ? "Send my question" : "Send booking";
    }

    function render(data) {
      if (data.error) { note.innerHTML = ""; return; }
      var html = '<div class="avail ' + (data.available ? "yes" : "no") + '"><strong>' + escapeHtml(data.message) + "</strong>";
      if (!data.available && data.alternatives.length) {
        html += '<span class="alt-label">Next free dates:</span><span class="alts">';
        data.alternatives.forEach(function (a) {
          html += '<button type="button" class="alt" data-date="' + a.date + '">' + escapeHtml(a.label) + "</button>";
        });
        html += "</span>";
      }
      html += askBlock(data, '<button type="button" class="ask-btn ask-send">Ask about this date</button>');
      note.innerHTML = html + "</div>";
      if (data.available) setAsking(false);
    }

    function check() {
      if (!dateInput.value) { note.innerHTML = ""; return; }
      fetchAvailability(form.dataset.availabilityUrl, dateInput.value, guestsInput.value, typeInput.value).then(render).catch(function () {});
    }

    dateInput.addEventListener("change", check);
    guestsInput.addEventListener("change", check);

    // Clicking a suggested date fills it in and checks again
    note.addEventListener("click", function (e) {
      if (e.target.closest(".ask-send")) {
        setAsking(true);
        form.elements["name"].focus();
        askBanner.scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }
      var alt = e.target.closest(".alt");
      if (!alt) return;
      dateInput.value = alt.dataset.date;
      check();
    });
  }
})();

// Hidden staff entrance: tap the footer logo 3 times quickly,
// or press and hold it for 1.5 seconds on a phone.
(function () {
  var logo = document.querySelector(".foot-logo[data-staff]");
  if (!logo) return;
  var taps = 0, timer = null, hold = null, held = false;
  function go() { window.location.href = logo.dataset.staff; }
  logo.addEventListener("click", function (e) {
    if (held) { e.preventDefault(); held = false; return; }
    taps += 1;
    clearTimeout(timer);
    if (taps >= 3) { e.preventDefault(); taps = 0; go(); return; }
    if (taps > 1) e.preventDefault();
    timer = setTimeout(function () {
      if (taps === 1 || taps === 2) { window.location.href = logo.href; }
      taps = 0;
    }, 500);
    e.preventDefault();
  });
  logo.addEventListener("touchstart", function () {
    hold = setTimeout(function () { held = true; go(); }, 1500);
  }, { passive: true });
  ["touchend", "touchmove", "touchcancel"].forEach(function (ev) {
    logo.addEventListener(ev, function () { clearTimeout(hold); }, { passive: true });
  });
  logo.addEventListener("contextmenu", function (e) { if (held) e.preventDefault(); });
})();
