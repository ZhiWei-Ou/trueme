"use strict";

const PHOTO_SIZES = {
  "small-one-inch": { width: 260, height: 378, mm: "22 × 32" },
  "one-inch": { width: 295, height: 413, mm: "25 × 35" },
  "large-one-inch": { width: 390, height: 567, mm: "33 × 48" },
  "two-inch": { width: 413, height: 579, mm: "35 × 49" },
  "small-two-inch": { width: 413, height: 531, mm: "35 × 45" },
  "large-two-inch": { width: 413, height: 626, mm: "35 × 53" },
  "five-inch": { width: 1050, height: 1500, mm: "88.9 × 127" },
  "six-inch": { width: 1200, height: 1800, mm: "101.6 × 152.4" },
  "seven-inch": { width: 1500, height: 2100, mm: "127 × 177.8" },
  "eight-inch": { width: 1800, height: 2400, mm: "152.4 × 203.2" },
};

function customPhotoSize(width, height) {
  const widthMM = Number(width);
  const heightMM = Number(height);
  if (![widthMM, heightMM].every((value) => Number.isFinite(value) && value >= 10 && value <= 300)) {
    return null;
  }
  return {
    width: Math.round(widthMM / 25.4 * 300), height: Math.round(heightMM / 25.4 * 300),
    mm: `${widthMM} × ${heightMM}`, widthMM, heightMM,
  };
}

function photoCrop(width, height, ratio, zoom, horizontal, vertical) {
  const cropWidth = Math.min(width, height * ratio) / zoom;
  const cropHeight = cropWidth / ratio;
  return {
    x: (width - cropWidth) * horizontal,
    y: (height - cropHeight) * vertical,
    width: cropWidth,
    height: cropHeight,
  };
}

function setupPhotoExport() {
  const element = (id) => document.getElementById(id);
  const dialog = element("photo-dialog");
  const canvas = element("photo-crop");
  const sizeSelect = element("photo-size");
  const formatSelect = element("photo-format");
  const customFields = element("photo-custom-size");
  const customWidth = element("photo-width");
  const customHeight = element("photo-height");
  const zoom = element("photo-zoom");
  const horizontal = element("photo-x");
  const vertical = element("photo-y");
  const status = element("photo-export-status");
  const download = element("photo-download");
  let source = null;
  let sourceName = "";
  let request = null;

  function selectedSize() {
    return sizeSelect.value === "custom"
      ? customPhotoSize(customWidth.value, customHeight.value) : PHOTO_SIZES[sizeSelect.value];
  }

  function render() {
    customFields.hidden = sizeSelect.value !== "custom";
    download.textContent = `Download ${formatSelect.value.toUpperCase()}`;
    if (!source?.complete || !source.naturalWidth) return;
    const size = selectedSize();
    download.disabled = !size || Boolean(request);
    if (!size) {
      canvas.width = canvas.height = 0;
      element("photo-dimensions").textContent = "";
      status.textContent = "Enter width and height between 10 and 300 mm.";
      return;
    }
    const crop = photoCrop(source.naturalWidth, source.naturalHeight,
      size.width / size.height, Number(zoom.value),
      Number(horizontal.value) / 100, Number(vertical.value) / 100);
    canvas.width = size.width;
    canvas.height = size.height;
    const context = canvas.getContext("2d");
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    if (formatSelect.value === "jpeg") {
      context.fillStyle = "white";
      context.fillRect(0, 0, canvas.width, canvas.height);
    }
    context.drawImage(source, crop.x, crop.y, crop.width, crop.height,
      0, 0, canvas.width, canvas.height);
    element("photo-dimensions").textContent =
      `${size.mm} mm · ${size.width} × ${size.height} px · 300 DPI`;
    status.textContent = crop.width < size.width || crop.height < size.height
      ? "This crop will be enlarged; a higher-resolution photo gives a sharper result."
      : "";
  }

  element("photo-export").addEventListener("click", async () => {
    const reference = element("reference-preview");
    if (reference.hidden || !reference.src) return;
    sourceName = reference.dataset.filename;
    zoom.value = "1";
    horizontal.value = vertical.value = "50";
    status.textContent = "Loading photo…";
    download.disabled = true;
    dialog.showModal();
    const image = new Image();
    source = image;
    image.src = reference.src;
    try {
      await image.decode();
      if (source !== image) return;
      render();
    } catch {
      if (source === image) status.textContent = "Cannot load the reference photo. Choose it again.";
    }
  });

  for (const control of [sizeSelect, formatSelect, customWidth, customHeight, zoom, horizontal, vertical]) {
    control.addEventListener("input", render);
  }

  download.addEventListener("click", async () => {
    const dimensions = selectedSize();
    if (!source || request || !dimensions) return;
    const controller = new AbortController();
    request = controller;
    const size = sizeSelect.value;
    const format = formatSelect.value;
    const extension = sourceName.lastIndexOf(".");
    const basename = extension > 0 ? sourceName.slice(0, extension) : sourceName;
    const suffix = size === "custom" ? `${dimensions.widthMM}x${dimensions.heightMM}mm` : size;
    const filename = `${basename}-${suffix}.${format === "png" ? "png" : "jpg"}`;
    const customQuery = size === "custom"
      ? `&width_mm=${dimensions.widthMM}&height_mm=${dimensions.heightMM}` : "";
    download.disabled = true;
    status.textContent = `Preparing ${format.toUpperCase()}…`;
    try {
      const body = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      if (!body) throw new Error("Cannot prepare this photo. Try another reference.");
      const response = await fetch(`/api/photo-export?size=${encodeURIComponent(size)}${customQuery}&format=${format}`, {
        method: "POST", headers: { "Content-Type": "image/png" }, body,
        signal: controller.signal,
      });
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.error.message);
      }
      const file = await response.blob();
      if (controller.signal.aborted) return;
      const url = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = `${format.toUpperCase()} ready. Check your browser downloads.`;
    } catch (error) {
      if (!controller.signal.aborted) status.textContent = error.message;
    } finally {
      if (request === controller) {
        request = null;
        download.disabled = !source || !selectedSize();
      }
    }
  });

  dialog.addEventListener("close", () => {
    request?.abort();
    request = null;
    source = null;
    sourceName = "";
    canvas.width = canvas.height = 0;
    download.disabled = true;
  });
}

if (typeof document !== "undefined") setupPhotoExport();
if (typeof module !== "undefined") {
  module.exports = { photoCrop, PHOTO_SIZES, customPhotoSize, setupPhotoExport };
}
