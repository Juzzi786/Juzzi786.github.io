/*
 * Progressive enhancement only. Every section, link, project detail panel and
 * contact action in the markup works with this file absent — the expandable
 * project panels are native <details>, and smooth scrolling is CSS.
 *
 * This adds three things:
 *   1. the mobile navigation drawer
 *   2. active-section highlighting in the desktop nav
 *   3. a copy-to-clipboard control for the email address
 */

(function () {
  "use strict";

  /* --------------------------------------------------------------------- *
   * 1. Mobile navigation drawer
   * --------------------------------------------------------------------- */

  var toggle = document.querySelector("[data-nav-toggle]");
  var drawer = document.getElementById("nav-drawer");

  if (toggle && drawer) {
    var setDrawer = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      drawer.hidden = !open;
      document.body.classList.toggle("is-locked", open);
      toggle.querySelector("[data-nav-toggle-text]").textContent = open
        ? "Close"
        : "Menu";
    };

    setDrawer(false);

    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") !== "true";
      setDrawer(open);
      if (open) {
        var first = drawer.querySelector("a, button");
        if (first) first.focus();
      }
    });

    // Close on selection, on Escape, and when the viewport grows to desktop.
    drawer.addEventListener("click", function (event) {
      if (event.target.closest("a")) setDrawer(false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !drawer.hidden) {
        setDrawer(false);
        toggle.focus();
      }
    });

    var desktop = window.matchMedia("(min-width: 62rem)");
    var onBreakpoint = function (event) {
      if (event.matches) setDrawer(false);
    };
    if (typeof desktop.addEventListener === "function") {
      desktop.addEventListener("change", onBreakpoint);
    }

    // Keep focus inside the drawer while it is open.
    drawer.addEventListener("keydown", function (event) {
      if (event.key !== "Tab") return;
      var focusable = drawer.querySelectorAll("a[href], button:not([disabled])");
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  /* --------------------------------------------------------------------- *
   * 2. Active-section highlighting
   * --------------------------------------------------------------------- */

  var navLinks = Array.prototype.slice.call(
    document.querySelectorAll("[data-nav-link]")
  );

  if (navLinks.length) {
    // Pair each link with its section, in document order.
    var spies = [];
    navLinks.forEach(function (link) {
      var section = document.getElementById(
        link.getAttribute("href").replace("#", "")
      );
      if (section) spies.push({ link: link, section: section });
    });

    var current = null;

    var sync = function () {
      // The section the reader is actually looking at is the last one whose
      // top has passed just below the sticky header.
      var line = window.scrollY + window.innerHeight * 0.32;
      var active = null;

      for (var i = 0; i < spies.length; i++) {
        if (spies[i].section.getBoundingClientRect().top + window.scrollY <= line) {
          active = spies[i];
        }
      }

      // Anything at the very bottom of the page belongs to the last section.
      if (
        window.innerHeight + window.scrollY >=
        document.documentElement.scrollHeight - 2
      ) {
        active = spies[spies.length - 1];
      }

      if (active === current) return;
      current = active;
      spies.forEach(function (spy) {
        if (spy === active) {
          spy.link.setAttribute("aria-current", "true");
        } else {
          spy.link.removeAttribute("aria-current");
        }
      });
    };

    var queued = false;
    var onScroll = function () {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () {
        queued = false;
        sync();
      });
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    sync();
  }

  /* --------------------------------------------------------------------- *
   * 3. Copy email
   * --------------------------------------------------------------------- */

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-copy]"),
    function (button) {
      var value = button.getAttribute("data-copy");
      var status = document.getElementById(
        button.getAttribute("data-copy-status")
      );

      // Without clipboard access the control would do nothing, so remove it
      // rather than leave a button that lies about what it does.
      if (!navigator.clipboard || !window.isSecureContext) {
        button.remove();
        return;
      }

      button.addEventListener("click", function () {
        navigator.clipboard.writeText(value).then(
          function () {
            if (status) status.textContent = "Copied";
            button.setAttribute("aria-label", "Email address copied");
            window.setTimeout(function () {
              if (status) status.textContent = "";
              button.removeAttribute("aria-label");
            }, 2400);
          },
          function () {
            if (status) status.textContent = "Press Ctrl/Cmd+C to copy";
          }
        );
      });
    }
  );

  /* --------------------------------------------------------------------- *
   * 4. Current year in the footer
   * --------------------------------------------------------------------- */

  var year = document.querySelector("[data-year]");
  if (year) year.textContent = String(new Date().getFullYear());
})();
