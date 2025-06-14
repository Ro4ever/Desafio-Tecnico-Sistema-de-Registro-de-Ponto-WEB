// Exemplo de script JS (opcional, pode ser usado para atualizar o relógio em tempo real)
function updateClock() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    const dateElement = document.getElementById('current-date');

    if (timeElement) {
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}:${seconds}`;
    }

    if (dateElement) {
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0'); // Mês é 0-indexed
        const year = now.getFullYear();
        dateElement.textContent = `${day}/${month}/${year}`;
    }
}

// Atualiza o relógio a cada segundo se o elemento existir
if (document.getElementById('current-time')) {
    setInterval(updateClock, 1000);
    updateClock(); // Chama imediatamente para exibir o tempo assim que a página carregar
}