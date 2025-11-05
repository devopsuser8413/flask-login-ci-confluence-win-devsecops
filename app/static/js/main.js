// ============================================
// 🧠 Secure Flask Frontend Helper
// ============================================

// Prevent autofill leaks and log safe startup
document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ Flask Secure App Loaded Successfully");

  // Disable right-click context menu for demo hardening
  document.addEventListener("contextmenu", (e) => e.preventDefault());

  // Optional: Simple client-side username validation
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", (e) => {
      const username = document.querySelector("#username");
      if (username && username.value.match(/[<>\"']/)) {
        alert("Invalid characters in username!");
        e.preventDefault();
      }
    });
  }
});
