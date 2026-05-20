(function () {
  try {
    var t = localStorage.getItem("theme");
    if (t === "default") {
      localStorage.setItem("theme", "dark");
      t = "dark";
    }
    document.documentElement.setAttribute("data-theme", t === "light" ? "light" : "dark");
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
})();
