/**
 * Lead Generation Tool - Main Application
 */

// State
let currentSearchId = null;
let currentBusinesses = [];
let currentPage = 0;
const PAGE_SIZE = 10;

// DOM Elements
const searchForm = document.getElementById('searchForm');
const searchBtn = document.getElementById('searchBtn');
const businessTypeInput = document.getElementById('businessType');
const locationInput = document.getElementById('location');
const radiusInput = document.getElementById('radius');
const maxResultsInput = document.getElementById('maxResults');

const statsBar = document.getElementById('statsBar');
const filtersSection = document.getElementById('filtersSection');
const resultsSection = document.getElementById('resultsSection');
const resultsBody = document.getElementById('resultsBody');
const emptyState = document.getElementById('emptyState');
const errorState = document.getElementById('errorState');

const websiteFilter = document.getElementById('websiteFilter');
const ratingFilter = document.getElementById('ratingFilter');
const exportBtn = document.getElementById('exportBtn');

const usageCount = document.getElementById('usageCount');
const usageFill = document.getElementById('usageFill');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // Load API usage on start
    await updateUsage();

    // Setup event listeners
    searchForm.addEventListener('submit', handleSearch);
    websiteFilter.addEventListener('change', handleFilterChange);
    ratingFilter.addEventListener('change', handleFilterChange);
    exportBtn.addEventListener('click', exportCSV);
}

/**
 * Update API usage display
 */
async function updateUsage() {
    try {
        const usage = await api.getUsage();
        usageCount.textContent = `${usage.calls_used}/${usage.calls_limit}`;
        usageFill.style.width = `${usage.percentage_used}%`;

        // Change color if getting close to limit
        if (usage.percentage_used > 80) {
            usageFill.style.background = 'linear-gradient(135deg, #ff9800, #f44336)';
        } else {
            usageFill.style.background = 'var(--accent-gradient)';
        }
    } catch (error) {
        console.error('Failed to get usage:', error);
    }
}

/**
 * Handle search form submission
 */
async function handleSearch(e) {
    e.preventDefault();

    const query = businessTypeInput.value.trim();
    const location = locationInput.value.trim();
    const radius = parseInt(radiusInput.value) || 10;
    const maxResults = parseInt(maxResultsInput.value) || 10;

    if (!query || !location) return;

    // Show loading state
    setLoading(true);
    hideError();

    try {
        const result = await api.searchBusinesses(query, location, radius, maxResults);

        currentSearchId = result.search_id;
        currentBusinesses = result.businesses;
        currentPage = 0; // Reset to first page

        // Update UI
        showResults(result.businesses);
        updateStats(result.businesses);
        await updateUsage();

    } catch (error) {
        showError('Search Failed', error.message);
    } finally {
        setLoading(false);
    }
}

/**
 * Get filtered businesses based on current filter selections
 * (Shared function to eliminate duplicate filter logic)
 */
function getFilteredBusinesses() {
    const websiteValue = websiteFilter.value;
    const minRating = ratingFilter.value ? parseFloat(ratingFilter.value) : null;

    let filtered = [...currentBusinesses];

    if (websiteValue === 'true') {
        filtered = filtered.filter(b => b.website);
    } else if (websiteValue === 'false') {
        filtered = filtered.filter(b => !b.website);
    }

    if (minRating) {
        filtered = filtered.filter(b => b.rating && b.rating >= minRating);
    }

    return filtered;
}

/**
 * Handle filter change - reset to page 0 and re-render
 */
function handleFilterChange() {
    currentPage = 0;
    applyFilters();
}

/**
 * Apply filters and render current page
 */
function applyFilters() {
    const filtered = getFilteredBusinesses();
    renderPage(filtered);
}

/**
 * Show search results
 */
function showResults(businesses) {
    if (businesses.length === 0) {
        emptyState.style.display = 'block';
        emptyState.querySelector('h3').textContent = 'No businesses found';
        emptyState.querySelector('p').textContent = 'Try a different search query or location.';
        resultsSection.style.display = 'none';
        statsBar.style.display = 'none';
        filtersSection.style.display = 'none';
        return;
    }

    emptyState.style.display = 'none';
    statsBar.style.display = 'flex';
    filtersSection.style.display = 'flex';
    resultsSection.style.display = 'block';

    renderPage(businesses);
}

/**
 * Render a page of businesses with pagination
 */
function renderPage(businesses) {
    const totalPages = Math.ceil(businesses.length / PAGE_SIZE);
    const start = currentPage * PAGE_SIZE;
    const pageData = businesses.slice(start, start + PAGE_SIZE);

    renderTable(pageData);
    renderPaginationControls(businesses.length, totalPages);
}

