function dashboard() {
    return {
        user: JSON.parse(localStorage.getItem('flb_user') || '{}'),
        contracts: [],
        jobs: [],
        listings: [],
        // Worker specific data
        workerStats: {
            jobsCompleted: 0,
            totalEarnings: 0,
            rating: 0
        },
        upcomingSchedule: [],

        async init() {
            if (!localStorage.getItem('is_logged_in')) {
                window.location.href = '/login-page';
                return;
            }

            if (this.user.id) {
                await this.fetchContracts();
                if (this.user.account_type === 'farmer') {
                    await this.fetchJobs();
                }
                if (this.user.account_type === 'realtor') {
                    await this.fetchListings();
                }
                if (this.user.account_type === 'worker') {
                    this.loadWorkerData();
                }
            }
        },

        loadWorkerData() {
            // Mock data for worker dashboard
            this.workerStats = {
                jobsCompleted: 12,
                totalEarnings: 450000,
                rating: 4.8
            };
            
            this.upcomingSchedule = [
                { id: 1, title: 'Maize Harvesting', date: '2025-12-12', location: 'Kaduna Farm A', time: '08:00 AM' },
                { id: 2, title: 'Fertilizer Application', date: '2025-12-15', location: 'Green Valley', time: '07:30 AM' },
                { id: 3, title: 'Equipment Maintenance', date: '2025-12-18', location: 'Lagos Agro Hub', time: '09:00 AM' }
            ];
        },

        async fetchContracts() {
            try {
                const res = await fetch(`/api/my-contracts?user_id=${this.user.id}`);
                if (res.ok) {
                    this.contracts = await res.json();
                }
            } catch (e) {
                console.error(e);
            }
        },

        async fetchJobs() {
            try {
                const res = await fetch(`/api/my-jobs?user_id=${this.user.id}`);
                if (res.ok) {
                    this.jobs = await res.json();
                }
            } catch (e) {
                console.error(e);
            }
        },

        async fetchListings() {
            try {
                const res = await fetch(`/listings/user/${this.user.id}`);
                if (res.ok) {
                    this.listings = await res.json();
                }
            } catch (e) {
                console.error(e);
            }
        }
    }
}
