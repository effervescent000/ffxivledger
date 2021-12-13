function getCraftQueue(num, currentUser) {
    if (typeof num === "string") {
        num = parseInt(num)
    }
    fetch(`/craft/get_queue/${currentUser}-${num}`)
    .then(data => data.json())
    .then(data => {
        console.log(data)
        const parent = document.getElementById("crafting-output-wrapper")
        const craftList = data[0]
        craftList.forEach(craft => {
            const craftDiv = document.createElement('div')
            craftDiv.className = "craft-queue-item"
            craftDiv.innerHTML = `${craft[0]} for ${craft[1]} ${craft[2]}`
            parent.appendChild(craftDiv)
        });
    })
}