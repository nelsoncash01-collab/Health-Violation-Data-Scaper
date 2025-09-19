// Global variables
let allOpportunities = [];
let histogramChart = null;

// Auto-load opportunities when page loads
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Page loaded, fetching opportunities...');
    await loadOpportunities();

    // Set up sort control event listener
    document.getElementById('sortSelect').addEventListener('change', (e) => {
        sortOpportunities(e.target.value);
    });
});

async function loadOpportunities() {
    try {
        // Use the same API call that worked with the test load button
        const response = await fetch('https://health-violation-data-scaper-backend.onrender.com/api/opportunities?days=30&quick=false&auto=' + Date.now());

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('API Response:', data);

        if (data && data.success && data.opportunities && data.opportunities.length > 0) {
            allOpportunities = data.opportunities;
            // Start with default sort (value high to low)
            sortOpportunities('value_desc');
            // Create histogram
            createHistogram();
        } else {
            showError('No opportunities found');
        }
    } catch (error) {
        console.error('Error loading opportunities:', error);
        showError('Failed to load opportunities: ' + error.message);
    }
}

function sortOpportunities(sortType) {
    if (!allOpportunities || allOpportunities.length === 0) return;

    let sortedOpportunities = [...allOpportunities];

    switch(sortType) {
        case 'value_desc':
            sortedOpportunities.sort((a, b) => b.totalValue - a.totalValue);
            break;
        case 'value_asc':
            sortedOpportunities.sort((a, b) => a.totalValue - b.totalValue);
            break;
        case 'name_asc':
            sortedOpportunities.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'name_desc':
            sortedOpportunities.sort((a, b) => b.name.localeCompare(a.name));
            break;
        case 'date_desc':
            sortedOpportunities.sort((a, b) => new Date(b.violationDate) - new Date(a.violationDate));
            break;
        case 'date_asc':
            sortedOpportunities.sort((a, b) => new Date(a.violationDate) - new Date(b.violationDate));
            break;
    }

    displayOpportunities(sortedOpportunities);
    console.log(`Sorted opportunities by ${sortType}`);
}

function displayOpportunities(opportunities) {
    const listContainer = document.getElementById('opportunitiesList');

    // Clear loading message
    listContainer.innerHTML = '';

    // Display each opportunity
    opportunities.forEach(opportunity => {
        const opportunityElement = document.createElement('div');
        opportunityElement.className = 'opportunity';
        opportunityElement.onclick = () => selectOpportunity(opportunity);

        opportunityElement.innerHTML = `
            <div class="opportunity-name">${opportunity.name}</div>
            <div class="opportunity-value">${formatCurrency(opportunity.totalValue)}</div>
            <div class="opportunity-address">${opportunity.address}, ${opportunity.neighborhood}</div>
        `;

        listContainer.appendChild(opportunityElement);
    });

    console.log(`Displayed ${opportunities.length} opportunities`);
}

function selectOpportunity(opportunity) {
    console.log('Selected opportunity:', opportunity.name);
    showPropertyDetails(opportunity);
}

function showPropertyDetails(opportunity) {
    const detailsContainer = document.getElementById('propertyDetails');

    detailsContainer.innerHTML = `
        <div class="property-name">${opportunity.name}</div>
        <div class="property-value">${formatCurrency(opportunity.totalValue)}</div>

        <div class="property-info">
            <p><strong>Address:</strong> ${opportunity.address}</p>
            <p><strong>Neighborhood:</strong> ${opportunity.neighborhood}</p>
            <p><strong>Borough:</strong> ${opportunity.borough}</p>
            <p><strong>Square Footage:</strong> ${opportunity.sqft?.toLocaleString() || 'N/A'} sq ft</p>
            <p><strong>Price per Sq Ft:</strong> $${opportunity.pricePerSqft || 'N/A'}</p>
            <p><strong>Violation Date:</strong> ${opportunity.violationDate}</p>
            <p><strong>Violation Type:</strong> ${opportunity.violationType || 'Health Violation'}</p>
            <p><strong>ML Confidence:</strong> ${opportunity.mlConfidence || 'N/A'}%</p>
        </div>

        <button class="owner-button" onclick="getOwnerInfo('${opportunity.address}', '${opportunity.borough}')">
            Get Owner Name & Phone Number
        </button>
    `;
}

