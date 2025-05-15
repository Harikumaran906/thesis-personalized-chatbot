document.addEventListener('DOMContentLoaded', function () {
    const doubtForm = document.getElementById('doubt_form');
    const doubtInput = document.getElementById('user_input');
    const chatArea = document.getElementById('chat_area');

    if (doubtForm) {
        doubtForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const doubt = doubtInput.value.trim();
            if (!doubt) return;

            chatArea.innerHTML = `<p><strong>You:</strong> ${doubt}</p>`;

            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doubt: doubt })
            })
            .then(response => response.json())
            .then(data => {
                // Show bot's answer
                chatArea.innerHTML += `<p><strong>Bot:</strong> ${data.ai_answer}</p>`;
                doubtInput.value = '';
            })
            .catch(error => {
                console.error('Error:', error);
                chatArea.innerHTML += `<p style="color:red;"><strong>Error:</strong> Could not get response</p>`;
            });
        });
    }
});
