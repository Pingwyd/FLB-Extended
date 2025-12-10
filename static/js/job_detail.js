function jobDetail() {
    return {
        job: {},
        loading: true,
        currentUser: null,
        
        // Apply Modal State
        showApplyModal: false,
        coverLetter: '',
        isApplying: false,

        // Applications Modal State
        showApplicationsModal: false,
        applications: [],
        isLoadingApplications: false,

        async init() {
            const userStr = localStorage.getItem('flb_user');
            if (userStr) {
                this.currentUser = JSON.parse(userStr);
            }

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

        get isEmployer() {
            return this.currentUser && this.job && this.currentUser.id === this.job.employer_id;
        },

        openApplyModal() {
            if (!this.currentUser) {
                alert('Please login to apply.');
                window.location.href = '/login-page';
                return;
            }
            this.showApplyModal = true;
        },

        async submitApplication() {
            if (!this.coverLetter.trim()) {
                alert('Please write a cover letter.');
                return;
            }
            
            this.isApplying = true;
            try {
                const response = await fetch(`/api/jobs/${this.job.id}/apply`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: this.currentUser.id,
                        cover_letter: this.coverLetter
                    })
                });
                
                const data = await response.json();
                if (response.ok) {
                    alert('Application submitted successfully!');
                    this.showApplyModal = false;
                    this.coverLetter = '';
                } else {
                    alert(data.error || 'Failed to submit application.');
                }
            } catch (error) {
                console.error('Error applying:', error);
                alert('An error occurred.');
            } finally {
                this.isApplying = false;
            }
        },

        async openApplicationsModal() {
            this.showApplicationsModal = true;
            this.isLoadingApplications = true;
            try {
                const response = await fetch(`/api/jobs/${this.job.id}/applications?employer_id=${this.currentUser.id}`);
                if (response.ok) {
                    this.applications = await response.json();
                } else {
                    alert('Failed to fetch applications.');
                }
            } catch (error) {
                console.error('Error fetching applications:', error);
            } finally {
                this.isLoadingApplications = false;
            }
        },

        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        }
    }
}
