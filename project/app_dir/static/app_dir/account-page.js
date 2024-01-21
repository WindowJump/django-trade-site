document.addEventListener('DOMContentLoaded', function () {
    // start WebSocket connection
    const accountSocket = new WebSocket('ws://localhost:8000/ws/account/');

    // retrieve all delete buttons for offers
    const deleteButtons = document.querySelectorAll('[id^="delete-"]');
    // if button is triggered send message to the server
    deleteButtons.forEach(function (button){
        button.addEventListener('click', function(){
            const offerID = button.id.split('-')[1];
            accountSocket.send(
                JSON.stringify({
                    'type': 'delete_offer',
                    'offerID_to_delete': offerID,
                })
            );
        });
    });

    accountSocket.onmessage = function (msg) {
        const data = JSON.parse(msg.data);
        // delete the offer from html table
        if (data.type === 'delete_offer'){
            const offer_to_delete = document.getElementById(data.id_to_delete);
            offer_to_delete.parentNode.removeChild(offer_to_delete);
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
        // update_balance
        else if (data.type === 'update_balance'){
            const idPrefix = data.id_prefix;
            console.log(1);
            if (idPrefix === 'USDT'){
                const USDTBalanceDOM = document.getElementById(`${idPrefix}-balance`);
                const USDTReservedDOM = document.getElementById(`${idPrefix}-reserved`);
                USDTBalanceDOM.textContent = data.new_balance
                USDTReservedDOM.textContent = data.new_reserved
            }
            else {
                const CoinBalanceDOM = document.getElementById(`${idPrefix}-balance`);
                const CoinReservedDOM = document.getElementById(`${idPrefix}-reserved`);
                CoinBalanceDOM.textContent = data.new_balance
                CoinReservedDOM.textContent = data.new_reserved
            }
        }
        // send an error if occurred
        else if (data.type === 'send_error'){
            alert(data.error_message);
        }
    };
});

