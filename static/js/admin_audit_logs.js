function adminAuditLogs(){
  return {
    logs: [],
    selected: [],
    filter_admin_id: '',
    filter_action: '',
    init(){
      // small delay to allow localStorage to be available
      setTimeout(()=> this.loadLogs(), 50)
    },
    async loadLogs(){
      let admin = null
      try{ admin = JSON.parse(localStorage.getItem('flb_user') || 'null') }catch(e){}
      let admin_id = (admin && admin.id) ? admin.id : (new URLSearchParams(location.search)).get('admin_id')
      if(!admin_id){
        // allow unauthenticated viewing only if admin_id provided via query param
        console.warn('No admin_id found in localStorage; prompt for admin id if needed')
      }

      const payload = {}
      if(admin_id) payload.admin_id = admin_id
      if(this.filter_admin_id) payload.filter_admin_id = this.filter_admin_id
      if(this.filter_action) payload.action = this.filter_action

      try{
        const res = await fetch('/admin/audit-logs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const data = await res.json()
        if(res.ok){
          this.logs = data
        } else {
          console.error('Failed to load audit logs', data)
          alert('Failed to load audit logs: ' + (data.error || res.statusText))
        }
      }catch(err){
        console.error('Error fetching audit logs', err)
        alert('Error fetching audit logs: ' + err)
      }
    },
    async markSelectedRead(){
      if(!this.selected || this.selected.length === 0){
        return alert('No logs selected')
      }
      let admin = null
      try{ admin = JSON.parse(localStorage.getItem('flb_user') || 'null') }catch(e){}
      let admin_id = (admin && admin.id) ? admin.id : prompt('Enter admin id to authorize mark-read:')
      if(!admin_id){ return alert('admin_id required') }

      try{
        const res = await fetch('/admin/audit-logs/mark-read', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ admin_id: admin_id, ids: this.selected })
        })
        const data = await res.json()
        if(res.ok){
          this.selected = []
          this.loadLogs()
        } else {
          console.error('mark-read failed', data)
          alert('Failed to mark logs read: ' + (data.error || res.statusText))
        }
      }catch(err){
        console.error('Error marking logs read', err)
        alert('Error marking logs read: ' + err)
      }
    },
    async markAllRead(){
      if(!confirm('Mark ALL audit logs as read?')) return
      let admin = null
      try{ admin = JSON.parse(localStorage.getItem('flb_user') || 'null') }catch(e){}
      let admin_id = (admin && admin.id) ? admin.id : prompt('Enter admin id to authorize mark-all:')
      if(!admin_id){ return alert('admin_id required') }

      try{
        const res = await fetch('/admin/audit-logs/mark-read', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ admin_id: admin_id, mark_all: true })
        })
        const data = await res.json()
        if(res.ok){
          this.loadLogs()
        } else {
          console.error('mark-all failed', data)
          alert('Failed to mark all read: ' + (data.error || res.statusText))
        }
      }catch(err){
        console.error('Error marking all read', err)
        alert('Error marking all read: ' + err)
      }
    },
    formatDate(s){
      if(!s) return ''
      try{ return new Date(s).toLocaleString() }catch(e){ return s }
    }
  }
}
