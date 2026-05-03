export function initSwipe(cardElement, onRight, onLeft, onUp) {
    if (!cardElement) return;

    let startX, startY, startTime;
    let isDragging = false;
    let currentTransform = { x: 0, y: 0, rotate: 0 };

    // Reset card with animation
    function resetCard() {
        cardElement.style.transition = 'transform 0.2s ease-out';
        cardElement.style.transform = 'translate(0, 0) rotate(0deg)';
        setTimeout(() => {
            cardElement.style.transition = '';
        }, 200);
    }

    // Fly off screen and trigger callback
    function flyOff(deltaX, deltaY, callback) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        let targetX = 0, targetY = 0;
        if (absX > absY && absX > 50) {
            targetX = deltaX > 0 ? 1500 : -1500;
        } else if (absY > 50 && deltaY < 0) {
            targetY = -1500;
        } else {
            resetCard();
            callback(false);
            return;
        }
        cardElement.style.transition = 'transform 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1)';
        cardElement.style.transform = `translate(${targetX}px, ${targetY}px) rotate(${deltaX * 0.1}deg)`;
        setTimeout(() => {
            callback(true);
            resetCard();
        }, 250);
    }

    function handleEnd(endX, endY, elapsed) {
        if (!isDragging) return;
        isDragging = false;
        const deltaX = endX - startX;
        const deltaY = endY - startY;
        if (elapsed > 800) {
            resetCard();
            return;
        }
        flyOff(deltaX, deltaY, (triggered) => {
            if (!triggered) return;
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                deltaX > 0 ? onRight() : onLeft();
            } else if (Math.abs(deltaY) > 50 && deltaY < 0) {
                onUp();
            }
        });
    }

    // Touch events
    cardElement.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        startTime = Date.now();
        isDragging = true;
        cardElement.style.transition = 'none';
    }, { passive: false });
    cardElement.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const dx = e.touches[0].clientX - startX;
        const dy = e.touches[0].clientY - startY;
        currentTransform = { x: dx, y: dy, rotate: dx * 0.05 };
        cardElement.style.transform = `translate(${dx}px, ${dy}px) rotate(${dx * 0.05}deg)`;
    });
    cardElement.addEventListener('touchend', (e) => {
        e.preventDefault();
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        const elapsed = Date.now() - startTime;
        handleEnd(endX, endY, elapsed);
    });

    // Mouse events
    cardElement.addEventListener('dragstart', (e) => e.preventDefault());
    cardElement.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        e.preventDefault();
        startX = e.clientX;
        startY = e.clientY;
        startTime = Date.now();
        isDragging = true;
        cardElement.style.transition = 'none';
        document.body.style.userSelect = 'none';

        const onMouseMove = (moveEvent) => {
            if (!isDragging) return;
            const dx = moveEvent.clientX - startX;
            const dy = moveEvent.clientY - startY;
            cardElement.style.transform = `translate(${dx}px, ${dy}px) rotate(${dx * 0.05}deg)`;
        };
        const onMouseUp = (upEvent) => {
            const endX = upEvent.clientX;
            const endY = upEvent.clientY;
            const elapsed = Date.now() - startTime;
            handleEnd(endX, endY, elapsed);
            document.body.style.userSelect = '';
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
        };
        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    });
}