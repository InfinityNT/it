// Filter state management for devices list
class FilterState {
    constructor() {
        this.filters = {
            search: '',
            status: '',
            category: ''
        };
        this.init();
    }

    init() {
        // Initialize form elements
        const searchInput = document.querySelector('[name="search"]');
        const statusSelect = document.querySelector('[name="status"]');
        const categoryInput = document.querySelector('[name="category"]');

        // Set up event listeners to update filter state
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filters.search = e.target.value;
            });
        }

        if (statusSelect) {
            statusSelect.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
            });
        }

        if (categoryInput) {
            categoryInput.addEventListener('input', (e) => {
                this.filters.category = e.target.value;
            });
        }
    }

    // Get current filter values
    getFilters() {
        return this.filters;
    }

    // Reset all filters
    resetFilters() {
        this.filters = {
            search: '',
            status: '',
            category: ''
        };
        
        // Update form elements
        const searchInput = document.querySelector('[name="search"]');
        const statusSelect = document.querySelector('[name="status"]');
        const categoryInput = document.querySelector('[name="category"]');

        if (searchInput) searchInput.value = '';
        if (statusSelect) statusSelect.value = '';
        if (categoryInput) categoryInput.value = '';
    }
}

// Initialize filter state when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('[name="search"], [name="status"], [name="category"]')) {
        window.deviceFilterState = new FilterState();
    }
});