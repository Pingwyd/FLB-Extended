function jobDetail() {
    return {
        job: {},
        loading: true,

        async init() {
            const pathParts = window.location.pathname.split('/');
            const jobId = pathParts[pathParts.length - 1];

            if (jobId && !isNaN(jobId)) {
                await this.fetchJob(jobId);
            } else {
                console.error("No job ID found in URL");
                this.loading = false;
            }
        },

        async fetchJob(id) {
            try {
                const response = await fetch(`/api/jobs/${id}`);
                if (response.ok) {
                    this.job = await response.json();
                } else {
                    console.error('Failed to fetch job details');
                }
            } catch (error) {
                console.error('Error fetching job:', error);
            } finally {
                this.loading = false;
            }
        },

        async applyForJob() {
            // Check if user is logged in
            const userStr = localStorage.getItem('flb_user');
            if (!userStr) {
                alert('Please login to apply for this job.');
                window.location.href = '/login-page';
                return;
            }

            const user = JSON.parse(userStr);

            // Check if user is trying to apply to their own job
            if (this.job.farmer_id === user.id) {
                alert('You cannot apply to your own job posting!');
                return;
            }

            // For now, show confirmation and redirect to messages
            // In future, this could create a JobApplication record
            if (confirm(`Apply for "${this.job.title}"?\n\nThis will send a message to the employer.`)) {
                // Redirect to messages with the job poster
                window.location.href = `/messages?recipient=${this.job.farmer_id}&job=${this.job.id}`;
            }
        },

        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        }
    }
}
