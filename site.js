(function () {
  // Note references: open the note in a sheet at the bottom of the screen.
  var sheet = document.getElementById("sheet");
  if (sheet) {
    var body = sheet.querySelector(".sheet-body");
    var close = function () { sheet.hidden = true; };
    sheet.querySelector(".sheet-x").addEventListener("click", close);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("sup.nref a");
      if (!a) {
        if (!sheet.hidden && !e.target.closest(".sheet-in")) close();
        return;
      }
      var n = a.getAttribute("data-n");
      var li = document.getElementById("n" + n);
      if (!li) return;
      e.preventDefault();
      var txt = li.querySelector(".ntext").cloneNode(true);
      txt.querySelectorAll(".back").forEach(function (b) { b.remove(); });
      body.innerHTML = "";
      var h = document.createElement("span"); h.className = "sh-n"; h.textContent = "Note " + n;
      body.appendChild(h);
      body.appendChild(txt);
      var go = document.createElement("a"); go.className = "sh-go"; go.href = "#n" + n; go.textContent = "Go to the notes";
      go.addEventListener("click", close);
      body.appendChild(go);
      sheet.hidden = false;
    });
  }

  // Images: open the full-size version in a viewer; tap the image to see it at full resolution.
  var lb = document.getElementById("lightbox");
  if (lb) {
    var scroll = lb.querySelector(".lb-scroll");
    var img = scroll.querySelector("img");
    var shut = function () { lb.hidden = true; img.removeAttribute("src"); scroll.classList.remove("big"); document.body.style.overflow = ""; };
    lb.querySelector(".lb-x").addEventListener("click", shut);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !lb.hidden) shut(); });
    img.addEventListener("click", function () { scroll.classList.toggle("big"); });
    document.querySelectorAll("a.zoom").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var small = a.querySelector("img");
        img.alt = small ? small.alt : "";
        img.src = a.getAttribute("data-full");
        lb.hidden = false;
        document.body.style.overflow = "hidden";
        lb.querySelector(".lb-x").focus();
      });
    });
  }
})();
