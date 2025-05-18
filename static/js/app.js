/**
 * Excel Data Analyzer App JavaScript
 * Handles all client-side interactions for data analysis and visualization
 */

// Store application state
const appState = {
    selectedField: null,
    selectedVisualizations: [],
    generatedVisualizations: {},
    exportConfig: {
        fields: [],
        visualizations: []
    },
    filters: {},
    activeFilters: {}
};

/**
 * Initialize the analysis page UI and event handlers
 */
function initializeAnalysisPage() {
    // Add event listeners to form elements
    document.getElementById('resetBtn').addEventListener('click', resetAnalysis);
    document.getElementById('analysisField').addEventListener('change', handleFieldSelection);
    document.getElementById('generateBtn').addEventListener('click', generateVisualizations);
    
    // Add event listeners to visualization checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateGenerateButtonState);
    });
    
    // Add event listeners to export buttons
    document.getElementById('exportPdfBtn').addEventListener('click', () => {
        exportResults('pdf');
    });
    document.getElementById('exportExcelBtn').addEventListener('click', () => {
        exportResults('excel');
    });
    
    // Initialize data filtering functionality
    initializeFilteringUI();
}

/**
 * Reset the analysis and return to file upload view
 */
function resetAnalysis() {
    window.location.href = '/';
}

/**
 * Handle field selection change
 */
function handleFieldSelection() {
    const selectedField = document.getElementById('analysisField').value;
    const fieldType = document.getElementById('analysisField').options[document.getElementById('analysisField').selectedIndex].dataset.type;
    
    appState.selectedField = selectedField;
    
    // Update generate button state
    updateGenerateButtonState();
    
    // Show recommendations based on field type
    showVisualizationRecommendations(fieldType);
}

/**
 * Show visualization recommendations based on field type
 */
function showVisualizationRecommendations(fieldType) {
    // Enable all checkboxes by default
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.disabled = false;
        cb.parentElement.classList.remove('text-muted');
    });
    
    // Apply specific recommendations based on field type
    if (fieldType === 'numeric') {
        // Numeric fields work well with bar charts
        document.getElementById('barChartCheck').checked = true;
    } else if (fieldType === 'categorical' || fieldType === 'text') {
        // Categorical fields work well with pie charts and frequency tables
        document.getElementById('freqTableCheck').checked = true;
        document.getElementById('pieChartCheck').checked = true;
    } else if (fieldType === 'datetime') {
        // Datetime fields work best with bar charts
        document.getElementById('barChartCheck').checked = true;
        
        // Disable inappropriate visualizations for datetime
        document.getElementById('pieChartCheck').disabled = true;
        document.getElementById('treemapCheck').disabled = true;
        document.getElementById('pieChartCheck').parentElement.classList.add('text-muted');
        document.getElementById('treemapCheck').parentElement.classList.add('text-muted');
    }
    
    // Update generate button state
    updateGenerateButtonState();
}

/**
 * Update the state of the generate button based on selections
 */
function updateGenerateButtonState() {
    const field = document.getElementById('analysisField').value;
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    const generateBtn = document.getElementById('generateBtn');
    
    // Update selected visualizations array
    appState.selectedVisualizations = Array.from(checkboxes).map(cb => cb.value);
    
    // Enable button only if a field is selected and at least one visualization type
    generateBtn.disabled = !(field && checkboxes.length > 0);
}

/**
 * Generate visualizations based on user selections
 */
