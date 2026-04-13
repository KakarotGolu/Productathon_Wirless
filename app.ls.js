const API_CONFIG = {
    BASE_URL: "http://localhost:8000"
};

function sendMessage() {
    const userInput = document.getElementById("user-input");
    const submitBtn = document.getElementById("send-button");
    const userMessage = userInput.value;

    if (userMessage.trim() === "") {
        return;
    }

    appendMessage(userMessage, "user");
    userInput.value = "";  // Clear input field

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";

    // Set up 10-second timeout via AbortController
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    // Send user input to backend API for processing
    fetch(`${API_CONFIG.BASE_URL}/chatbot/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ "niche": userMessage }),
        signal: controller.signal
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || !Array.isArray(data.content_suggestions) || data.content_suggestions.length === 0) {
                throw new Error("Invalid response format from server");
            }
            const botReply = data.content_suggestions.join("\n");  // Joining ideas into a single string
            console.log("Bot reply received:", botReply);
            appendMessage(botReply, "bot");
        })
        .catch(error => {
            if (error.name === "AbortError") {
                console.error("Request timed out after 10 seconds");
                appendMessage("Error: Request timed out. Please try again.", "bot");
            } else {
                console.error("Error:", error);
                appendMessage(`Error: ${error.message || "Failed to get response"}`, "bot");
            }
        })
        .finally(() => {
            clearTimeout(timeoutId);
            submitBtn.disabled = false;
            submitBtn.textContent = "Send";
        });
}

function appendMessage(message, sender) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");
    messageElement.classList.add("chat-message", `${sender}-message`);
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;  // Auto scroll to the latest message
}

// Allow users to send messages by pressing Enter
document.addEventListener("DOMContentLoaded", function () {
    const userInput = document.getElementById("user-input");
    if (userInput) {
        userInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                sendMessage();
            }
        });
    }
});
