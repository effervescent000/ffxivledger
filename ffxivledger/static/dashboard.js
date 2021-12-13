function getCraftQueue(num, currentUser) {
    if (typeof num === "string") {
        num = parseInt(num);
    }
    // first clear out any currently listed crafting queue items
    const parent = document.getElementById("crafting-output-wrapper");
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }

    // next retrieve the crafting queue from the backend
    fetch(`/craft/get_queue/${currentUser}-${num}`)
        .then((data) => data.json())
        .then((data) => {
            // console.log(data)
            const craftList = data[0];
            craftList.forEach((craft) => {
                const craftDiv = document.createElement("div");
                craftDiv.className = "craft-queue-item";
                craftDiv.innerHTML = `${craft[0]} for ${craft[1]} ${craft[2]}`;
                parent.appendChild(craftDiv);
            });
        });
}

async function getName(value) {
    let data = await fetch(`/item/view/${value}`)
        .then((data) => data.json())
        .then((data) => data.name);
    return data.name;
}

async function loadStockFrame(currentUser) {
    fetch(`/item/stock/user/${currentUser}`)
        .then((data) => data.json())
        .then((data) => {
            data.forEach((stock) => {
                const nameDiv = document.createElement("div");
                nameDiv.className = "stock-name";
                const amountDiv = document.createElement("div");
                amountDiv.className = "stock-amount";
                nameDiv.innerHTML = stock.item_value;
                amountDiv.innerHTML = stock.amount;
                document.getElementById("stock-frame").appendChild(nameDiv);
                document.getElementById("stock-frame").appendChild(amountDiv);
            });
        });
}
