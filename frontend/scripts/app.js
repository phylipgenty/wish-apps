import { getAuthToken, getRandomWish, grantWish, reportWish, getMe } from './api.js';
import { initSwipe } from './swipe.js';
import { showToast } from './toast.js';
import { showFlagModal } from './modal.js';

let seenWishIds = new Set();
let currentWishId = null;

if (!getAuthToken()) window.location.href = '/login.html';

getMe().catch(() => window.location.href = '/login.html');

async function loadNextCard() {
    try {
        let attempts = 0;
        let wish = null;
        while (attempts < 10) {
            wish = await getRandomWish();
            if (!seenWishIds.has(wish.id)) break;
            attempts++;
        }
        if (seenWishIds.has(wish.id)) {
            document.querySelector('.card-stack').innerHTML = '<div class="card">🎉 You\'ve seen all wishes! Post a new one.</div>';
            return;
        }
        seenWishIds.add(wish.id);
        currentWishId = wish.id;
        displayCard(wish);
    } catch (err) {
        console.error(err);
        document.querySelector('.card-stack').innerHTML = '<div class="card">No wishes available. Post one!</div>';
    }
}

function displayCard(wish) {
    const stack = document.querySelector('.card-stack');
    const imageUrl = wish.proof_url ? `http://127.0.0.1:8000${wish.proof_url}` : null;
    const imageHtml = imageUrl ? `<div class="card-image"><img src="${imageUrl}" alt="Proof"></div>` : '';
    const costNgn = (wish.estimated_cost * 1500).toLocaleString();  // <-- FIX: compute ngnCost here
    const posterHtml = wish.is_anonymous ? 'Anonymous' : `<a href="/public-profile.html?user_id=${wish.user_id}" style="color:#8a2be2; text-decoration:none;">${escapeHtml(wish.username)}</a>`;
    
    stack.innerHTML = `
        <div class="card" data-id="${wish.id}">
            ${imageHtml}
            <div class="card-cost">💰 ₦${costNgn}</div>
            <h2>${escapeHtml(wish.title)}</h2>
            <p>${escapeHtml(wish.description)}</p>
            <div class="card-meta">🏷 ${escapeHtml(wish.category_tag)} | ${escapeHtml(wish.wish_type)}</div>
            <div class="card-user">👤 Posted by: ${posterHtml}</div>
        </div>
    `;
    const cardEl = stack.querySelector('.card');
    initSwipe(cardEl,
        () => handleGrant(wish.id),
        () => loadNextCard(),
        () => handleReport(wish.id)
    );
}

function handleGrant(wishId) {
    let queue = JSON.parse(localStorage.getItem('grantQueue') || '[]');
    if (!queue.includes(wishId)) {
        queue.push(wishId);
        localStorage.setItem('grantQueue', JSON.stringify(queue));
        showToast('💚 Added to grant queue! Go to Dashboard to confirm.', 'success');
    } else {
        showToast('Already in your queue.', 'info');
    }
    loadNextCard();
}

function handleReport(wishId) {
    showFlagModal(async (reason) => {
        try {
            await reportWish(wishId, reason);
            showToast('📢 Report submitted. Thank you for keeping Wishbridge safe!', 'info');
            loadNextCard();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>]/g, m => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;' }[m]));
}

loadNextCard();