"use strict";

const API_URL = "http://127.0.0.1:8000";

const input = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const chat = document.getElementById("chat");

let isSubmitting = false;

function hideWelcomeContent() {
    const welcome = document.getElementById("welcome");
    const suggestions = document.getElementById("suggestions");

    if (welcome) welcome.style.display = "none";
    if (suggestions) suggestions.style.display = "none";
}

function scrollChatToBottom() {
    chat.scrollTop = chat.scrollHeight;
}

function addMessage(text, role) {
    hideWelcomeContent();

    const message = document.createElement("div");
    message.className = `message ${role}`;

    const icon = document.createElement("div");
    icon.className = "message-icon";
    icon.textContent = role === "assistant" ? "🤖" : "👤";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    // textContent safely displays the backend answer as text.
    bubble.textContent = String(text ?? "");

    if (role === "assistant") {
        message.append(icon, bubble);
    } else {
        message.append(bubble, icon);
    }

    chat.appendChild(message);
    scrollChatToBottom();

    return message;
}

function addLoading() {
    const message = document.createElement("div");
    message.className = "message assistant";
    message.id = "loadingMessage";

    const icon = document.createElement("div");
    icon.className = "message-icon";
    icon.textContent = "🤖";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const typing = document.createElement("div");
    typing.className = "typing";

    for (let i = 0; i < 3; i++) {
        typing.appendChild(document.createElement("span"));
    }

    bubble.appendChild(typing);
    message.append(icon, bubble);
    chat.appendChild(message);

    scrollChatToBottom();
}

function removeLoading() {
    document.getElementById("loadingMessage")?.remove();
}

async function sendQuestion() {
    const question = input.value.trim();

    if (!question || isSubmitting) {
        return;
    }

    isSubmitting = true;
    sendButton.disabled = true;
    input.disabled = true;

    addMessage(question, "user");
    input.value = "";
    input.style.height = "42px";

    addLoading();

    try {
        const response = await fetch(`${API_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ question })
        });

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("The server did not return valid JSON.");
        }

        console.log("Backend response:", data);
        removeLoading();

        if (response.ok && data.success === true) {
            addMessage(
                data.answer || "AgentForge returned an empty answer.",
                "assistant"
            );
        } else {
            addMessage(
                data.answer ||
                data.detail ||
                data.error ||
                "AgentForge could not answer this question.",
                "assistant"
            );
        }
    } catch (error) {
        console.error("AgentForge frontend error:", error);
        removeLoading();

        addMessage(
            "Unable to connect to AgentForge. Make sure FastAPI is running at http://127.0.0.1:8000.",
            "assistant"
        );
    } finally {
        isSubmitting = false;
        sendButton.disabled = false;
        input.disabled = false;
        input.focus();
    }
}

function useSuggestion(text) {
    if (isSubmitting) return;

    input.value = text;
    sendQuestion();
}

function newConversation() {
    if (isSubmitting) return;

    // Reloading the page cleanly restores the welcome screen and suggestions.
    window.location.reload();
}

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
});

input.addEventListener("input", function () {
    this.style.height = "42px";
    this.style.height = `${Math.min(this.scrollHeight, 130)}px`;
});