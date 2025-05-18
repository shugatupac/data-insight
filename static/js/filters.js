/**
 * Data filtering functionality for Excel Data Analyzer
 */

// Store filter state
const filterState = {
    activeFilters: {}
};

/**
 * Initialize the data filtering UI and event handlers
 */
function initializeFilteringUI() {
    // Add event listeners to filter field selection
    const filterField = document.getElementById('filterField');
    if (filterField) {
        filterField.addEventListener('change', handleFilterFieldSelection);
    }
    
    // Add event listeners to filter buttons
    const applyFilterBtn = document.getElementById('applyFilterBtn');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', applyFilter);
    }
    
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', resetFilters);
    }
    
    // Add event listeners to filter input fields for real-time validation
    const minValue = document.getElementById('minValue');
    const maxValue = document.getElementById('maxValue');
    const textContains = document.getElementById('textContains');
    const categoricalValue = document.getElementById('categoricalValue');
    
    if (minValue) minValue.addEventListener('input', validateFilterInputs);
    if (maxValue) maxValue.addEventListener('input', validateFilterInputs);
    if (textContains) textContains.addEventListener('input', validateFilterInputs);
    if (categoricalValue) categoricalValue.addEventListener('input', validateFilterInputs);
}

/**
 * Handle filter field selection change
 */
function handleFilterFieldSelection() {
    const filterField = document.getElementById('filterField');
    const fieldType = filterField.options[filterField.selectedIndex].dataset.type;
    const filterValue = filterField.value;
    
    const filterOptionsContainer = document.getElementById('filterOptionsContainer');
    const numericFilterOptions = document.getElementById('numericFilterOptions');
    const textFilterOptions = document.getElementById('textFilterOptions');
    const categoricalFilterOptions = document.getElementById('categoricalFilterOptions');
    
    // Hide all filter options initially
    filterOptionsContainer.style.display = 'none';
    numericFilterOptions.style.display = 'none';
    textFilterOptions.style.display = 'none';
    categoricalFilterOptions.style.display = 'none';
    
    // Clear previous filter inputs
    document.getElementById('minValue').value = '';
    document.getElementById('maxValue').value = '';
    document.getElementById('textContains').value = '';
    document.getElementById('categoricalValue').value = '';
    
    // Enable Apply Filter button only if a field is selected
    document.getElementById('applyFilterBtn').disabled = !filterValue;
    
    if (!filterValue) {
        return;
    }
    
    // Show appropriate filter options based on field type
    filterOptionsContainer.style.display = 'block';
    
    if (fieldType === 'numeric') {
        numericFilterOptions.style.display = 'block';
    } else if (fieldType === 'text') {
        textFilterOptions.style.display = 'block';
    } else if (fieldType === 'categorical' || fieldType === 'datetime') {
        categoricalFilterOptions.style.display = 'block';
    }
}

/**
 * Validate filter inputs in real-time
 */
function validateFilterInputs() {
    const filterField = document.getElementById('filterField');
    const fieldType = filterField.options[filterField.selectedIndex].dataset.type;
    const filterValue = filterField.value;
    
    let isValid = false;
    
    if (fieldType === 'numeric') {
        const minValue = document.getElementById('minValue').value.trim();
        const maxValue = document.getElementById('maxValue').value.trim();
        isValid = minValue !== '' || maxValue !== '';
    } else if (fieldType === 'text') {
        const textContains = document.getElementById('textContains').value.trim();
        isValid = textContains !== '';
    } else if (fieldType === 'categorical' || fieldType === 'datetime') {
        const categoricalValue = document.getElementById('categoricalValue').value.trim();
        isValid = categoricalValue !== '';
    }
    
    // Update apply button state
    document.getElementById('applyFilterBtn').disabled = !isValid || !filterValue;
}

/**
 * Apply the selected filter to the data
 */
function applyFilter() {
    const filterField = document.getElementById('filterField');
    const fieldName = filterField.value;
    const fieldType = filterField.options[filterField.selectedIndex].dataset.type;
    
    if (!fieldName) {
        return;
    }
    
    let filterValue;
    
    // Create filter based on field type
    if (fieldType === 'numeric') {
        const minValue = document.getElementById('minValue').value.trim();
        const maxValue = document.getElementById('maxValue').value.trim();
        
        if (minValue === '' && maxValue === '') {
            return;
        }
        
        filterValue = {};
        if (minValue !== '') {
            filterValue.min = parseFloat(minValue);
        }
        if (maxValue !== '') {
            filterValue.max = parseFloat(maxValue);
        }
    } else if (fieldType === 'text') {
        const textContains = document.getElementById('textContains').value.trim();
        
        if (textContains === '') {
            return;
        }
        
        filterValue = { contains: textContains };
    } else if (fieldType === 'categorical' || fieldType === 'datetime') {
        const categoricalValue = document.getElementById('categoricalValue').value.trim();
        
        if (categoricalValue === '') {
            return;
        }
        
        filterValue = categoricalValue;
    }
    
    // Store the filter
    filterState.activeFilters[fieldName] = {
        type: fieldType,
        value: filterValue,
        displayValue: getFilterDisplayValue(fieldName, fieldType, filterValue)
    };
    
    // Send filter to server
    submitFilters();
}

