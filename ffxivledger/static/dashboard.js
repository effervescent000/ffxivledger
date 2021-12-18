// functions
function getCraftQueue(num) {
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
                const craftWrapperDiv = document.createElement("div");
                craftWrapperDiv.className = "craft-item-wrapper";
                parent.appendChild(craftWrapperDiv);

                const craftTextDiv = document.createElement("div");
                craftTextDiv.innerHTML = `${craft[0]} for ${craft[1]} gil/hour`;
                const craftButtonWrapper = document.createElement("div");
                const craftButton = document.createElement("button");
                craftButton.innerHTML = "Craft 1";
                let craftId = null
                fetch(`/item/get_name/${craft[0]}`)
                    .then(data => data.json())
                    .then(data => {
                        craftId = data.id
                    })
                craftButton.addEventListener("click", (event) =>
                    addStock(craftId, 1)
                );

                craftWrapperDiv.appendChild(craftTextDiv);
                craftWrapperDiv.appendChild(craftButtonWrapper);
                craftButtonWrapper.appendChild(craftButton);
            });
        });
}

async function getName(id) {
    let data = await fetch(`/item/view/${id}`)
        .then((data) => data.json())
        .then((data) => data.name);
    return data.name;
}

function loadStockFrame() {
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

        fetch("http://127.0.0.1:5000/transaction/add", {
            method: 'POST',
            headers: {"content-type": "application/json"},
            body: JSON.stringify(newTransaction)
        })
            .then(response => response.json())
            .then(data => console.log(data))
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

function addStock(selectedItem = null, amount = null) {
    if (selectedItem === null) {
        selectedItem = getSelectedItem();
    }
    if (amount === null) {
        amount = getAmount();
    }
    const gilValue = 0;

    console.log(postTransaction(selectedItem, amount, gilValue));
}
