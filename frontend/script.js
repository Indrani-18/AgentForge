"use strict";

const API_URL = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", () => {
    const questionInput = document.getElementById("question");
    const sendButton = document.getElementById("send-btn");
    const chatBox = document.getElementById("chat-box");
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");

    if (!questionInput || !sendButton || !chatBox) {
        console.error("Frontend setup error: required HTML elements were not found.");
        return;
    }

    function addMessage(text, sender) {
        const message = document.createElement("div");
        message.className = sender === "user"
            ? "message user-message"
            : "message assistant-message";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = sender === "user" ? "👤" : "🤖";

        const content = document.createElement("div");
        content.className = "message-content";

        const name = document.createElement("div");
        name.className = "message-name";
        name.textContent = sender === "user" ? "You" : "AgentForge";

        const messageText = document.createElement("div");
        messageText.className = "message-text";

        // Safe display of backend text
        messageText.textContent = String(text ?? "");

        content.append(name, messageText);
        message.append(avatar, content);
        chatBox.appendChild(message);

        chatBox.scrollTop = chatBox.scrollHeight;

        return message;
    }

    async function sendQuestion() {
        const question = questionInput.value.trim();

        if (!question || sendButton.disabled) {
            return;
        }

        addMessage(question, "user");

        questionInput.value = "";
        questionInput.disabled = true;
        sendButton.disabled = true;
        sendButton.textContent = "Thinking...";

        const loadingMessage = addMessage(
            "AgentForge is thinking...",
            "assistant"
        );

        try {
            const response = await fetch(`${API_URL}/ask`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question
                })
            });

            let data;

            try {
                data = await response.json();
            } catch {
                throw new Error("The API returned an invalid response.");
            }

            loadingMessage.remove();

            addMessage(
                data.success
                    ? (data.answer || "AgentForge returned an empty answer.")
                    : (data.answer || "Something went wrong."),
                "assistant"
            );

        } catch (error) {
            console.error("AgentForge request error:", error);

            loadingMessage.remove();

            addMessage(
                "Could not connect to AgentForge. Please make sure FastAPI is running on port 8000.",
                "assistant"
            );

        } finally {
            questionInput.disabled = false;
            sendButton.disabled = false;
            sendButton.textContent = "Send";
            questionInput.focus();
        }
    }

    async function checkAPI() {
        try {
            const response = await fetch(`${API_URL}/health`);

            if (!response.ok) {
                throw new Error("API unavailable");
            }

            if (statusDot) {
                statusDot.className = "status-dot online";
            }

            if (statusText) {
                statusText.textContent = "API Connected";
            }

        } catch (error) {
            console.error("API health check failed:", error);

            if (statusDot) {
                statusDot.className = "status-dot offline";
            }

            if (statusText) {
                statusText.textContent = "API Offline";
            }
        }
    }

    window.setQuestion = function (question) {
        questionInput.value = question;
        questionInput.focus();
    };

    sendButton.addEventListener("click", sendQuestion);

    questionInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendQuestion();
        }
    });

    checkAPI();
});