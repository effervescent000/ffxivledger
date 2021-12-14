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
    fetch(`/craft/get_queue/${num}`, {
        credentials: "include"
    })
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

async function loadStockFrame() {
    fetch(`/item/stock`, {
        credentials: "include"
    })
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

function getSelectedItem() {
    const selectedItem = document.getElementById("item").value;
    if (selectedItem !== "") {
        return selectedItem;
    } else {
        alert("Please select an item");
    }
}

function getAmount() {
    const amount = document.getElementById("amount").value;
    // console.log(amount);
    if (amount !== 0 || amount !== "") {
        return amount;
    } else {
        alert("Please input an amount");
    }
}

function getGilValue() {
    const gilValue = document.getElementById("gil_value").value;
    // console.log(gilValue);
    if (gilValue !== "" || gilValue !== 0) {
        return gilValue;
    } else {
        alert("Please input a value in gil");
    }
}

function addSale() {
    const selectedItem = getSelectedItem();
    const amount = getAmount() * -1;
    const gilValue = getGilValue();

    if (
        selectedItem != undefined &&
        amount != undefined &&
        gilValue != undefined
    ) {
        const newTransaction = {
            item_value: selectedItem,
            amount: amount,
            gil_value: gilValue,
        };
        const xhr = new XMLHttpRequest();
        const url = "/transaction/add";
        xhr.open("POST", url);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.withCredentials = true;
        xhr.send(JSON.stringify(newTransaction));
    }
}
