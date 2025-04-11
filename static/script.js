function send_msg() {
    const userInput = document.getElementById('user_input').value;
    const edu_level = document.getElementById('edu_level').value;
    const course = document.getElementById('course').value;

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_input: userInput,
            edu_level: edu_level,
            course: course
        })
    })
    .then(response => response.json())
    .then(data => {
        const chat_area = document.getElementById('chat_area');
        chat_area.innerHTML += `<p><strong>You (${edu_level}, ${course}):</strong> ${userInput}</p>`;
        chat_area.innerHTML += `<p><strong>Bot:</strong> ${data.ai_answer}</p>`;
        document.getElementById('user_input').value = '';
    });
}

function clr_chat() {
    window.location.href = "/clear";
}