function generateVisualizations() {
    // Show loading state
    const visualizationsContainer = document.getElementById('visualizationsContainer');
    visualizationsContainer.style.display = 'block';
    document.getElementById('loadingVisualizations').style.display = 'block';
    document.getElementById('visualizationResults').innerHTML = '';
    
    // Prepare request data
    const requestData = {
        field: appState.selectedField,
        visualization_types: appState.selectedVisualizations
    };
    
    // Send AJAX request
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Network response was not ok');
            }).catch(err => {
                throw new Error('Network response was not ok: ' + err.message);
            });
        }
        return response.json();
    })
    .then(data => {
        // Save generated visualizations
        appState.generatedVisualizations = data;
        
        // Update export config
        appState.exportConfig = {
            fields: [appState.selectedField],
            visualizations: appState.selectedVisualizations.map(type => ({
                field: appState.selectedField,
                type: type
            }))
        };
        
        // Display visualizations
        displayVisualizations(data);
    })
    .catch(error => {
        console.error('Error generating visualizations:', error);
        document.getElementById('visualizationResults').innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    Error generating visualizations: ${error.message}
                </div>
            </div>
        `;
    })
    .finally(() => {
        document.getElementById('loadingVisualizations').style.display = 'none';
    });
}

/**
 * Display generated visualizations in the results container
 */
function displayVisualizations(visualizationsData) {
    const resultsContainer = document.getElementById('visualizationResults');
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Process each visualization type
    Object.keys(visualizationsData).forEach(vizType => {
        const vizData = visualizationsData[vizType];
        
        // Create container for this visualization
        const vizContainer = document.createElement('div');
        
        // Set column width based on visualization type
        if (vizType === 'frequency_table') {
            vizContainer.className = 'col-12 mb-4';
        } else {
            vizContainer.className = 'col-md-6 mb-4';
        }
        
        // Create card for visualization
        const vizCard = document.createElement('div');
        vizCard.className = 'card h-100';
        
        // Create card header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        
        let vizTitle = '';
        let vizIcon = '';
        
        switch (vizType) {
            case 'frequency_table':
                vizTitle = 'Frequency Table';
                vizIcon = 'fa-table';
                break;
            case 'pie_chart':
                vizTitle = 'Pie Chart';
                vizIcon = 'fa-chart-pie';
                break;
            case 'bar_chart':
                vizTitle = 'Bar Chart';
                vizIcon = 'fa-chart-bar';
                break;
            case 'treemap':
                vizTitle = 'Treemap';
                vizIcon = 'fa-th-large';
                break;
        }
        
        cardHeader.innerHTML = `
            <h5 class="card-title mb-0">
                <i class="fas ${vizIcon} me-2"></i>
                ${vizTitle}: ${vizData.field}
            </h5>
        `;
        
        // Create card body
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Add content based on visualization type
        if (vizType === 'frequency_table') {
            // Create a table for frequency data
            const tableContainer = document.createElement('div');
            tableContainer.className = 'table-responsive';
            
            const table = document.createElement('table');
            table.className = 'table table-striped table-hover';
            
            // Create table header
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>Value</th>
                    <th>Count</th>
                    <th>Percentage (%)</th>
                </tr>
            `;
            
            // Create table body
            const tbody = document.createElement('tbody');
            
            // Check if we have data
            if (vizData.data && vizData.data.length > 0) {
                for (const row of vizData.data) {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.value}</td>
                        <td>${row.count}</td>
                        <td>${row.percentage}%</td>
                    `;
                    tbody.appendChild(tr);
                }
            } else {
                // No data message
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td colspan="3" class="text-center">No data available for this selection</td>
                `;
                tbody.appendChild(tr);
            }
            
            table.appendChild(thead);
            table.appendChild(tbody);
            tableContainer.appendChild(table);
            cardBody.appendChild(tableContainer);
            
        } else {
            // Check if there's an error message
            if (vizData.error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'alert alert-warning';
                errorDiv.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${vizData.error}
                `;
                cardBody.appendChild(errorDiv);
            } else if (vizData.data && vizData.data.data) {
                // For charts, create a div for plotly
                const plotDiv = document.createElement('div');
                plotDiv.className = 'plot-container';
                plotDiv.style.height = '400px';
                plotDiv.id = `plot-${vizType}-${Date.now()}`;
                
                cardBody.appendChild(plotDiv);
                
                // Defer the plot creation until after the container is added to the DOM
                setTimeout(() => {
                    try {
                        Plotly.newPlot(plotDiv.id, vizData.data.data, vizData.data.layout || {});
                    } catch (e) {
                        console.error(`Error plotting ${vizType}:`, e);
                        plotDiv.innerHTML = `
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-circle me-2"></i>
                                Error displaying visualization
                            </div>
                        `;
                    }
                }, 0);
            } else {
                // No data available
                const noDataDiv = document.createElement('div');
                noDataDiv.className = 'alert alert-info';
                noDataDiv.innerHTML = `
                    <i class="fas fa-info-circle me-2"></i>
                    No data available for this visualization
                `;
                cardBody.appendChild(noDataDiv);
            }
        }
        
        // Assemble the card
        vizCard.appendChild(cardHeader);
        vizCard.appendChild(cardBody);
        vizContainer.appendChild(vizCard);
        
        // Add to results container
        resultsContainer.appendChild(vizContainer);
    });
}

/**
 * Export analysis results to PDF or Excel
 */
function exportResults(exportType) {
    // Show export processing modal
    const exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
    exportModal.show();
    
    // Prepare request data
    const requestData = {
        export_type: exportType,
        fields: appState.exportConfig.fields,
        visualizations: appState.exportConfig.visualizations
    };
    
    // Send AJAX request
    fetch('/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Hide export modal
        exportModal.hide();
        
        // Show download modal
        const downloadModal = new bootstrap.Modal(document.getElementById('downloadModal'));
        
        // Set download link
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = data.download_url;
        
        // Set file type in modal
        document.getElementById('downloadModalLabel').textContent = 
            `Export Complete (${exportType.toUpperCase()})`;
        
        downloadModal.show();
    })
    .catch(error => {
        console.error('Error exporting results:', error);
        
        // Hide export modal
        exportModal.hide();
        
        // Show error message
        alert(`Error exporting results: ${error.message}`);
    });
}
