// Global variables
let currentData = [];
let processedData = [];
let sortColumn = 'date';
let sortDirection = 'desc';
let currentSymbol = '';

// Main function to fetch stock data
async function fetchStockData() {
    const symbolInput = document.getElementById('symbolInput');
    const fetchBtn = document.getElementById('fetchBtn');
    const errorMessage = document.getElementById('errorMessage');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultSection = document.getElementById('resultSection');
    const symbol = symbolInput.value.trim().toUpperCase();

    if (!symbol) {
        showError('Please enter a stock symbol');
        return;
    }

    errorMessage.classList.remove('show');
    resultSection.classList.remove('show');
    loadingSpinner.classList.add('show');
    fetchBtn.disabled = true;

    try {
        const response = await fetch('/api/stock-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol })
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch data');
        }

        currentData = data.data; // The API response now merges everything into 'data'
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

// Process data for display (add calculated fields)
function processDataForDisplay() {
    processedData = currentData.map(day => {
        const change = day.close - day.open;
        const changePercent = (day.open !== 0) ? (change / day.open) * 100 : 0;
        return {
            ...day,
            change,
            changePercent,
            changeFormatted: `${change >= 0 ? '+' : ''}$${change.toFixed(2)}`,
            changePercentFormatted: `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`
        };
    });
    sortData(sortColumn, false);
}

// Sort data logic
function sortData(column, reRender = true) {
    if (sortColumn === column && reRender) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else if (reRender) {
        sortColumn = column;
        sortDirection = (column === 'date') ? 'desc' : 'asc';
    }

    processedData.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];
        if (column === 'date') {
            return sortDirection === 'asc' ? new Date(aVal) - new Date(bVal) : new Date(bVal) - new Date(aVal);
        }
        aVal = (aVal === null || aVal === undefined) ? -Infinity : parseFloat(aVal);
        bVal = (bVal === null || bVal === undefined) ? -Infinity : parseFloat(bVal);
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

    if (reRender) {
        renderTable();
        updateSortIndicators();
    }
}

// Display results section and header
function displayStockData(symbol) {
    const stockSymbol = document.getElementById('stockSymbol');
    const dataCount = document.getElementById('dataCount');
    const resultSection = document.getElementById('resultSection');
    stockSymbol.textContent = symbol;

    if (processedData.length > 0) {
        const dates = processedData.map(d => new Date(d.date));
        const oldestDate = new Date(Math.min(...dates));
        const newestDate = new Date(Math.max(...dates));
        const years = ((newestDate - oldestDate) / (365.25 * 24 * 60 * 60 * 1000)).toFixed(1);
        dataCount.textContent = `${processedData.length} trading days • ${years} years`;
    } else {
        dataCount.textContent = '0 days of data';
    }

    renderTable();
    updateSortIndicators();
    resultSection.classList.add('show');
}

// Render the main data table
function renderTable() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';

    processedData.forEach(day => {
        const row = document.createElement('tr');
        const changeClass = day.change >= 0 ? 'positive' : 'negative';

        // Get highlight classes directly from each day's data object
        const class5Day = day.highlight_5_day === 'red' ? 'highlight-red' : day.highlight_5_day === 'green' ? 'highlight-green' : '';
        const class10Day = day.highlight_10_day === 'red' ? 'highlight-red' : day.highlight_10_day === 'green' ? 'highlight-green' : '';
        
        // Helper to format whole numbers (integers) sent from the backend
        const formatInt = (num) => num !== null ? num : 'N/A';

        row.innerHTML = `
            <td><strong>${formatDate(day.date)}</strong></td>
            <td>$${day.open.toFixed(2)}</td>
            <td>$${day.high.toFixed(2)}</td>
            <td>$${day.low.toFixed(2)}</td>
            <td><strong>$${day.close.toFixed(2)}</strong></td>
            <td class="${changeClass}">${day.changeFormatted}</td>
            <td class="${changeClass}">${day.changePercentFormatted}</td>
            <td>${formatVolume(day.volume)}</td>
            <td>${formatInt(day.rsi_2)}</td>
            <td class="${class5Day}">${formatInt(day.rsi_2_avg_5)}</td>
            <td class="${class10Day}">${formatInt(day.rsi_2_avg_10)}</td>
        `;
        tableBody.appendChild(row);
    });
    updateRowCount();
}

// Update sorting arrows in table headers
function updateSortIndicators() {
    document.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
    const columnMap = {
        'date': 0, 'open': 1, 'high': 2, 'low': 3, 'close': 4,
        'change': 5, 'changePercent': 6, 'volume': 7,
        'rsi_2': 8, 'rsi_2_avg_5': 9, 'rsi_2_avg_10': 10
    };
    const th = document.querySelectorAll('th')[columnMap[sortColumn]];
    if (th) {
        th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
    }
}

// Update the row count display
function updateRowCount() {
    document.getElementById('rowCount').textContent = `Showing ${processedData.length} rows`;
}

// Show an error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// Utility functions for formatting
const formatVolume = (vol) => {
    if (!vol) return 'N/A';
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(2)}B`;
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(2)}M`;
    if (vol >= 1e3) return `${(vol / 1e3).toFixed(2)}K`;
    return vol.toLocaleString();
};

const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' });
};

// Export data to CSV
function exportToCSV() {
    if (processedData.length === 0) return showError('No data to export.');
    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Change', 'Change %', 'Volume', 'RSI(2)', '5-Day Avg RSI(2)', '10-Day Avg RSI(2)'];
    const csvRows = [headers.join(',')];
    processedData.forEach(day => {
        const row = [
            day.date, day.open.toFixed(2), day.high.toFixed(2), day.low.toFixed(2), day.close.toFixed(2),
            day.change.toFixed(2), day.changePercent.toFixed(2), day.volume,
            day.rsi_2 ?? '', day.rsi_2_avg_5 ?? '', day.rsi_2_avg_10 ?? ''
        ];
        csvRows.push(row.join(','));
    });
    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentSymbol}_data_with_rsi_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Event listener for Enter key
document.getElementById('symbolInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        fetchStockData();
    }
});

// Any initial setup on page load can go here
document.addEventListener('DOMContentLoaded', () => {
    // e.g., loadAvailableSymbols();
});