(function () {
  window.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".terminal-copy").forEach((button) => {
      button.addEventListener("click", async () => {
        const command = button.dataset.copy || "";
        const originalLabel = button.textContent;

        try {
          await navigator.clipboard.writeText(command);
          button.textContent = "Copied!";
        } catch (_) {
          const input = document.createElement("textarea");
          input.value = command;
          input.setAttribute("readonly", "");
          input.style.position = "fixed";
          input.style.opacity = "0";
          document.body.appendChild(input);
          input.select();
          document.execCommand("copy");
          input.remove();
          button.textContent = "Copied!";
        }

        window.setTimeout(() => {
          button.textContent = originalLabel;
        }, 1600);
      });
    });
  });
})();
