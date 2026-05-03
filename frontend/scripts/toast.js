// Toast notification system
let toastContainer = null;

function getContainer() {
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'wishbridge-toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
    }
    return toastContainer;
}

export function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#8a2be2',
        warning: '#f59e0b'
    };
    const bgColor = colors[type] || colors.info;
    
    toast.style.cssText = `
        background: white;
        color: ${bgColor};
        border-left: 5px solid ${bgColor};
        padding: 12px 24px;
        border-radius: 60px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
        font-weight: 600;
        font-size: 0.9rem;
        backdrop-filter: blur(8px);
        background: rgba(255,255,255,0.95);
        transition: all 0.2s ease;
        pointer-events: none;
        min-width: 200px;
        text-align: center;
    `;
    toast.textContent = message;
    
    const container = getContainer();
    container.appendChild(toast);
    
    // Animate in
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity = '0';
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    });
    
    // Auto remove after 2.5 seconds
    setTimeout(() => {
        toast.style.transform = 'translateY(20px)';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 200);
    }, 2500);
}