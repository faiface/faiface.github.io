// Theme toggle: the initial theme is set inline in <head> to avoid a flash; this only handles changes.
(function () {
  const root = document.documentElement;
  const button = document.querySelector(".theme-toggle");
  const system = window.matchMedia("(prefers-color-scheme: dark)");

  const saved = () => {
    try {
      return localStorage.getItem("theme");
    } catch (e) {
      return null;
    }
  };

  if (button) {
    button.addEventListener("click", () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        localStorage.setItem("theme", next);
      } catch (e) {}
    });
  }

  // Follow the system setting until the reader picks a theme themselves.
  system.addEventListener("change", (e) => {
    if (!saved()) root.dataset.theme = e.matches ? "dark" : "light";
  });
})();

// Copy buttons on code blocks.
(function () {
  if (!navigator.clipboard) return;
  document.querySelectorAll(".post-content pre").forEach((pre) => {
    const code = pre.querySelector("code");
    if (!code) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    button.textContent = "Copy";
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.innerText);
        button.textContent = "Copied";
      } catch (e) {
        button.textContent = "Failed";
      }
      setTimeout(() => (button.textContent = "Copy"), 1500);
    });
    (pre.closest(".highlight") || pre).append(button);
  });
})();
