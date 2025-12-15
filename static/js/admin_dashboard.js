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
        recentActivity: [],
        showNotifications: false,
        unreadCount: 0,
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
                this.fetchWallet(),
                this.fetchRecentActivity()
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
                
                const text = await res.text();
                try{
                    const payload = text ? JSON.parse(text) : null;
                    if(res.ok && payload){
                        this.stats = payload;
                        console.debug('Fetched admin stats:', payload);
                    } else {
                        console.warn('Failed to fetch admin stats, status=', res.status, 'body=', payload);
                    }
                }catch(e){
                    console.error('Failed to parse /api/admin/stats response', e, 'raw=', text);
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

        async fetchRecentActivity() {
            try {
                const res = await fetch('/admin/audit-logs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        limit: 5,
                        admin_id: this.user.id
                    })
                });
                
                if (res.ok) {
                    this.recentActivity = await res.json();
                    // Compute unread/unseen count if server provides an unread/seen flag
                    this.unreadCount = this.recentActivity.filter(item => {
                        return item.unread === true || item.is_unread === true || item.seen === false || item.read === false;
                    }).length;
                }
            } catch (error) {
                console.error('Error fetching activity:', error);
            }
        },

        formatCurrency(amount) {
            return new Intl.NumberFormat('en-NG', {
                style: 'currency',
                currency: 'NGN'
            }).format(amount);
        },

        formatDate(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
        },
        async markNotificationsRead(ids) {
            if (!ids || ids.length === 0) return;
            try {
                await fetch('/admin/audit-logs/mark-read', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: ids, admin_id: this.user.id })
                });
                // locally mark them as read to update UI
                this.recentActivity = this.recentActivity.map(item => {
                    if (ids.includes(item.id)) item.read = true;
                    return item;
                });
                this.unreadCount = this.recentActivity.filter(i => !i.read).length;
            } catch (e) {
                console.error('Failed to mark notifications read', e);
            }
        },
        async toggleNotifications() {
            this.showNotifications = !this.showNotifications;
            if (this.showNotifications) {
                await this.fetchRecentActivity();
                // mark any unread items as read on the server
                const unreadIds = this.recentActivity.filter(i => !i.read).map(i => i.id);
                if (unreadIds.length > 0) {
                    await this.markNotificationsRead(unreadIds);
                }
            }
        },
        
        logout() {
            // Clear local client state and call server logout endpoint to clear server session
            localStorage.removeItem('is_logged_in');
            localStorage.removeItem('flb_user');
            try {
                fetch('/logout', { method: 'GET', credentials: 'same-origin' }).catch(()=>{});
            } catch (e) {}
            window.location.href = '/login-page';
        }
    }
}
