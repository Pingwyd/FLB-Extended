function jobsDirectory() {
    return {
        jobs: [],
        loading: true,
        searchQuery: '',
        sortBy: 'recent',

        async fetchJobs() {
            this.loading = true;
            try {
                let url = '/api/jobs/list?'; // We need to create this endpoint or use existing
                if (this.searchQuery) {
                    url += 'q=' + encodeURIComponent(this.searchQuery) + '&';
                }
                if (this.sortBy) {
                    url += 'sort_by=' + encodeURIComponent(this.sortBy);
                }

                const response = await fetch(url);
                if (response.ok) {
                    this.jobs = await response.json();
                } else {
                    // Mock data if API fails or doesn't exist yet
                    console.warn('Failed to fetch jobs, using mock data');
                    this.jobs = [
                        { id: 1, title: 'Farm Manager', location: 'Lagos', salary_range: '₦150k - ₦200k', description: 'Experienced farm manager needed for a poultry farm.', created_at: new Date().toISOString() },
                        { id: 2, title: 'Tractor Operator', location: 'Ogun', salary_range: '₦80k - ₦120k', description: 'Licensed tractor operator for land preparation.', created_at: new Date().toISOString() },
                        { id: 3, title: 'Harvester', location: 'Oyo', salary_range: 'Daily Pay', description: 'Seasonal harvesters needed for maize farm.', created_at: new Date().toISOString() }
                    ];
                }
            } catch (error) {
                console.error('Error fetching jobs:', error);
                // Mock data fallback
                 this.jobs = [
                        { id: 1, title: 'Farm Manager', location: 'Lagos', salary_range: '₦150k - ₦200k', description: 'Experienced farm manager needed for a poultry farm.', created_at: new Date().toISOString() },
                        { id: 2, title: 'Tractor Operator', location: 'Ogun', salary_range: '₦80k - ₦120k', description: 'Licensed tractor operator for land preparation.', created_at: new Date().toISOString() },
                        { id: 3, title: 'Harvester', location: 'Oyo', salary_range: 'Daily Pay', description: 'Seasonal harvesters needed for maize farm.', created_at: new Date().toISOString() }
                    ];
            } finally {
                this.loading = false;
            }
        },

        formatDate(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleDateString();
        },

        init() {
            this.fetchJobs();
        }
    }
}
