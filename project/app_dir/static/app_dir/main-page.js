document.addEventListener('DOMContentLoaded', function () {
    // start WebSocket connection with coincap api to get new coin data
    const pricesWs = new WebSocket('wss://ws.coincap.io/prices?assets=bitcoin,ethereum,litecoin');

    pricesWs.onmessage = function (msg){
        const data = JSON.parse(msg.data);
        // get coin_name from data dict
        for (const coin_name in data) {
            // get new price for coin_name
            const newPrice = parseFloat(data[coin_name]).toFixed(3);
            // change values in needed elements
            const priceCell = document.getElementById('last_price_' + coin_name);
            const percentageChangeCell = document.getElementById('24h_change_' + coin_name);
            // get first price from Element and calculate 24h change
            const prevPriceStr = document.getElementById('first_price_' + coin_name).textContent;
            const prevPrice = parseFloat(prevPriceStr.replace(/"/g, '')).toFixed(3);
            const percentageChange = ((newPrice - prevPrice) / prevPrice) * 100;
            // change values in Elements
            percentageChangeCell.textContent = percentageChange.toFixed(3);
            priceCell.textContent = newPrice;
        }
    }
});
