(function () {
  const startBtn = document.getElementById("start-scan-btn");
  const stopBtn = document.getElementById("stop-scan-btn");
  const statusEl = document.getElementById("scan-status");
  const readerEl = document.getElementById("reader");

  if (!startBtn || !readerEl) {
    return;
  }

  const endpoint = window.scanEndpoint;
  let scanner = null;
  let scanning = false;
  let lastPayload = "";
  let lastHitAt = 0;

  function getCsrfToken() {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const cookie of cookies) {
      const item = cookie.trim();
      if (item.startsWith("csrftoken=")) {
        return decodeURIComponent(item.slice("csrftoken=".length));
      }
    }
    return "";
  }

  function setStatus(message, type) {
    statusEl.textContent = message;
    statusEl.className = "scan-status" + (type ? " " + type : "");
  }

  async function submitQrData(decodedText) {
    const now = Date.now();
    if (decodedText === lastPayload && now - lastHitAt < 3500) {
      return;
    }
    lastPayload = decodedText;
    lastHitAt = now;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ qr_data: decodedText }),
      });

      const data = await response.json();
      if (!response.ok || !data.ok) {
        setStatus(data.message || "Could not mark attendance.", "error");
        return;
      }

      if (data.status === "marked") {
        setStatus(data.message + " (" + data.student + ")", "success");
      } else {
        setStatus(data.message + " (" + data.student + ")", "warning");
      }

      setTimeout(function () {
        window.location.reload();
      }, 900);
    } catch (error) {
      setStatus("Network error while sending QR data.", "error");
    }
  }

  async function startScanner() {
    if (scanning) {
      return;
    }

    if (!window.Html5Qrcode) {
      setStatus("Scanner library could not load. Check internet connection.", "error");
      return;
    }

    scanner = new window.Html5Qrcode("reader");
    try {
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        submitQrData,
        function () {}
      );
      scanning = true;
      setStatus("Camera is live. Scan student QR.", "success");
    } catch (error) {
      scanning = false;
      setStatus("Camera start failed. Grant permission and retry.", "error");
    }
  }

  async function stopScanner() {
    if (!scanner || !scanning) {
      return;
    }

    try {
      await scanner.stop();
      await scanner.clear();
      scanning = false;
      setStatus("Scanner stopped.", "");
    } catch (error) {
      setStatus("Could not stop scanner cleanly.", "warning");
    }
  }

  startBtn.addEventListener("click", startScanner);
  stopBtn.addEventListener("click", stopScanner);
  window.addEventListener("beforeunload", stopScanner);
})();
