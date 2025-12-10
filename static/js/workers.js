function workersDirectory() {
    return {
        workers: [],
        loading: true,
        searchQuery: '',
        sortBy: 'rating',

        async fetchWorkers() {
            this.loading = true;
            try {
                let url = '/api/workers/list?';
                if (this.searchQuery) {
                    url += 'q=' + encodeURIComponent(this.searchQuery) + '&';
                }
                if (this.sortBy) {
                    url += 'sort_by=' + encodeURIComponent(this.sortBy);
                }

                const response = await fetch(url);
                if (response.ok) {
                    this.workers = await response.json();
                } else {
                    console.error('Failed to fetch workers');
                }
            } catch (error) {
                console.error('Error fetching workers:', error);
            } finally {
                this.loading = false;
            }
        },

        init() {
            this.fetchWorkers();
        }
    }
}
