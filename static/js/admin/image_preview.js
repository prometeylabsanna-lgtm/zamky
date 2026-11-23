(() => {
  const setPreviewImg = (box, url, maxSize) => {
    if (!box) return;
    let img = box.querySelector("img");
    if (!img) {
      box.textContent = "";
      img = document.createElement("img");
      img.alt = "";
      img.loading = "lazy";
      img.decoding = "async";
      box.appendChild(img);
    }
    img.src = url;
    img.style.maxWidth = `${maxSize}px`;
    img.style.maxHeight = `${maxSize}px`;
  };

  const previewBoxFor = (input) => {
    const name = input.name || "";
    const short = name.split("-").pop();
    if (!short) return null;
    const row = document.querySelector(`.field-${short}_preview`);
    return row ? row.querySelector("[data-admin-img-preview]") : null;
  };

  document.addEventListener("change", (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || input.type !== "file") return;
    const file = input.files && input.files[0];
    if (!file || !file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    const box = previewBoxFor(input);
    const max = Number(box && box.getAttribute("data-admin-img-max")) || 120;
    setPreviewImg(box, url, max);

    const field = input.closest(".site-content-editor__field");
    const cmsImg = field && field.querySelector(".site-content-editor__img-preview img");
    if (cmsImg) cmsImg.src = url;

    const hero = input.closest("[data-hero-row]");
    const heroImg = hero && hero.querySelector(".hero-slide-row__preview img");
    if (heroImg) heroImg.src = url;
  });
})();
