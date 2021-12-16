// event listeners
// document
//     .getElementById("sale-btn")
//     .addEventListener("click", (event) => addSale());
// document.getElementById("purchase-btn").addEventListener("click", (event) => addPurchase());
// document.getElementById("remove-stock-btn").addEventListener("click", (event) => removeStock());
// document.getElementById("add-stock-btn").addEventListener("click", (event) => addStock())

// functions
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
        credentials: "include",
    })
        .then((data) => data.json())
        .then((data) => {
            console.log(data);
            const craftList = data;
            craftList.forEach((craft) => {
                const craftDiv = document.createElement("div");
                craftDiv.className = "craft-queue-item";
                craftDiv.innerHTML = `${craft[0]} for ${craft[1]}`;
                parent.appendChild(craftDiv);
            });
        });
}

async function getName(id) {
    let data = await fetch(`/item/view/${id}`)
        .then((data) => data.json())
        .then((data) => data.name);
    return data.name;
}

async function loadStockFrame() {
    fetch(`/item/stock`, {
        credentials: "include",
    })
        .then((data) => data.json())
        .then((data) => {
            data.forEach((stock) => {
                const nameDiv = document.createElement("div");
                nameDiv.className = "stock-name";
                const amountDiv = document.createElement("div");
                amountDiv.className = "stock-amount";
                nameDiv.innerHTML = stock.item.name;
                amountDiv.innerHTML = stock.amount;
                document.getElementById("stock-frame").appendChild(nameDiv);
                document.getElementById("stock-frame").appendChild(amountDiv);
            });
        });
}

function getSelectedItem() {
    const selectedItem = document.getElementById("item").value;
    // console.log(selectedItem);
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

function postTransaction(selectedItem, amount, gilValue) {
    if (
        selectedItem != undefined &&
        amount != undefined &&
        gilValue != undefined
    ) {
        const newTransaction = {
            item_id: selectedItem,
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

function addSale() {
    const selectedItem = getSelectedItem();
    const amount = getAmount() * -1;
    const gilValue = getGilValue();

    postTransaction(selectedItem, amount, gilValue);
}

function addPurchase() {
    const selectedItem = getSelectedItem();
    const amount = getAmount();
    const gilValue = getGilValue() * -1;

    postTransaction(selectedItem, amount, gilValue);
}

function removeStock() {
    const selectedItem = getSelectedItem();
    const amount = getAmount() * -1;
    const gilValue = 0;

    postTransaction(selectedItem, amount, gilValue);
}

function addStock() {
    const selectedItem = getSelectedItem();
    const amount = getAmount();
    const gilValue = 0;

    console.log(postTransaction(selectedItem, amount, gilValue));
}