/**
 * Render pagination controls
 */
function renderPaginationControls(totalItems, totalPages) {
    // Remove existing pagination if present
    const existingPagination = document.getElementById('paginationControls');
    if (existingPagination) {
        existingPagination.remove();
    }

    // Don't show pagination if only one page
    if (totalPages <= 1) return;

    const paginationHtml = `
        <div id="paginationControls" class="pagination">
            <button class="btn btn-secondary pagination-btn" id="prevBtn" ${currentPage === 0 ? 'disabled' : ''}>
                ← Previous
            </button>
            <span class="pagination-info">
                Page ${currentPage + 1} of ${totalPages} (${totalItems} results)
            </span>
            <button class="btn btn-secondary pagination-btn" id="nextBtn" ${currentPage >= totalPages - 1 ? 'disabled' : ''}>
                Next →
            </button>
        </div>
    `;

    // Insert after the table
    const tableContainer = document.querySelector('.table-container');
    tableContainer.insertAdjacentHTML('afterend', paginationHtml);

    // Add event listeners
    document.getElementById('prevBtn').addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            applyFilters();
        }
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        if (currentPage < totalPages - 1) {
            currentPage++;
            applyFilters();
        }
    });
}

/**
 * Render businesses in table
 */
function renderTable(businesses) {
    resultsBody.innerHTML = businesses.map(b => `
        <tr>
            <td>
                <strong>${escapeHtml(b.name)}</strong>
            </td>
            <td>
                <span class="lead-score ${getLeadScoreClass(b.lead_score)}">
                    ${b.lead_score || 0}
                </span>
            </td>
            <td>
                ${b.rating ? `
                    <div class="rating">
                        <span class="rating-stars">★</span>
                        <span class="rating-value">${b.rating.toFixed(1)}</span>
                    </div>
                ` : '<span style="color: var(--text-muted)">N/A</span>'}
            </td>
            <td>
                ${b.review_count ? b.review_count.toLocaleString() : '-'}
            </td>
            <td>
                ${b.website ? `
                    <a href="${escapeHtml(b.website)}" target="_blank" class="website-link">
                        🔗 Visit
                    </a>
                ` : '<span class="no-website">❌ No Website</span>'}
            </td>
            <td>
                ${b.phone ? escapeHtml(b.phone) : '-'}
            </td>
            <td>
                ${b.address ? escapeHtml(b.address) : '-'}
            </td>
        </tr>
    `).join('');
}

/**
 * Get CSS class for lead score badge
 */
function getLeadScoreClass(score) {
    if (score >= 65) return 'score-hot';
    if (score >= 35) return 'score-warm';
    return 'score-cold';
}

/**
 * Update statistics display
 */
function updateStats(businesses) {
    const total = businesses.length;
    const withWebsite = businesses.filter(b => b.website).length;
    const withoutWebsite = total - withWebsite;

    document.getElementById('statTotal').textContent = total;
    document.getElementById('statWithWebsite').textContent = withWebsite;
    document.getElementById('statWithoutWebsite').textContent = withoutWebsite;
}

/**
 * Export current results to CSV (uses shared filter function)
 */
function exportCSV() {
    if (currentBusinesses.length === 0) return;

    // Use shared filter function
    const businesses = getFilteredBusinesses();

    // Create CSV content
    const headers = ['Name', 'Lead Score', 'Rating', 'Reviews', 'Website', 'Phone', 'Address'];
    const rows = businesses.map(b => [
        `"${(b.name || '').replace(/"/g, '""')}"`,
        b.lead_score || 0,
        b.rating || '',
        b.review_count || '',
        `"${(b.website || '').replace(/"/g, '""')}"`,
        `"${(b.phone || '').replace(/"/g, '""')}"`,
        `"${(b.address || '').replace(/"/g, '""')}"`
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Set loading state
 */
function setLoading(loading) {
    searchBtn.disabled = loading;
    searchBtn.querySelector('.btn-text').style.display = loading ? 'none' : 'inline';
    searchBtn.querySelector('.btn-loading').style.display = loading ? 'inline' : 'none';
}

/**
 * Show error message
 */
function showError(title, message) {
    errorState.style.display = 'block';
    document.getElementById('errorTitle').textContent = title;
    document.getElementById('errorMessage').textContent = message;

    emptyState.style.display = 'none';
    resultsSection.style.display = 'none';
    statsBar.style.display = 'none';
    filtersSection.style.display = 'none';
}

/**
 * Hide error message
 */
function hideError() {
    errorState.style.display = 'none';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
