let savedTheme = null;
try {
  savedTheme = localStorage.getItem("urbero-theme");
} catch {
  // Storage can be unavailable in private sessions.
}
const dark = savedTheme === "dark" ||
  (savedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
document.documentElement.classList.toggle("dark", dark);
