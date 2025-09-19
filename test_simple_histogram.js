// Simple histogram test - standalone JavaScript that works
console.log('🔧 Loading simple histogram test...');

// Wait for the page to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - starting histogram test');

    // Wait a bit more to ensure everything is loaded
    setTimeout(function() {
        console.log('⏰ Delayed start - creating histogram');
        createWorkingHistogram();
    }, 1000);
});

async function createWorkingHistogram() {
    console.log('🚀 Starting working histogram creation...');

    try {
        // 1. Check if canvas exists
        const canvas = document.getElementById('valuePieChart');
        if (!canvas) {
            console.error('❌ Canvas element not found');
            return;
        }
        console.log('✅ Canvas element found:', canvas);

        // 2. Load data from API
        console.log('📡 Fetching data from API...');
        const response = await fetch('/api/opportunities?days=30');
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || 'API returned error');
        }

        const opportunities = data.opportunities;
        console.log('✅ Loaded', opportunities.length, 'opportunities');

        // 3. Prepare histogram data
        console.log('📊 Preparing histogram data...');
        const values = opportunities.map(opp => opp.totalValue || 0);
        const binSize = 50000;

        // Create bins
        const bins = new Map();
        values.forEach(value => {
            const binIndex = Math.floor(value / binSize);
            const binStart = binIndex * binSize;
            const binEnd = binStart + binSize;

            let label;
            if (binStart >= 1000000) {
                label = `$${(binStart/1000000).toFixed(1)}M - $${(binEnd/1000000).toFixed(1)}M`;
            } else {
                label = `$${(binStart/1000).toFixed(0)}K - $${(binEnd/1000).toFixed(0)}K`;
            }

            bins.set(label, (bins.get(label) || 0) + 1);
        });

        // Convert to arrays
        const labels = Array.from(bins.keys()).filter(key => bins.get(key) > 0);
        const counts = labels.map(label => bins.get(label));

        console.log('📈 Histogram data ready:', labels.length, 'bins');
        console.log('📊 Labels:', labels);
        console.log('📊 Counts:', counts);

        // 4. Create Chart.js chart
        console.log('🎨 Creating Chart.js chart...');

        // Destroy any existing chart
        if (window.existingChart) {
            window.existingChart.destroy();
        }

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Properties',
                    data: counts,
                    backgroundColor: '#ffd700',
                    borderColor: '#ffed4e',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Property Value Distribution ($50K Bins)',
                        color: '#ffffff',
                        font: { size: 14 }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Value Range',
                            color: '#ffffff'
                        },
                        ticks: {
                            color: '#ffffff',
                            maxRotation: 45
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
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
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });

        // Store reference
        window.existingChart = chart;

        console.log('✅ Chart created successfully!', chart);

        // Add success indicator to page
        const container = canvas.parentElement;
        if (container) {
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'color: #4CAF50; text-align: center; margin-top: 10px; font-size: 12px;';
            successMsg.textContent = `✅ Histogram showing ${opportunities.length} properties in ${labels.length} bins`;
            container.appendChild(successMsg);
        }

    } catch (error) {
        console.error('❌ Histogram creation failed:', error);

        // Show error on page
        const canvas = document.getElementById('valuePieChart');
        if (canvas) {
            const container = canvas.parentElement;
            if (container) {
                const errorMsg = document.createElement('div');
                errorMsg.style.cssText = 'color: #f44336; text-align: center; margin-top: 10px; font-size: 12px;';
                errorMsg.textContent = `❌ Chart failed: ${error.message}`;
                container.appendChild(errorMsg);
            }
        }
    }
}

console.log('📄 Simple histogram script loaded');