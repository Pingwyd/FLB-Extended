function workerDetail() {
    return {
        worker: {},
        loading: true,

        async init() {
            // Extract worker ID from URL path: /workers/123
            const pathParts = window.location.pathname.split('/');
            const workerId = pathParts[pathParts.length - 1];
            
            if (workerId && !isNaN(workerId)) {
                await this.fetchWorker(workerId);
            } else {
                // Fallback or error handling
                console.error("No worker ID found in URL");
                this.loading = false;
            }
        },

        async fetchWorker(id) {
            try {
                const response = await fetch(`/workers/${id}`, {
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                if (response.ok) {
                    this.worker = await response.json();
                    // Map backend fields to frontend expected fields if necessary
                    this.worker.location = `${this.worker.location_area}, ${this.worker.location_state}`;
                } else {
                    console.error('Failed to fetch worker details');
                }
            } catch (error) {
                console.error('Error fetching worker:', error);
            } finally {
                this.loading = false;
            }
        }
    }
}
