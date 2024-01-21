// declare variables to check and update user's balance data
let UserUSDTBalance, UserCoinBalance;

// in pricesData we will store data to build and update chart
let pricesData = {
    dates: [],
    prices: []
};

// declare variables to track max and min price for 24h
let minPrice = Infinity;
let maxPrice = -Infinity;
let firstPrice = 0;
let currentPrice = 0;

document.addEventListener('DOMContentLoaded', function () {
    // get User balance data
    UserUSDTBalance = Number.parseFloat(document.getElementById('user-usdt-balance').textContent);
    UserCoinBalance = Number.parseFloat(document.getElementById('user-coin-balance').textContent);

    // retrieve coinName
    coinName = document.getElementById('coin-name').textContent;

    // functions that starts WebSocket connections
    startClientWebSocketConn();
    startCoinCapWebSocketConn();

    // add logic for curr/100% buttons
    const currentPriceButtonElement= document.getElementById('current-price-button');
    const currenPriceInputElement = document.getElementById('offer-price-input');
    currentPriceButtonElement.onclick = function (){
        currenPriceInputElement.value = currentPrice;
    }

    const allUserCoinsButtonElement = document.getElementById('all-amount-button');
    const allUserCoinsInputElement = document.getElementById('offer-amount-input');
    allUserCoinsButtonElement.onclick = function (){
        allUserCoinsInputElement.value = UserCoinBalance;
    }
})

function startClientWebSocketConn(){
    // start websocket connection with client and our server
    const clientSocket = new WebSocket('ws://localhost:8000/ws/main-page/' + coinName + '/');
    // wait for message from server
    clientSocket.onmessage = function (msg){
        // parse and use new data
        const data = JSON.parse(msg.data);
        // update coin data
        if (data.type === 'fetch_coin_data'){
            firstPrice = data.prices[0]
            update_coin_data(data.min_val, data.max_val, data.prices.slice(-1));
            pricesData.dates = data.dates;
            pricesData.prices = data.prices;
            buildChart();
        }
        // delete the offer from html table
        else if (data.type === 'delete_offer'){
            const offer_to_delete = document.getElementById(data.id_to_delete);
            offer_to_delete.parentNode.removeChild(offer_to_delete);
        }
        // display new offer
        else if (data.type === 'send_offer'){
            // create new tbody, new row and cell to append
            const newRow = document.createElement('tr');
            const newCell = document.createElement('td');
            newCell.id = 'offer-' + data.data.object_id;
            const newTbody = document.createElement('tbody');

            // Create a link element (<a>) with the href to new offer
            const link = document.createElement('a');
            link.href = 'http://localhost:8000/offer-detail/' + data.data.object_id;
            link.innerText = `${data.data.coin_type}: ${data.data.amount} total: ${data.data.total} (rate: ${data.data.exchange_rate})`;

            // Append the link to the cell
            newCell.appendChild(link);
            newRow.appendChild(newCell);

            // swap operation type to display from user perspective
            const targetTable = data.data.operation_type === 'Buy' ? document.getElementById('sell-table') : document.getElementById('buy-table');
            targetTable.appendChild(newTbody);
            newTbody.appendChild(newRow);
        }
        // display a new transaction
        else if (data.type === 'display_transaction') {
            // create a new row and cell names what we have to create
            const newRow = document.createElement('tr');
            const cellNames = ['crypto_name', 'operation', 'amount', 'exchange_rate'];
            // create for each cellName new td and get info from data using cellName as a key
            cellNames.forEach((cellName) => {
                const cell = document.createElement('td');
                cell.innerText = data[cellName];
                cell.classList.add('text-center');
                newRow.appendChild(cell);
            });
            // find target table
            const targetTable = document.getElementById('last-transactions-table');
            // create tbody and append new elements to the table
            const tbody = document.createElement('tbody');
            targetTable.appendChild(tbody);
            tbody.appendChild(newRow);
        }
        // display an error if it was caught in consumer
        else if (data.type === 'send_error'){
            alert(data.error_message);
        }
    }

    // submit offer on click
    const submitButtonElement = document.getElementById('submit-offer');
    submitButtonElement.onclick = function () {
        // get necessary data to send for offer creation
        const exchange_rateElement = document.getElementById('offer-price-input');
        const amountElement = document.getElementById('offer-amount-input');
        const operation = document.getElementById('sell-or-buy').value;
        const exchange_rate = exchange_rateElement.value;
        const amount = amountElement.value;
        const total = amount * exchange_rate;

        // make simple check if all inputs have some values
        if (!operation || !exchange_rate || !amount) {
            alert('Please fill in all fields before sending the offer.');
        }
        // also check if user have enough usdt/coins to make an offer, also there is double check on backend
        else if (operation === 'Sell') {
            if (UserCoinBalance < amount) {
                alert(`You don't have enough ${coinName} on balance to post this offer`);
            }
            else {
                // update user balance
                UserCoinBalance -= amount;
                const userCoinBalanceElement = document.getElementById('user-coin-balance');
                userCoinBalanceElement.value = UserCoinBalance;
            }
        } else if (operation === 'Buy') {
            if (UserUSDTBalance < total) {
                alert(`You don't have enough USDT on balance to post this offer`);
            }
            else {
                UserUSDTBalance -= total;
                const userUSDTBalanceElement = document.getElementById('user-usdt-balance');
                userUSDTBalanceElement.textContent = UserUSDTBalance;
            }
        }
        // create dict with offer data and send it
        const dataToSend = {
            exchange_rate: exchange_rate,
            amount: amount,
            operation_type: operation,
            total: total,
        };

        clientSocket.send(
            JSON.stringify({
                'type': 'create_offer',
                'data': dataToSend,
            })
        )
        exchange_rateElement.value = '';
        amountElement.value = '';
    }
}

