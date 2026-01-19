// Quote Summary JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeQuoteSummary();
});

function initializeQuoteSummary() {
    // Initialize selection strategy handler
    const selectionStrategy = document.getElementById('selectionStrategy');
    if (selectionStrategy) {
        selectionStrategy.addEventListener('change', handleSelectionStrategyChange);
    }
    
    // Initialize form submission
    const quoteForm = document.getElementById('quoteSelectionForm');
    if (quoteForm) {
        quoteForm.addEventListener('submit', handleQuoteSelection);
    }
    
    // Initialize table sorting
    initializeTableSorting();
    
    // Update selection summary
    updateSelectionSummary();
    
    // Auto-refresh quote status every 30 seconds
    setInterval(refreshQuoteStatus, 30000);
}

function handleSelectionStrategyChange(event) {
    const strategy = event.target.value;
    const customPanel = document.getElementById('customSelectionPanel');
    
    if (strategy === 'custom') {
        customPanel.classList.remove('d-none');
        populateCustomSelectionTable();
    } else {
        customPanel.classList.add('d-none');
        applySelectionStrategy(strategy);
    }
    
    updateSelectionSummary();
}

function applySelectionStrategy(strategy) {
    const parts = document.querySelectorAll('[data-part-id]');
    
    parts.forEach(row => {
        const partId = row.dataset.partId;
        let selectedQuote = null;
        
        switch (strategy) {
            case 'recommended':
                selectedQuote = getRecommendedQuote(partId);
                break;
            case 'lowest_cost':
                selectedQuote = getLowestCostQuote(partId);
                break;
            case 'fastest_completion':
                selectedQuote = getFastestCompletionQuote(partId);
                break;
            case 'highest_quality':
                selectedQuote = getHighestQualityQuote(partId);
                break;
        }
        
        if (selectedQuote) {
            selectQuoteForPart(partId, selectedQuote);
        }
    });
}

function getRecommendedQuote(partId) {
    // Get the quote marked as recommended (best overall score)
    const row = document.querySelector(`[data-part-id="${partId}"]`);
    const bestQuoteCell = row.querySelector('.best-quote-cell');
    
    if (bestQuoteCell && !bestQuoteCell.textContent.includes('-')) {
        return extractQuoteFromCell(bestQuoteCell);
    }
    
    return getLowestCostQuote(partId);
}

function getLowestCostQuote(partId) {
    const row = document.querySelector(`[data-part-id="${partId}"]`);
    const quoteCells = row.querySelectorAll('.quote-cell');
    let lowestQuote = null;
    let lowestCost = Infinity;
    
    quoteCells.forEach(cell => {
        const amountElement = cell.querySelector('.quote-amount');
        if (amountElement) {
            const cost = parseFloat(amountElement.textContent.replace('£', '').replace(',', ''));
            if (cost < lowestCost) {
                lowestCost = cost;
                lowestQuote = extractQuoteFromCell(cell);
            }
        }
    });
    
    return lowestQuote;
}

function getFastestCompletionQuote(partId) {
    const row = document.querySelector(`[data-part-id="${partId}"]`);
    const quoteCells = row.querySelectorAll('.quote-cell');
    let fastestQuote = null;
    let fastestDays = Infinity;
    
    quoteCells.forEach(cell => {
        const detailsElement = cell.querySelector('.quote-details');
        if (detailsElement) {
            const daysMatch = detailsElement.textContent.match(/(\d+)d completion/);
            if (daysMatch) {
                const days = parseInt(daysMatch[1]);
                if (days < fastestDays) {
                    fastestDays = days;
                    fastestQuote = extractQuoteFromCell(cell);
                }
            }
        }
    });
    
    return fastestQuote || getLowestCostQuote(partId);
}

function getHighestQualityQuote(partId) {
    const row = document.querySelector(`[data-part-id="${partId}"]`);
    
    // Prefer dealer quotes for highest quality, then network, then assessor, then independent
    const qualityOrder = ['dealer-quote', 'network-quote', 'assessor-quote', 'independent-quote'];
    
    for (const qualityClass of qualityOrder) {
        const cell = row.querySelector(`.${qualityClass}`);
        if (cell && cell.querySelector('.quote-amount')) {
            return extractQuoteFromCell(cell);
        }
    }
    
    return getLowestCostQuote(partId);
}

