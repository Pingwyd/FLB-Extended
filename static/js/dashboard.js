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
        recentApplications: [],
        recentMessages: [],

        // Task Management
        tasks: [],
        isLoadingTasks: false,
        showTaskModal: false,
        newTask: {
            title: '',
            due_date: ''
        },

        async init() {
            if (!localStorage.getItem('is_logged_in')) {
                window.location.href = '/login-page';
                return;
            }

            // Redirect admins to admin dashboard
            if (['admin', 'super_admin', 'moderator'].includes(this.user.account_type)) {
                window.location.href = '/admin/dashboard';
                return;
            }

            if (this.user.id) {
                await this.fetchContracts();
                await this.fetchTasks(); // Load tasks for all users
                if (this.user.account_type === 'farmer') {
                    await this.fetchJobs();
                }
                if (this.user.account_type === 'realtor') {
                    await this.fetchListings();
                }
                if (this.user.account_type === 'worker') {
                    await this.loadWorkerData();
                }

                // Fetch messages for everyone
                await this.fetchRecentMessages();
            }
        },

        async fetchTasks() {
            this.isLoadingTasks = true;
            try {
                const res = await fetch(`/api/tasks?user_id=${this.user.id}`);
                if (res.ok) {
                    this.tasks = await res.json();
                }
            } catch (e) {
                console.error('Error fetching tasks:', e);
            } finally {
                this.isLoadingTasks = false;
            }
        },

        openTaskModal() {
            this.newTask = { title: '', due_date: '' };
            this.showTaskModal = true;
        },

        async createTask() {
            if (!this.newTask.title) {
                alert('Title is required');
                return;
            }
            try {
                const res = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: this.user.id,
                        ...this.newTask
                    })
                });
                if (res.ok) {
                    this.showTaskModal = false;
                    this.fetchTasks();
                } else {
                    alert('Failed to create task');
                }
            } catch (e) {
                console.error(e);
            }
        },

        async toggleTaskStatus(task) {
            const newStatus = task.status === 'completed' ? 'pending' : 'completed';
            try {
                const res = await fetch(`/api/tasks/${task.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    task.status = newStatus;
                }
            } catch (e) {
                console.error(e);
            }
        },

        async deleteTask(taskId) {
            if (!confirm('Are you sure?')) return;
            try {
                const res = await fetch(`/api/tasks/${taskId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    this.tasks = this.tasks.filter(t => t.id !== taskId);
                }
            } catch (e) {
                console.error(e);
            }
        },

        async loadWorkerData() {
            try {
                const res = await fetch(`/api/worker-dashboard-stats?user_id=${this.user.id}`);
                if (res.ok) {
                    const data = await res.json();
                    this.workerStats = {
                        jobsCompleted: data.jobsCompleted,
                        totalEarnings: data.totalEarnings,
                        rating: data.rating
                    };
                    this.recentApplications = data.recentApplications;
                }
            } catch (e) {
                console.error('Error loading worker data:', e);
            }
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
        },

        async fetchRecentMessages() {
            try {
                const res = await fetch(`/messages/${this.user.id}`);
                if (res.ok) {
                    const data = await res.json();

                    // Process messages to find recent conversations
                    const all = [...data.sent, ...data.received].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                    const uniquePartners = new Map();

                    all.forEach(msg => {
                        const isSender = msg.sender_id === this.user.id;
                        const partnerId = isSender ? msg.recipient_id : msg.sender_id;

                        if (!uniquePartners.has(partnerId)) {
                            // Use enriched data
                            const partnerName = isSender ? msg.recipient_name : msg.sender_name;
                            const partnerPic = isSender ? msg.recipient_picture : msg.sender_picture;

                            uniquePartners.set(partnerId, {
                                partner_id: partnerId,
                                partner_name: partnerName || 'Unknown User',
                                partner_picture: partnerPic,
                                last_message: msg.content,
                                time: msg.created_at
                            });
                        }
                    });

                    this.recentMessages = Array.from(uniquePartners.values()).slice(0, 3);
                }
            } catch (e) {
                console.error('Error fetching recent messages:', e);
            }
        }
    }
}
