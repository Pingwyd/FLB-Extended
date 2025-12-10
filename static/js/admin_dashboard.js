function adminDashboard() {
    return {
        user: JSON.parse(localStorage.getItem('flb_user') || '{}'),
        stats: {
            users: 0,
            jobs: 0,
            listings: 0,
            pending_verifications: 0,
            total_revenue: 0
        },
        wallet: {
            balance: 0,
            currency: 'NGN'
        },
        isLoading: true,

        async init() {
            if (!localStorage.getItem('is_logged_in')) {
                window.location.href = '/login-page';
                return;
            }

            // Redirect if not admin
            if (!['admin', 'super_admin'].includes(this.user.account_type)) {
                window.location.href = '/dashboard';
                return;
            }

            await Promise.all([
                this.fetchStats(),
                this.fetchWallet()
            ]);
            
            this.isLoading = false;
        },

        async fetchStats() {
            try {
                const res = await fetch(`/api/admin/stats?admin_id=${this.user.id}`, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (res.ok) {
                    this.stats = await res.json();
                }
            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        },

        async fetchWallet() {
            try {
                const res = await fetch(`/api/wallet/balance/${this.user.id}`);
                if (res.ok) {
                    const data = await res.json();
                    this.wallet.balance = data.balance;
                }
            } catch (error) {
                console.error('Error fetching wallet:', error);
            }
        },

        formatCurrency(amount) {
            return new Intl.NumberFormat('en-NG', {
                style: 'currency',
                currency: 'NGN'
            }).format(amount);
        },
        
        logout() {
            localStorage.removeItem('is_logged_in');
            localStorage.removeItem('flb_user');
            window.location.href = '/login-page';
        }
    }
}
