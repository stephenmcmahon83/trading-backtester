// Function to fetch stock data
async function fetchStockData() {
    const symbolInput = document.getElementById('symbolInput');
    const fetchBtn = document.getElementById('fetchBtn');
    const errorMessage = document.getElementById('errorMessage');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultSection = document.getElementById('resultSection');
    
    const symbol = symbolInput.value.trim().toUpperCase();
    
    // Validate input
    if (!symbol) {
        showError('Please enter a stock symbol');
        return;
    }
    
    // Clear previous error and hide results
    errorMessage.classList.remove('show');
    resultSection.classList.remove('show');
    
    // Show loading spinner
    loadingSpinner.classList.add('show');
    fetchBtn.disabled = true;
    
    try {
        const response = await fetch('/api/stock-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbol: symbol })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch data');
        }
        
        // Display the data
        displayStockData(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        loadingSpinner.classList.remove('show');
        fetchBtn.disabled = false;
    }
}

// Function to display stock data in table
function displayStockData(data) {
    const stockSymbol = document.getElementById('stockSymbol');
    const dataCount = document.getElementById('dataCount');
    const tableBody = document.getElementById('tableBody');
    const resultSection = document.getElementById('resultSection');
    
    // Update header
    stockSymbol.textContent = data.symbol;
    dataCount.textContent = `${data.data.length} trading days`;
    
    // Clear existing table data
    tableBody.innerHTML = '';
    
    // Populate table (reverse to show newest first)
    data.data.reverse().forEach(day => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${day.date}</td>
            <td>$${day.open.toFixed(2)}</td>
            <td>$${day.high.toFixed(2)}</td>
            <td>$${day.low.toFixed(2)}</td>
            <td>$${day.close.toFixed(2)}</td>
            <td>${formatVolume(day.volume)}</td>
        `;
        tableBody.appendChild(row);
    });
    
    // Show results
    resultSection.classList.add('show');
}

// Function to show error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// Function to format volume numbers
function formatVolume(volume) {
    if (volume >= 1000000) {
        return (volume / 1000000).toFixed(2) + 'M';
    } else if (volume >= 1000) {
        return (volume / 1000).toFixed(2) + 'K';
    }
    return volume.toLocaleString();
}

// Allow Enter key to trigger fetch
document.getElementById('symbolInput').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        fetchStockData();
    }
});