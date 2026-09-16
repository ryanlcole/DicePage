function capture(element, label) {
  const rect = element.getBoundingClientRect();
  const style = getComputedStyle(element);
  return {
    label,
    semanticId: element.dataset.semanticId || "",
    mode: element.dataset.renderMode || "",
    background: style.backgroundImage && style.backgroundImage !== "none"
      ? style.backgroundImage
      : style.backgroundColor,
    width: rect.width,
    height: rect.height,
    x: rect.x,
    y: rect.y
  };
}

export function observe(element) {
  if (!element) {
    return {
      semanticId: "",
      mode: "",
      background: "",
      width: 0,
      height: 0,
      x: 0,
      y: 0
    };
  }

  return capture(element, "observe");
}

export function runInvarianceProof(element) {
  if (!element) {
    return { semanticId: "", stable: false, samples: [] };
  }

  const originalStyle = element.getAttribute("style");
  const samples = [];

  try {
    samples.push(capture(element, "baseline"));

    element.style.background = "linear-gradient(135deg, rgb(150, 46, 31), rgb(239, 178, 64))";
    samples.push(capture(element, "palette"));

    element.style.width = "137px";
    element.style.height = "73px";
    samples.push(capture(element, "size"));

    element.style.transform = "translate(-91px, 57px) rotate(7deg)";
    samples.push(capture(element, "position"));

    const semanticId = samples.length ? samples[0].semanticId : "";
    const stable = semanticId.length > 0 && samples.every(sample => sample.semanticId === semanticId);

    return { semanticId, stable, samples };
  } finally {
    if (originalStyle === null) {
      element.removeAttribute("style");
    } else {
      element.setAttribute("style", originalStyle);
    }
  }
}
