// Global variable to store current data
let currentData = [];
let processedData = [];
let sortColumn = 'date';
let sortDirection = 'desc';
let currentSymbol = '';

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
        currentSymbol = data.symbol;
        sortColumn = 'date';
        sortDirection = 'desc';
        processDataForDisplay();
        displayStockData(data.symbol);
        
    } catch (error) {
        showError(error.message);
    } finally {
        loadingSpinner.classList.remove('show');
        fetchBtn.disabled = false;
    }
}

// Process data to include calculated fields
function processDataForDisplay() {
    processedData = currentData.map(day => {
        const change = day.close - day.open;
        const changePercent = (change / day.open) * 100;
        
        return {
            ...day,
            change: change,
            changePercent: changePercent,
            changeFormatted: `${change >= 0 ? '+' : ''}$${change.toFixed(2)}`,
            changePercentFormatted: `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`
        };
    });
    
    sortData(sortColumn, false); // Sort without re-processing
}

// Function to sort data
function sortData(column, reRender = true) {
    // Toggle direction if clicking same column
    if (sortColumn === column && reRender) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else if (reRender) {
        sortColumn = column;
        sortDirection = column === 'date' ? 'desc' : 'desc';
    }
    
    // Sort the data
    processedData.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];
        
        // Handle different data types
        if (column === 'date') {
            aVal = new Date(aVal);
            bVal = new Date(bVal);
        } else {
            // All other columns are numeric
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
        }
        
        if (sortDirection === 'asc') {
            return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        } else {
            return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        }
    });
    
    // Re-render table if requested
    if (reRender) {
        renderTable();
        updateSortIndicators();
    }
}

// Function to display stock data
function displayStockData(symbol) {
    const stockSymbol = document.getElementById('stockSymbol');
    const dataCount = document.getElementById('dataCount');
    const resultSection = document.getElementById('resultSection');
    
    // Update header
    stockSymbol.textContent = symbol;
    
    // Calculate date range
    const dates = processedData.map(d => new Date(d.date));
    const oldestDate = new Date(Math.min(...dates));
    const newestDate = new Date(Math.max(...dates));
    const years = ((newestDate - oldestDate) / (365.25 * 24 * 60 * 60 * 1000)).toFixed(1);
    
    dataCount.textContent = `${processedData.length} trading days • ${years} years`;
    
    // Render table
    renderTable();
    updateSortIndicators();
    updateRowCount();
    
    // Show results
    resultSection.classList.add('show');
}

// Function to render table body
function renderTable() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    
    processedData.forEach(day => {
        const row = document.createElement('tr');
        
        const changeClass = day.change >= 0 ? 'positive' : 'negative';
        
        row.innerHTML = `
            <td><strong>${formatDate(day.date)}</strong></td>
            <td>$${day.open.toFixed(2)}</td>
            <td>$${day.high.toFixed(2)}</td>
            <td>$${day.low.toFixed(2)}</td>
            <td><strong>$${day.close.toFixed(2)}</strong></td>
            <td class="${changeClass}">${day.changeFormatted}</td>
            <td class="${changeClass}">${day.changePercentFormatted}</td>
            <td>${formatVolume(day.volume)}</td>
        `;
        tableBody.appendChild(row);
    });
    
    updateRowCount();
}

// Function to update sort indicators
function updateSortIndicators() {
    // Remove all existing indicators
    document.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Map column names to table header indices
    const columnMap = {
        'date': 0,
        'open': 1,
        'high': 2,
        'low': 3,
        'close': 4,
        'change': 5,
        'changePercent': 6,
        'volume': 7
    };
    
    const thIndex = columnMap[sortColumn];
    if (thIndex !== undefined) {
        const th = document.querySelectorAll('th')[thIndex];
        th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
    }
}

// Update row count
function updateRowCount() {
    const rowCount = document.getElementById('rowCount');
    if (rowCount) {
        rowCount.textContent = `Showing ${processedData.length} rows`;
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

// Function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Export to CSV function
function exportToCSV() {
    if (processedData.length === 0) {
        showError('No data to export');
        return;
    }
    
    // Create CSV header
    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Change', 'Change %', 'Volume'];
    const csvRows = [headers.join(',')];
    
    // Add data rows
    processedData.forEach(day => {
        const row = [
            day.date,
            day.open.toFixed(2),
            day.high.toFixed(2),
            day.low.toFixed(2),
            day.close.toFixed(2),
            day.change.toFixed(2),
            day.changePercent.toFixed(2),
            day.volume
        ];
        csvRows.push(row.join(','));
    });
    
    // Create CSV string
    const csvString = csvRows.join('\n');
    
    // Create download link
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentSymbol}_stock_data_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Load available symbols on page load
async function loadAvailableSymbols() {
    try {
        const response = await fetch('/api/available-symbols');
        const data = await response.json();
        
        if (data.symbols && data.symbols.length > 0) {
            const symbolInput = document.getElementById('symbolInput');
            const symbolsList = data.symbols.map(s => s.symbol).join(', ');
            symbolInput.placeholder = `Enter symbol (e.g., ${data.symbols.slice(0, 3).map(s => s.symbol).join(', ')})`;
        }
    } catch (error) {
        console.error('Error loading available symbols:', error);
    }
}

// Allow Enter key to trigger fetch
document.getElementById('symbolInput').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        fetchStockData();
    }
});

// Load available symbols when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadAvailableSymbols();
});