function extractQuoteFromCell(cell) {
    const amountElement = cell.querySelector('.quote-amount');
    const detailsElement = cell.querySelector('.quote-details');
    
    if (!amountElement) return null;
    
    const cost = parseFloat(amountElement.textContent.replace('£', '').replace(',', ''));
    const providerType = getProviderTypeFromCell(cell);
    
    let completionDays = 7; // default
    if (detailsElement) {
        const daysMatch = detailsElement.textContent.match(/(\d+)d completion/);
        if (daysMatch) {
            completionDays = parseInt(daysMatch[1]);
        }
    }
    
    return {
        cost: cost,
        providerType: providerType,
        completionDays: completionDays,
        cell: cell
    };
}

function getProviderTypeFromCell(cell) {
    if (cell.classList.contains('assessor-quote')) return 'assessor';
    if (cell.classList.contains('dealer-quote')) return 'dealer';
    if (cell.classList.contains('independent-quote')) return 'independent';
    if (cell.classList.contains('network-quote')) return 'network';
    return 'unknown';
}

function selectQuoteForPart(partId, quote) {
    const row = document.querySelector(`[data-part-id="${partId}"]`);
    
    // Remove previous selections
    row.querySelectorAll('.quote-cell').forEach(cell => {
        cell.classList.remove('selected-quote');
    });
    
    // Add selection to chosen quote
    if (quote && quote.cell) {
        quote.cell.classList.add('selected-quote');
    }
    
    // Store selection data
    row.dataset.selectedQuote = JSON.stringify(quote);
}

