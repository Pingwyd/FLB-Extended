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
        recentMessages: [],
        showNotifications: false,
        unreadCount: 0,
        isLoading: true,

        async init() {
            if (!localStorage.getItem('is_logged_in')) {
                window.location.href = '/login-page';
                return;
            }

            // Redirect if not admin
            if (!['admin', 'super_admin', 'moderator'].includes(this.user.account_type)) {
                window.location.href = '/dashboard';
                return;
            }

            await Promise.all([
                this.fetchStats(),
                this.fetchWallet(),
                this.fetchRecentActivity(),
                this.fetchRecentMessages()
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
                try {
                    const payload = text ? JSON.parse(text) : null;
                    if (res.ok && payload) {
                        this.stats = payload;
                        console.debug('Fetched admin stats:', payload);
                    } else {
                        console.warn('Failed to fetch admin stats, status=', res.status, 'body=', payload);
                    }
                } catch (e) {
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

        async fetchRecentMessages() {
            try {
                // Use a different API or same one if it works for admins? 
                // Currently /messages/<user_id> works for any user_id if valid session.
                // Admin can see their own messages.
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
        },

        logout() {
            // Clear local client state and call server logout endpoint to clear server session
            localStorage.removeItem('is_logged_in');
            localStorage.removeItem('flb_user');
            try {
                fetch('/logout', { method: 'GET', credentials: 'same-origin' }).catch(() => { });
            } catch (e) { }
            window.location.href = '/login-page';
        }
    }
}
