let foods = [];

function addFood() {
    const name = document.getElementById('foodName').value;
    const expiry = document.getElementById('expiryDate').value;
    if (!name || !expiry) return alert("입력값을 확인하세요!");
    
    foods.push({ name, expiry });
    render();
}

function render() {
    const list = document.getElementById('foodList');
    list.innerHTML = '';
    
    // 정렬: 유통기한 임박순
    foods.sort((a, b) => new Date(a.expiry) - new Date(b.expiry));
    
    foods.forEach((food, index) => {
        const today = new Date();
        const expiryDate = new Date(food.expiry);
        const diffDays = (expiryDate - today) / (1000 * 60 * 60 * 24);
        
        const li = document.createElement('li');
        if (diffDays <= 3) li.className = 'urgent';
        
        li.innerHTML = `<span>${food.name} (유통기한: ${food.expiry})</span>
                        <button onclick="foods.splice(${index}, 1); render()">삭제</button>`;
        list.appendChild(li);
    });
}
