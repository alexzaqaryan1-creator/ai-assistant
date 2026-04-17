const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const docInfo = document.getElementById("doc-info");
const resetBtn = document.getElementById("reset-btn");
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) uploadFile(e.target.files[0]);
});

["dragenter", "dragover"].forEach((ev) =>
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    })
);
["dragleave", "drop"].forEach((ev) =>
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
    })
);
dropZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
});

async function uploadFile(file) {
    setStatus("Uploading and reading document...");
    const fd = new FormData();
    fd.append("file", file);

    try {
        const res = await fetch("/upload", { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok) {
            addMessage("error", data.error || "Upload failed.");
            return;
        }
        docInfo.querySelector(".doc-name").textContent = data.filename;
        docInfo.querySelector(".doc-meta").textContent =
            `${data.chars.toLocaleString()} characters extracted`;
        docInfo.classList.remove("hidden");
        chatInput.disabled = false;
        sendBtn.disabled = false;
        messagesEl.innerHTML = "";
        addMessage("assistant",
            `Got "${data.filename}". Ask me anything about it.`);
        chatInput.focus();
    } catch (err) {
        addMessage("error", "Upload failed: " + err.message);
    }
}

resetBtn.addEventListener("click", async () => {
    await fetch("/reset", { method: "POST" });
    docInfo.classList.add("hidden");
    fileInput.value = "";
    chatInput.disabled = true;
    sendBtn.disabled = true;
    messagesEl.innerHTML =
        '<div class="empty-state"><h2>Ready when you are.</h2>' +
        '<p>Upload a document on the left to begin the conversation.</p></div>';
});

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = chatInput.value.trim();
    if (!question) return;

    addMessage("user", question);
    chatInput.value = "";
    chatInput.style.height = "auto";
    sendBtn.disabled = true;

    const loadingEl = addMessage("assistant loading", "Thinking...");

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });
        const data = await res.json();
        loadingEl.remove();

        if (!res.ok) {
            addMessage("error", data.error || "Something went wrong.");
        } else {
            addMessage("assistant", data.answer);
        }
    } catch (err) {
        loadingEl.remove();
        addMessage("error", "Request failed: " + err.message);
    } finally {
        sendBtn.disabled = false;
        chatInput.focus();
    }
});

chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = chatInput.scrollHeight + "px";
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

function addMessage(role, text) {
    const empty = messagesEl.querySelector(".empty-state");
    if (empty) empty.remove();
    const el = document.createElement("div");
    el.className = `message ${role}`;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
}

function setStatus(text) {
    console.log(text);
}