async function getOwnerInfo(address, borough) {
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Loading...';
    button.disabled = true;

    try {
        const response = await fetch('https://health-violation-data-scaper-backend.onrender.com/api/property-owner', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, borough })
        });

        const result = await response.json();

        if (result.success && result.owner && result.owner !== 'Owner lookup failed') {
            alert(`Property Owner: ${result.owner}\n\nPhone: ${result.phone || 'Not available'}\n\nAddress: ${address}, ${borough}`);
        } else {
            alert(`Owner information not available for:\n${address}, ${borough}`);
        }
    } catch (error) {
        console.error('Owner lookup failed:', error);
        alert(`Owner lookup failed: ${error.message}`);
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

function formatCurrency(amount) {
    if (amount >= 1000000) {
        return '$' + (amount / 1000000).toFixed(1) + 'M';
    } else if (amount >= 1000) {
        return '$' + (amount / 1000).toFixed(0) + 'K';
    }
    return '$' + amount.toLocaleString();
}

function createHistogram() {
    if (!allOpportunities || allOpportunities.length === 0) return;

    const ctx = document.getElementById('histogramChart').getContext('2d');

    // Create $50K bins
    const binSize = 50000;
    const values = allOpportunities.map(opp => opp.totalValue || 0);
    const maxValue = Math.max(...values);
    const numBins = Math.ceil(maxValue / binSize);

    // Initialize bins
    const bins = {};
    const labels = [];

    for (let i = 0; i <= numBins; i++) {
        const binStart = i * binSize;
        const binEnd = (i + 1) * binSize;
        const label = formatValueRange(binStart, binEnd);
        labels.push(label);
        bins[label] = 0;
    }

    // Count opportunities in each bin
    allOpportunities.forEach(opp => {
        const value = opp.totalValue || 0;
        const binIndex = Math.floor(value / binSize);
        const binStart = binIndex * binSize;
        const binEnd = (binIndex + 1) * binSize;
        const label = formatValueRange(binStart, binEnd);

        if (bins[label] !== undefined) {
            bins[label]++;
        }
    });

    // Filter out empty bins
    const nonEmptyLabels = [];
    const nonEmptyData = [];

    labels.forEach(label => {
        if (bins[label] > 0) {
            nonEmptyLabels.push(label);
            nonEmptyData.push(bins[label]);
        }
    });

    // Destroy existing chart if it exists
    if (histogramChart) {
        histogramChart.destroy();
    }

    // Create histogram
    histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: nonEmptyLabels,
            datasets: [{
                label: 'Number of Properties',
                data: nonEmptyData,
                backgroundColor: '#ffd700',
                borderColor: '#ffed4e',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Property Value Range',
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff',
                        maxRotation: 45
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of Properties',
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff',
                        stepSize: 1
                    }
                }
            }
        }
    });

    console.log('Histogram created with', nonEmptyData.length, 'bins');
}

function formatValueRange(start, end) {
    const formatValue = (value) => {
        if (value >= 1000000) {
            return '$' + (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return '$' + (value / 1000).toFixed(0) + 'K';
        } else {
            return '$' + value.toLocaleString();
        }
    };

    return formatValue(start) + ' - ' + formatValue(end);
}

function exportToExcel() {
    if (!allOpportunities || allOpportunities.length === 0) {
        alert('No data to export');
        return;
    }

    // Create CSV content
    const headers = ['Name', 'Address', 'Borough', 'Neighborhood', 'Total Value', 'Price per SqFt', 'Square Feet', 'Violation Date', 'Violation Type', 'ML Confidence'];

    const rows = allOpportunities.map(opp => [
        opp.name,
        opp.address,
        opp.borough,
        opp.neighborhood,
        opp.totalValue,
        opp.pricePerSqft || 'N/A',
        opp.sqft || 'N/A',
        opp.violationDate,
        opp.violationType || 'Health Violation',
        opp.mlConfidence || 'N/A'
    ]);

    const csvContent = [headers, ...rows]
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `nyc_opportunities_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    console.log('Exported', allOpportunities.length, 'opportunities to CSV');
}

function showError(message) {
    const listContainer = document.getElementById('opportunitiesList');
    listContainer.innerHTML = `
        <div style="text-align: center; color: #ff6b6b; padding: 20px;">
            <p>Error: ${message}</p>
        </div>
    `;
}