/**
 * API Client for Lead Generation Tool
 */

const API_BASE = '/api';

const api = {
    /**
     * Search for businesses
     */
    async searchBusinesses(query, location, radiusKm, maxResults) {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                location: location,
                radius_km: radiusKm,
                max_results: maxResults
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Search failed');
        }

        return response.json();
    },

    /**
     * Get API usage statistics
     */
    async getUsage() {
        const response = await fetch(`${API_BASE}/search/usage`);
        if (!response.ok) {
            throw new Error('Failed to get usage stats');
        }
        return response.json();
    },

    /**
     * Get list of businesses with filters
     */
    async getBusinesses(filters = {}) {
        const params = new URLSearchParams();

        if (filters.searchId) params.append('search_id', filters.searchId);
        if (filters.hasWebsite !== undefined && filters.hasWebsite !== '') {
            params.append('has_website', filters.hasWebsite);
        }
        if (filters.minRating) params.append('min_rating', filters.minRating);
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.offset) params.append('offset', filters.offset);

        const response = await fetch(`${API_BASE}/businesses?${params}`);
        if (!response.ok) {
            throw new Error('Failed to get businesses');
        }
        return response.json();
    },

    /**
     * Get summary statistics
     */
    async getStats() {
        const response = await fetch(`${API_BASE}/businesses/stats/summary`);
        if (!response.ok) {
            throw new Error('Failed to get stats');
        }
        return response.json();
    },

    /**
     * Health check
     */
    async healthCheck() {
        const response = await fetch(`${API_BASE}/health`);
        return response.json();
    }
};