/**
 * Get human-readable display value for a filter
 */
function getFilterDisplayValue(fieldName, fieldType, filterValue) {
    if (fieldType === 'numeric') {
        let display = '';
        if ('min' in filterValue) {
            display += `≥ ${filterValue.min}`;
        }
        if ('min' in filterValue && 'max' in filterValue) {
            display += ' and ';
        }
        if ('max' in filterValue) {
            display += `≤ ${filterValue.max}`;
        }
        return display;
    } else if (fieldType === 'text') {
        return `contains "${filterValue.contains}"`;
    } else {
        return `= "${filterValue}"`;
    }
}

/**
 * Submit all active filters to the server
 */
function submitFilters() {
    // Create filters object
    const filters = {};
    Object.keys(filterState.activeFilters).forEach(field => {
        filters[field] = filterState.activeFilters[field].value;
    });
    
    // Show loading state
    document.getElementById('applyFilterBtn').disabled = true;
    document.getElementById('applyFilterBtn').innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Applying...';
    
    // Send request to server
    fetch('/filter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filters })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Error applying filters');
            }).catch(err => {
                throw new Error('Error applying filters: ' + err.message);
            });
        }
        return response.json();
    })
    .then(data => {
        // Update the UI with filtered data
        updateDataPreview(data.preview_data);
        document.getElementById('totalRowsCount').textContent = data.total_rows;
        
        // Update filter badges
        updateActiveFiltersDisplay();
        
        // Enable reset filters button
        document.getElementById('resetFiltersBtn').disabled = false;
        
        // Show success message
        showFilterAlert('success', data.message);
    })
    .catch(error => {
        console.error('Error applying filters:', error);
        showFilterAlert('danger', `Error applying filters: ${error.message}`);
    })
    .finally(() => {
        // Reset button state
        document.getElementById('applyFilterBtn').disabled = false;
        document.getElementById('applyFilterBtn').innerHTML = '<i class="fas fa-filter me-1"></i> Apply Filter';
    });
}

/**
 * Update the data preview table with filtered data
 */
function updateDataPreview(previewData) {
    const table = document.querySelector('.table');
    if (!table || !previewData || !previewData.length) {
        return;
    }
    
    const tbody = table.querySelector('tbody');
    const columns = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add new rows
    previewData.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(column => {
            const td = document.createElement('td');
            td.textContent = row[column] !== null ? row[column] : '';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

/**
 * Show a filter operation alert message
 */
function showFilterAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-2`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find container and add alert
    const container = document.querySelector('.card-body');
    container.insertBefore(alertDiv, document.getElementById('filterOptionsContainer'));
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 5000);
}

/**
 * Update the active filters display
 */
function updateActiveFiltersDisplay() {
    const activeFiltersContainer = document.getElementById('activeFiltersContainer');
    const activeFiltersList = document.getElementById('activeFiltersList');
    const activeFiltersCount = document.getElementById('activeFiltersCount');
    
    const filterCount = Object.keys(filterState.activeFilters).length;
    
    // Update count badge
    activeFiltersCount.textContent = `${filterCount} active ${filterCount === 1 ? 'filter' : 'filters'}`;
    activeFiltersCount.style.display = filterCount > 0 ? 'inline-block' : 'none';
    
    // Show/hide container
    activeFiltersContainer.style.display = filterCount > 0 ? 'block' : 'none';
    
    if (filterCount === 0) {
        return;
    }
    
    // Clear previous filters
    activeFiltersList.innerHTML = '';
    
    // Add filter badges
    Object.keys(filterState.activeFilters).forEach(field => {
        const filter = filterState.activeFilters[field];
        
        const badge = document.createElement('div');
        badge.className = 'badge bg-info text-dark p-2 d-inline-flex align-items-center';
        badge.innerHTML = `
            <span class="fw-bold me-1">${field}:</span>
            <span>${filter.displayValue}</span>
            <button type="button" class="btn-close btn-close-white ms-2" aria-label="Remove filter" data-field="${field}"></button>
        `;
        
        // Add click handler for removing filter
        badge.querySelector('.btn-close').addEventListener('click', () => {
            removeFilter(field);
        });
        
        activeFiltersList.appendChild(badge);
    });
}

/**
 * Remove a specific filter
 */
function removeFilter(field) {
    if (field in filterState.activeFilters) {
        delete filterState.activeFilters[field];
        submitFilters();
    }
}

/**
 * Reset all active filters
 */
function resetFilters() {
    // Clear all active filters
    filterState.activeFilters = {};
    
    // Reset filter UI elements
    document.getElementById('filterField').value = '';
    document.getElementById('filterOptionsContainer').style.display = 'none';
    document.getElementById('applyFilterBtn').disabled = true;
    document.getElementById('resetFiltersBtn').disabled = true;
    
    // Update filters display
    updateActiveFiltersDisplay();
    
    // Submit empty filters to reset data
    submitFilters();
}

// Initialize filtering when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('filterField')) {
        initializeFilteringUI();
    }
});