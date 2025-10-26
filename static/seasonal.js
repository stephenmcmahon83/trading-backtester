/**
 * Gets the CSS class for the Average Return heatmap (top table).
 * @param {number} percentage - The average return as a percentage.
 * @returns {string} The CSS class name.
 */
function getReturnHeatmapClass(percentage) {
    if (percentage <= -0.5) return 'heat-ret-neg-high';
    if (percentage < 0) return 'heat-ret-neg-med';
    if (percentage < 0.05) return 'heat-ret-neg-low'; // Near zero
    if (percentage < 0.5) return 'heat-ret-pos-low';
    if (percentage < 1.0) return 'heat-ret-pos-med';
    return 'heat-ret-pos-high';
}

/**
 * Gets the CSS class for the Win Rate heatmap (bottom table).
 * @param {number} percentage - The win rate percentage.
 * @returns {string} The CSS class name.
 */
function getWinRateHeatmapClass(percentage) {
    if (percentage < 40) return 'heat-0-40';
    if (percentage < 45) return 'heat-40-45';
    if (percentage < 50) return 'heat-45-50';
    if (percentage < 55) return 'heat-50-55';
    if (percentage < 60) return 'heat-55-60';
    if (percentage < 65) return 'heat-60-65';
    if (percentage < 70) return 'heat-65-70';
    return 'heat-70-100';
}

function renderSeasonalTables(data) {
    const avgReturnBody = document.getElementById('avgReturnBody');
    const winRateBody = document.getElementById('winRateBody');
    avgReturnBody.innerHTML = '';
    winRateBody.innerHTML = '';

    // --- CORRECTED: Get today's date to find the matching 2025 date string ---
    const today = new Date();
    const targetDateStr = today.toLocaleString('en-US', { month: 'short', day: 'numeric' }) + ", 2025";
    
    data.forEach(day => {
        const isTodayRow = day.date === targetDateStr;

        // --- Row for Average Return Table (with new heatmap) ---
        const avgReturnRow = document.createElement('tr');
        if (isTodayRow) avgReturnRow.classList.add('highlight-today');
        
        let avgReturnCells = `<td><strong>${day.date}</strong></td><td>${day.tradingDayNum}</td><td>${day.tradeCount}</td>`;
        day.avgReturns.forEach(ret => {
            const value = ret * 100;
            const heatmapClass = getReturnHeatmapClass(value);
            const sign = value > 0 ? '+' : '';
            avgReturnCells += `<td class="heat-return ${heatmapClass}">${sign}${value.toFixed(2)}%</td>`;
        });
        avgReturnRow.innerHTML = avgReturnCells;
        avgReturnBody.appendChild(avgReturnRow);

        // --- Row for Win Rate Table ---
        const winRateRow = document.createElement('tr');
        if (isTodayRow) winRateRow.classList.add('highlight-today');

        let winRateCells = `<td><strong>${day.date}</strong></td><td>${day.tradingDayNum}</td><td>${day.tradeCount}</td>`;
        day.winRates.forEach(rate => {
            const value = rate * 100;
            const heatmapClass = getWinRateHeatmapClass(value);
            winRateCells += `<td class="heat-cell ${heatmapClass}">${value.toFixed(0)}%</td>`;
        });
        winRateRow.innerHTML = winRateCells;
        winRateBody.appendChild(winRateRow);
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultSection = document.getElementById('resultSection');
    const symbol = 'SPY'; 

    try {
        const response = await fetch(`/api/seasonal-data?symbol=${symbol}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.length > 0) {
            renderSeasonalTables(data);
            document.getElementById('stats1').textContent = `Based on ${data[0].tradeCount} years of data`;
        } else {
            document.getElementById('avgReturnBody').innerHTML = '<tr><td colspan="18">No seasonal data could be calculated.</td></tr>';
        }

    } catch (error) {
        console.error("Error fetching seasonal data:", error);
        document.getElementById('avgReturnBody').innerHTML = `<tr><td colspan="18">Failed to load data: ${error.message}</td></tr>`;
    } finally {
        loadingSpinner.classList.remove('show');
        resultSection.classList.add('show');
    }
});