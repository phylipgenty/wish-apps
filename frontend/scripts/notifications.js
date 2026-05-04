import { getAuthToken } from './api.js';

let currentUnreadCount = 0;

export async function fetchUnreadCount() {
    const token = getAuthToken();
    if (!token) return 0;
    try {
        const res = await fetch('https://wish-apps.onrender.com/users/notifications', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        const notifs = await res.json();
        return notifs.filter(n => !n.is_read).length;
    } catch (err) {
        console.error('Failed to fetch notifications', err);
        return 0;
    }
}

export async function loadNotifications() {
    const token = getAuthToken();
    if (!token) return [];
    try {
        const res = await fetch('https://wish-apps.onrender.com/users/notifications', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        return await res.json();
    } catch (err) {
        console.error('Failed to load notifications', err);
        return [];
    }
}

export async function markAsRead(notifId) {
    const token = getAuthToken();
    if (!token) return;
    try {
        await fetch(`https://wish-apps.onrender.com/users/notifications/${notifId}/read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` }
        });
    } catch (err) {
        console.error(err);
    }
}

export async function initNotificationBell(bellElement, countSpanElement, dropdownElement) {
    async function updateCount() {
        const count = await fetchUnreadCount();
        currentUnreadCount = count;
        if (count > 0) {
            countSpanElement.textContent = count;
            countSpanElement.style.display = 'inline-block';
        } else {
            countSpanElement.style.display = 'none';
        }
    }

    async function showDropdown() {
        const notifs = await loadNotifications();
        if (!notifs.length) {
            dropdownElement.innerHTML = '<div class="notif-dropdown-item">No notifications</div>';
        } else {
            dropdownElement.innerHTML = notifs.map(n => `
                <div class="notif-dropdown-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
                    ${escapeHtml(n.message)}
                    <span class="notif-time">${new Date(n.created_at).toLocaleString()}</span>
                </div>
            `).join('');
            // Mark as read when clicked
            dropdownElement.querySelectorAll('.notif-dropdown-item').forEach(item => {
                item.addEventListener('click', async () => {
                    const id = parseInt(item.dataset.id);
                    if (!item.classList.contains('unread')) return;
                    await markAsRead(id);
                    await updateCount();
                    await showDropdown(); // refresh list
                });
            });
        }
        dropdownElement.style.display = 'block';
    }

    bellElement.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (dropdownElement.style.display === 'block') {
            dropdownElement.style.display = 'none';
        } else {
            await updateCount();
            await showDropdown();
        }
    });

    document.addEventListener('click', (e) => {
        if (!bellElement.contains(e.target) && !dropdownElement.contains(e.target)) {
            dropdownElement.style.display = 'none';
        }
    });

    await updateCount();
    setInterval(updateCount, 30000);
}

function escapeHtml(str) {
    return String(str).replace(/[&<>]/g, m => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;' }[m]));
}