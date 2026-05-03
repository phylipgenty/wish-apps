export function showFlagModal(onSubmit) {
    // Remove existing modal if any
    const existing = document.getElementById('custom-modal');
    if (existing) existing.remove();

    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'custom-modal';
    modalOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;

    const modalBox = document.createElement('div');
    modalBox.style.cssText = `
        background: white;
        border-radius: 32px;
        padding: 24px;
        width: 90%;
        max-width: 400px;
        box-shadow: 0 20px 35px rgba(0,0,0,0.2);
        text-align: center;
    `;
    modalBox.innerHTML = `
        <h3 style="margin-bottom: 16px; color:#8a2be2;">🚩 Flag this wish</h3>
        <p style="margin-bottom: 12px; font-size:14px; color:#555;">Why is this inappropriate?</p>
        <textarea id="flag-reason" rows="3" style="width:100%; padding:12px; border-radius:16px; border:1px solid #ddd; margin-bottom:20px; font-size:14px;" placeholder="e.g., Spam, offensive, scam..."></textarea>
        <div style="display:flex; gap:12px;">
            <button id="modal-submit" style="flex:1; background:#8a2be2; color:white; border:none; padding:12px; border-radius:60px; font-weight:bold;">Submit</button>
            <button id="modal-cancel" style="flex:1; background:#f0f0f0; border:none; padding:12px; border-radius:60px;">Cancel</button>
        </div>
    `;

    modalOverlay.appendChild(modalBox);
    document.body.appendChild(modalOverlay);

    const submitBtn = modalBox.querySelector('#modal-submit');
    const cancelBtn = modalBox.querySelector('#modal-cancel');
    const textarea = modalBox.querySelector('#flag-reason');

    function close() {
        modalOverlay.remove();
    }

    submitBtn.onclick = () => {
        const reason = textarea.value.trim();
        if (reason) {
            close();
            onSubmit(reason);
        } else {
            // simple inline error
            textarea.style.borderColor = '#ef4444';
            setTimeout(() => { textarea.style.borderColor = '#ddd'; }, 1000);
        }
    };
    cancelBtn.onclick = close;
    // click outside also close
    modalOverlay.onclick = (e) => { if (e.target === modalOverlay) close(); };
}