function startCoinCapWebSocketConn(){
    // start websocket connection with coincap to retrieve new information about coin
    const pricesWs = new WebSocket('wss://ws.coincap.io/prices?assets=' + coinName);
    // wait for message event
    pricesWs.onmessage = function (msg) {
        // Parse the data from WebSocket
        const newData = JSON.parse(msg.data);

        // get price data from msg
        for (const key in newData) {
            if (newData.hasOwnProperty(key)) {
                const newPrice = newData[key];
                // Update coin data
                currentPrice = parseFloat(newPrice);
                update_coin_data(currentPrice, currentPrice, currentPrice)
            }
        }
    };
}

// function to find minimal and maximal value for minVal and maxVal
function update_coin_data(newMin, newMax, currentPrice){
    // calculate new values
    minPrice = Math.min(minPrice, newMin);
    maxPrice = Math.max(maxPrice, newMax);

    // Update current price element
    const currentPriceElement = document.getElementById('current-price-output');
    currentPriceElement.innerText = currentPrice;

    // Update min and max price elements
    const maxOutputElement = document.getElementById('max-price-output');
    const minOutputElement = document.getElementById('min-price-output');
    minOutputElement.textContent = minPrice;
    maxOutputElement.textContent = maxPrice;

    // Update 24h change(%)
    const percentageChangeElement = document.getElementById('percentage-change-output');
    const percentageChange = ((currentPrice - firstPrice) / firstPrice) * 100;
    percentageChangeElement.innerText = percentageChange.toFixed(2) + '%';
}

function buildChart(){
    // function responsible for building the chart using plotly
    let trace = {
        x: pricesData.dates,
        y: pricesData.prices,
        type: 'scatter',
        mode: 'lines',
    };

    const layout = {
        displayModeBar: false,
        yaxis: {
            fixedrange: true
        },
        xaxis: {
            fixedrange: true
        }
    };
    const config = {
        displayModeBar: false,
        dragmode: false,
    };

    let chartData = [trace];
    Plotly.newPlot('plotly-chart', chartData, layout, config);
}

function allowOnlyNumbersAndDot(event){
    // function that allows to input only numbers or 1 dot in input fields
    if (event.which != 8 && event.which != 0 && event.which != 46 && (event.which < 48 || event.which > 57)) {
            event.preventDefault();
    }
    const input = event.target.value;
    if (event.which == 46 && input.indexOf('.') !== -1) {
            event.preventDefault();
    }
}
