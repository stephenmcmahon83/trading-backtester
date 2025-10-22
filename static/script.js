// Global variable to store current data
let currentData = [];
let sortColumn = 'date';
let sortDirection = 'desc'; // Start with newest first

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
        
        // Store data globally and display
        currentData = data.data;
        sortColumn = 'date';
        sortDirection = 'desc';
        displayStockData(data.symbol, currentData);
        
    } catch (error) {
        showError(error.message);
    } finally {
        loadingSpinner.classList.remove('show');
        fetchBtn.disabled = false;
    }
}

// Function to sort data
function sortData(column) {
    // Toggle direction if clicking same column
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'desc'; // Default to descending for new column
    }
    
    // Sort the data
    currentData.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];
        
        // Handle different data types
        if (column === 'date') {
            aVal = new Date(aVal);
            bVal = new Date(bVal);
        } else {
            aVal = parseFloat(aVal);
            bVal = parseFloat(bVal);
        }
        
        if (sortDirection === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });
    
    // Re-render table
    renderTable(currentData);
    updateSortIndicators();
}

// Function to display stock data
function displayStockData(symbol, data) {
    const stockSymbol = document.getElementById('stockSymbol');
    const dataCount = document.getElementById('dataCount');
    const resultSection = document.getElementById('resultSection');
    
    // Update header
    stockSymbol.textContent = symbol;
    
    // Calculate date range
    const dates = data.map(d => new Date(d.date));
    const oldestDate = new Date(Math.min(...dates));
    const newestDate = new Date(Math.max(...dates));
    const years = ((newestDate - oldestDate) / (365.25 * 24 * 60 * 60 * 1000)).toFixed(1);
    
    dataCount.textContent = `${data.length} trading days (${years} years)`;
    
    // Render table
    renderTable(data);
    updateSortIndicators();
    
    // Show results
    resultSection.classList.add('show');
}

// Function to render table body
function renderTable(data) {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    
    data.forEach(day => {
        const row = document.createElement('tr');
        
        // Calculate daily change
        const change = day.close - day.open;
        const changePercent = ((change / day.open) * 100).toFixed(2);
        const changeClass = change >= 0 ? 'positive' : 'negative';
        
        row.innerHTML = `
            <td>${day.date}</td>
            <td>$${day.open.toFixed(2)}</td>
            <td>$${day.high.toFixed(2)}</td>
            <td>$${day.low.toFixed(2)}</td>
            <td>$${day.close.toFixed(2)}</td>
            <td class="${changeClass}">${change >= 0 ? '+' : ''}$${change.toFixed(2)} (${changePercent}%)</td>
            <td>${formatVolume(day.volume)}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Function to update sort indicators
function updateSortIndicators() {
    // Remove all existing indicators
    document.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add indicator to current sort column
    const columnMap = {
        'date': 0,
        'open': 1,
        'high': 2,
        'low': 3,
        'close': 4,
        'volume': 5
    };
    
    const thIndex = columnMap[sortColumn];
    if (thIndex !== undefined) {
        const th = document.querySelectorAll('th')[thIndex];
        th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
    }
}

// Function to show error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// Function to format volume numbers
function formatVolume(volume) {
    if (volume >= 1000000000) {
        return (volume / 1000000000).toFixed(2) + 'B';
    } else if (volume >= 1000000) {
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