function populateCustomSelectionTable() {
    const tableBody = document.getElementById('customSelectionTable');
    const parts = document.querySelectorAll('[data-part-id]');
    
    tableBody.innerHTML = '';
    
    parts.forEach(row => {
        const partId = row.dataset.partId;
        const partName = row.querySelector('td:first-child strong').textContent;
        const quoteCells = row.querySelectorAll('.quote-cell');
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${partName}</td>
            <td>
                <select class="form-select form-select-sm" data-part-id="${partId}" onchange="handleCustomQuoteSelection(this)">
                    <option value="">Select Quote...</option>
                </select>
            </td>
            <td class="selected-cost">-</td>
            <td class="selected-provider">-</td>
        `;
        
        const select = tr.querySelector('select');
        quoteCells.forEach(cell => {
            const amountElement = cell.querySelector('.quote-amount');
            if (amountElement) {
                const cost = amountElement.textContent;
                const providerType = getProviderTypeFromCell(cell);
                const option = document.createElement('option');
                option.value = JSON.stringify(extractQuoteFromCell(cell));
                option.textContent = `${providerType.charAt(0).toUpperCase() + providerType.slice(1)} - ${cost}`;
                select.appendChild(option);
            }
        });
        
        tableBody.appendChild(tr);
    });
}

function handleCustomQuoteSelection(select) {
    const partId = select.dataset.partId;
    const quoteData = select.value ? JSON.parse(select.value) : null;
    
    const row = select.closest('tr');
    const costCell = row.querySelector('.selected-cost');
    const providerCell = row.querySelector('.selected-provider');
    
    if (quoteData) {
        costCell.textContent = `£${quoteData.cost.toFixed(2)}`;
        providerCell.textContent = quoteData.providerType.charAt(0).toUpperCase() + quoteData.providerType.slice(1);
        
        // Update main table selection
        selectQuoteForPart(partId, quoteData);
    } else {
        costCell.textContent = '-';
        providerCell.textContent = '-';
        selectQuoteForPart(partId, null);
    }
    
    updateSelectionSummary();
}

function updateSelectionSummary() {
    const selectedQuotes = getSelectedQuotes();
    
    let totalCost = 0;
    let maxCompletionDays = 0;
    let originalTotalCost = 0;
    
    selectedQuotes.forEach(quote => {
        if (quote) {
            totalCost += quote.cost;
            maxCompletionDays = Math.max(maxCompletionDays, quote.completionDays);
        }
    });
    
    // Calculate original cost (highest quotes for comparison)
    const parts = document.querySelectorAll('[data-part-id]');
    parts.forEach(row => {
        const quoteCells = row.querySelectorAll('.quote-cell .quote-amount');
        let highestCost = 0;
        quoteCells.forEach(cell => {
            const cost = parseFloat(cell.textContent.replace('£', '').replace(',', ''));
            highestCost = Math.max(highestCost, cost);
        });
        originalTotalCost += highestCost;
    });
    
    const savings = originalTotalCost - totalCost;
    
    // Update display
    document.getElementById('selectedTotalCost').textContent = `£${totalCost.toFixed(2)}`;
    document.getElementById('selectedCompletionTime').textContent = maxCompletionDays > 0 ? `${maxCompletionDays} days` : '-';
    document.getElementById('selectedSavings').textContent = `£${Math.max(0, savings).toFixed(2)}`;
    
    // Update summary styling
    const summaryElement = document.querySelector('.selection-summary');
    if (totalCost > 0) {
        summaryElement.classList.add('active');
    } else {
        summaryElement.classList.remove('active');
    }
}

function getSelectedQuotes() {
    const parts = document.querySelectorAll('[data-part-id]');
    const selectedQuotes = [];
    
    parts.forEach(row => {
        const selectedData = row.dataset.selectedQuote;
        if (selectedData && selectedData !== 'null') {
            try {
                selectedQuotes.push(JSON.parse(selectedData));
            } catch (e) {
                console.warn('Failed to parse selected quote data:', e);
            }
        }
    });
    
    return selectedQuotes;
}

function viewPartDetails(partId) {
    // Show loading state
    const modal = new bootstrap.Modal(document.getElementById('partDetailsModal'));
    const content = document.getElementById('partDetailsContent');
    content.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> Loading part details...</div>';
    modal.show();
    
    // Fetch part details via AJAX
    fetch(`/assessments/parts/${partId}/details/`)
        .then(response => response.json())
        .then(data => {
            content.innerHTML = renderPartDetails(data);
        })
        .catch(error => {
            console.error('Error fetching part details:', error);
            content.innerHTML = '<div class="alert alert-danger">Failed to load part details.</div>';
        });
}

function renderPartDetails(data) {
    return `
        <div class="part-details">
            <h6>${data.part_name}</h6>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Category:</strong> ${data.part_category}</p>
                    <p><strong>Damage Severity:</strong> ${data.damage_severity}</p>
                    <p><strong>Labor Hours:</strong> ${data.estimated_labor_hours}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Part Number:</strong> ${data.part_number || 'N/A'}</p>
                    <p><strong>Section:</strong> ${data.section_type}</p>
                    <p><strong>Replacement Required:</strong> ${data.requires_replacement ? 'Yes' : 'No'}</p>
                </div>
            </div>
            <div class="mt-3">
                <h6>Damage Description:</h6>
                <p>${data.damage_description}</p>
            </div>
            ${data.quotes && data.quotes.length > 0 ? `
                <div class="mt-3">
                    <h6>Available Quotes:</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Provider</th>
                                    <th>Cost</th>
                                    <th>Part Type</th>
                                    <th>Completion</th>
                                    <th>Warranty</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.quotes.map(quote => `
                                    <tr>
                                        <td>${quote.provider_name}</td>
                                        <td>£${quote.total_cost}</td>
                                        <td>${quote.part_type}</td>
                                        <td>${quote.estimated_completion_days}d</td>
                                        <td>${quote.part_warranty_months}m</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

function selectPartQuote(partId) {
    const modal = new bootstrap.Modal(document.getElementById('quoteSelectionModal'));
    const content = document.getElementById('quoteSelectionContent');
    
    // Get available quotes for this part
    const row = document.querySelector(`[data-part-id="${partId}"]`);
    const partName = row.querySelector('td:first-child strong').textContent;
    const quoteCells = row.querySelectorAll('.quote-cell');
    
    let quotesHtml = `
        <h6>Select quote for: ${partName}</h6>
        <div class="quote-options">
    `;
    
    quoteCells.forEach(cell => {
        const amountElement = cell.querySelector('.quote-amount');
        if (amountElement) {
            const quote = extractQuoteFromCell(cell);
            const isSelected = cell.classList.contains('selected-quote');
            
            quotesHtml += `
                <div class="form-check quote-option ${isSelected ? 'selected' : ''}">
                    <input class="form-check-input" type="radio" name="selectedQuote" 
                           value='${JSON.stringify(quote)}' ${isSelected ? 'checked' : ''}>
                    <label class="form-check-label">
                        <strong>${quote.providerType.charAt(0).toUpperCase() + quote.providerType.slice(1)}</strong> - 
                        £${quote.cost.toFixed(2)} 
                        <small class="text-muted">(${quote.completionDays} days)</small>
                    </label>
                </div>
            `;
        }
    });
    
    quotesHtml += `
        </div>
        <div class="mt-3">
            <button type="button" class="btn btn-success" onclick="confirmQuoteSelection(${partId})">
                Confirm Selection
            </button>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancel
            </button>
        </div>
    `;
    
    content.innerHTML = quotesHtml;
    modal.show();
}

function confirmQuoteSelection(partId) {
    const selectedRadio = document.querySelector('input[name="selectedQuote"]:checked');
    if (selectedRadio) {
        const quote = JSON.parse(selectedRadio.value);
        selectQuoteForPart(partId, quote);
        updateSelectionSummary();
    }
    
    bootstrap.Modal.getInstance(document.getElementById('quoteSelectionModal')).hide();
}

function handleQuoteSelection(event) {
    event.preventDefault();
    
    const selectedQuotes = getSelectedQuotes();
    if (selectedQuotes.length === 0) {
        alert('Please select quotes for at least one part before finalizing.');
        return;
    }
    
    // Show confirmation
    if (!confirm('Are you sure you want to finalize these quote selections? This action cannot be undone.')) {
        return;
    }
    
    // Prepare form data
    const formData = new FormData(event.target);
    
    // Add selected quotes data
    selectedQuotes.forEach((quote, index) => {
        if (quote) {
            formData.append(`selected_quotes[${index}][part_id]`, quote.partId);
            formData.append(`selected_quotes[${index}][provider_type]`, quote.providerType);
            formData.append(`selected_quotes[${index}][cost]`, quote.cost);
        }
    });
    
    // Submit form
    fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url || window.location.href;
        } else {
            alert('Error finalizing quotes: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error submitting quote selection:', error);
        alert('Error submitting quote selection. Please try again.');
    });
}

function exportQuoteSummary() {
    const pathMatch = window.location.pathname.match(/\/assessments\/(\d+)\//);
    if (!pathMatch) return;
    
    const assessmentId = pathMatch[1];
    window.open(`/assessments/${assessmentId}/quote-summary/export/`, '_blank');
}

function refreshQuoteStatus() {
    const pathMatch = window.location.pathname.match(/\/assessments\/(\d+)\//);
    if (!pathMatch) return;
    
    const assessmentId = pathMatch[1];
    
    fetch(`/assessments/${assessmentId}/quote-status/`)
        .then(response => response.json())
        .then(data => {
            if (data.updated) {
                // Refresh the page if there are updates
                window.location.reload();
            }
        })
        .catch(error => {
            console.warn('Failed to refresh quote status:', error);
        });
}

function initializeTableSorting() {
    const table = document.getElementById('partsComparisonTable');
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        if (index < 8) { // Only make first 8 columns sortable
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(index));
        }
    });
}

function sortTable(columnIndex) {
    const table = document.getElementById('partsComparisonTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isNumeric = columnIndex >= 3 && columnIndex <= 7; // Quote columns
    
    rows.sort((a, b) => {
        const aCell = a.cells[columnIndex];
        const bCell = b.cells[columnIndex];
        
        let aValue = aCell.textContent.trim();
        let bValue = bCell.textContent.trim();
        
        if (isNumeric) {
            aValue = parseFloat(aValue.replace(/[£,]/g, '')) || 0;
            bValue = parseFloat(bValue.replace(/[£,]/g, '')) || 0;
            return aValue - bValue;
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// CSS for selected quotes
const style = document.createElement('style');
style.textContent = `
    .selected-quote {
        background-color: #d4edda !important;
        border: 2px solid #28a745 !important;
    }
    
    .quote-option.selected {
        background-color: #d4edda;
        border-radius: 4px;
        padding: 0.5rem;
    }
`;
document.head.appendChild(style);