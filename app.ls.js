function sendMessage() {
    const userMessage = document.getElementById("user-input").value;
    if (userMessage.trim() !== "") {
        appendMessage(userMessage, "user");
        document.getElementById("user-input").value = "";  // Clear input field

        // Send user input to backend API for processing
        fetch("http://localhost:8000/chatbot/", {  // Change to your actual API URL
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ "niche": userMessage })
        })
            .then(response => response.json())
            .then(data => {
                const botReply = data.content_suggestions.join("\n");  // Joining ideas into a single string
                appendMessage(botReply, "bot");
            })
            .catch(error => {
                console.error("Error:", error);
                appendMessage("Sorry, there was an error. Please try again.", "bot");
            });
    }
}

function appendMessage(message, sender) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");
    messageElement.classList.add("chat-message", `${sender}-message`);
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;  // Auto scroll to the latest message
}
