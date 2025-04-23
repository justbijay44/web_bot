let context = {};
const chatPopup = document.getElementById('chat-popup');
const chatContent = document.getElementById('chat-content');
const quickActions = document.getElementById('quick-actions');

function toggleChat() {
    chatPopup.style.display = chatPopup.style.display === 'block' ? 'none' : 'block';
    if (chatPopup.style.display === 'block' && chatContent.innerHTML.trim() === '') {
        const timestamp = getCurrentTime();
        chatContent.innerHTML = `
            <div class="message bot">
                Hi, Welcome to Samasta Groups!<br>How can we help you today?
                <span class="timestamp">${timestamp}</span>
            </div>
        `;
        quickActions.style.display = 'flex';
    } else if (chatPopup.style.display === 'none') {
        quickActions.style.display = 'none';
    }
}

function sendMessage() {
    const input = document.getElementById('message');
    const message = input.value.trim();
    if (!message) return;

    const timestamp = getCurrentTime();
    const userMessage = `
        <div class="message user">
            ${message}
        </div>
    `;
    chatContent.innerHTML += userMessage;
    input.value = '';

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, context: context })
    })
    .then(response => response.json())
    .then(data => {
        const botMessage = `
            <div class="message bot">
                ${data.response}
                <span class="timestamp">${data.timestamp}</span>
            </div>
        `;
        chatContent.innerHTML += botMessage;
        context = data.context;
        chatContent.scrollTop = chatContent.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);
        const errorMessage = `
            <div class="message bot">
                Oops, something went wrong!
                <span class="timestamp">${getCurrentTime()}</span>
            </div>
        `;
        chatContent.innerHTML += errorMessage;
        chatContent.scrollTop = chatContent.scrollHeight;
    });
}

function sendQuickAction(action) {
    let message = '';
    switch (action) {
        case 'services': message = 'What services do you offer'; break;
        case 'contact': message = 'How do I contact you'; break;
        case 'pricing': message = 'How much'; break;
        case 'availability': message = 'When can you start'; break;
        case 'other': message = 'help'; break;
    }
    sendMessage();
    document.getElementById('message').value = message;
    sendMessage();
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

document.getElementById('message').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
});

// Initial setup
toggleChat();