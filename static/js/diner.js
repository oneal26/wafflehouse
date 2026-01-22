// Waffle House Simulator - Client-side JavaScript (Refactored)

// Check if Socket.IO is available
if (typeof io === 'undefined') {
    console.error('Socket.IO is not defined! Cannot connect to server.');
    alert('Error: Socket.IO library not loaded. Please refresh the page.');
} else {
    console.log('Initializing Socket.IO connection...');
}

const socket = io();

// Global state
let currentSupplies = {};
let currentCash = 0;
let currentAchievements = [];

// Initialize cash from DOM on page load
document.addEventListener('DOMContentLoaded', () => {
    const cashDisplay = document.getElementById('cash-display');
    if (cashDisplay) {
        const cashText = cashDisplay.textContent.replace('$', '');
        currentCash = parseFloat(cashText) || 0;
    }
});

// Supply costs (must match backend)
const SUPPLY_COSTS = {
    'batter': 5,
    'eggs': 8,
    'bacon': 10,
    'sausage': 10,
    'coffee_beans': 6,
    'hash_browns': 7,
    'bread': 4
};

// Audio management
const sounds = {
    order_ding: new Audio('/static/sounds/order_ding.mp3'),
    sizzle: new Audio('/static/sounds/sizzle.mp3'),
    plate_clang: new Audio('/static/sounds/plate_clang.mp3'),
    spray_bottle: new Audio('/static/sounds/spray_bottle.mp3'),
    sparkle: new Audio('/static/sounds/sparkle.mp3'),
    achievement: new Audio('/static/sounds/achievement.mp3'),
    ambient: document.getElementById('ambient-audio')
};

// Set volumes
Object.values(sounds).forEach(sound => {
    if (sound) sound.volume = 0.3;
});

// Play ambient sound on user interaction
let ambientStarted = false;
function startAmbient() {
    if (!ambientStarted && sounds.ambient) {
        sounds.ambient.play().catch(e => console.log('Ambient audio blocked:', e));
        ambientStarted = true;
    }
}

document.body.addEventListener('click', startAmbient, { once: true });

// Play sound effect
function playSound(soundName) {
    startAmbient();
    if (sounds[soundName]) {
        sounds[soundName].currentTime = 0;
        sounds[soundName].play().catch(e => console.log('Sound blocked:', e));
    }
}

// Activity feed
function addToFeed(message, type = 'info') {
    const feed = document.getElementById('activity-feed');
    const item = document.createElement('div');
    item.className = 'feed-item';
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    item.innerHTML = `
        <span class="timestamp">${timeStr}</span>
        <span class="message">${message}</span>
    `;
    
    feed.insertBefore(item, feed.firstChild);
    
    // Keep only last 10 items
    while (feed.children.length > 10) {
        feed.removeChild(feed.lastChild);
    }
}

// Socket.IO connection handlers (must be after addToFeed is defined)
socket.on('connect', () => {
    console.log('Socket.IO connected! ID:', socket.id);
    addToFeed('Connected to server', 'success');
    
    // Request supplies after a brief delay to ensure backend is ready
    setTimeout(() => {
        console.log('[SUPPLIES] Requesting supplies...');
        socket.emit('get_supplies');
    }, 100);
});

socket.on('disconnect', () => {
    console.log('Socket.IO disconnected');
    addToFeed('Disconnected from server', 'error');
});

socket.on('connect_error', (error) => {
    console.error('Socket.IO connection error:', error);
    addToFeed('Connection error', 'error');
});

// Update player stats in real-time
function updateStats(data) {
    // Update cash
    if (data.cash !== undefined) {
        currentCash = data.cash;
        const cashDisplay = document.getElementById('cash-display');
        if (cashDisplay) {
            cashDisplay.textContent = `$${data.cash.toFixed(2)}`;
        }
        const modalCash = document.getElementById('modal-cash');
        if (modalCash) {
            modalCash.textContent = data.cash.toFixed(2);
        }
    }
    
    // Update other stats
    if (data.total_orders !== undefined) {
        const el = document.getElementById('stat-orders');
        if (el) el.textContent = data.total_orders;
    }
    if (data.total_cooked !== undefined) {
        const el = document.getElementById('stat-cooked');
        if (el) el.textContent = data.total_cooked;
    }
    if (data.total_cleanings !== undefined) {
        const el = document.getElementById('stat-cleanings');
        if (el) el.textContent = data.total_cleanings;
    }
    if (data.experience !== undefined) {
        const el = document.querySelector('.experience');
        if (el) el.textContent = `${data.experience} XP`;
    }
}

// Update supplies display
function updateSuppliesDisplay(supplies) {
    console.log('[SUPPLIES] Updating display with:', supplies);
    currentSupplies = supplies;
    const list = document.getElementById('supplies-list');
    if (!list) {
        console.error('[SUPPLIES] supplies-list element not found!');
        return;
    }
    
    list.innerHTML = Object.entries(supplies)
        .map(([name, qty]) => `
            <div class="supply-item ${qty <= 3 ? 'low-supply' : ''}">
                <span class="supply-name">${name.replace('_', ' ')}</span>
                <span class="supply-qty">${qty}</span>
            </div>
        `).join('');
    console.log('[SUPPLIES] Display updated, currentSupplies:', currentSupplies);
}

// Update player count
function updatePlayerCount(count) {
    document.getElementById('player-count').textContent = count;
}

// Socket events - removed duplicate connect handler, consolidated above

socket.on('player_joined', (data) => {
    addToFeed(`${data.username} started their shift`);
    updatePlayerCount(data.player_count);
});

socket.on('player_left', (data) => {
    addToFeed(`${data.username} clocked out`);
    updatePlayerCount(data.player_count);
});

socket.on('station_changed', (data) => {
    addToFeed(`${data.username} moved to ${data.station} station`);
});

// Real-time stats updates
socket.on('stats_updated', (data) => {
    updateStats(data);
});

// Supplies updated
socket.on('supplies_updated', (supplies) => {
    console.log('[SUPPLIES] Received supplies update:', supplies);
    updateSuppliesDisplay(supplies);
    
    // If supply modal is open, refresh it
    const supplyModal = document.getElementById('supply-modal');
    if (supplyModal && !supplyModal.classList.contains('hidden')) {
        // Refresh modal content
        const modalCash = document.getElementById('modal-cash');
        if (modalCash) {
            modalCash.textContent = currentCash.toFixed(2);
        }
        
        // Update current quantities in modal
        Object.entries(supplies).forEach(([supply, qty]) => {
            const currentEl = document.querySelector(`[data-supply="${supply}"]`)?.parentElement?.parentElement?.querySelector('.supply-order-current');
            if (currentEl) {
                currentEl.textContent = `Current: ${qty}`;
            }
        });
    }
});

// Achievements loaded
socket.on('achievements_loaded', (achievements) => {
    currentAchievements = achievements;
});

// Level up notification
socket.on('level_up', (data) => {
    addToFeed(`LEVEL UP! Reached Level ${data.new_level}! +$${data.cash_reward}`, 'success');
    playSound('achievement');
    
    // Update level display
    const levelEl = document.querySelector('.level');
    if (levelEl) {
        levelEl.textContent = `Lv. ${data.new_level}`;
    }
});

// Customer left angry
socket.on('customer_left', (data) => {
    const streakMsg = data.streak_reset ? ' Streak reset!' : '';
    addToFeed(`Customer #${data.order_number} left angry! -${data.penalty_xp} XP.${streakMsg}`, 'error');
    playSound('spray_bottle');
    
    // Remove customer card from UI
    const card = document.querySelector(`.order-card[data-order-id="${data.order_id}"]`);
    if (card) {
        card.classList.add('order-angry');
        setTimeout(() => {
            card.style.opacity = '0';
            setTimeout(() => {
                card.remove();
                
                // Check if queue is empty
                const queue = document.getElementById('order-queue');
                if (queue && queue.children.length === 0) {
                    queue.innerHTML = '<div class="empty-state">No customers yet... waiting for the rush!</div>';
                }
            }, 300);
        }, 500);
    }
});

// Achievement unlocked
socket.on('achievement_unlocked', (achievement) => {
    addToFeed(`Achievement Unlocked: ${achievement.name}!`, 'success');
    playSound('achievement');
    currentAchievements.push(achievement);
});

// Supplies ordered
socket.on('supplies_ordered', (data) => {
    addToFeed(`${data.username} ordered ${data.quantity}x ${data.supply.replace('_', ' ')} for $${data.cost.toFixed(2)}`);
});

// Error handling
socket.on('error', (data) => {
    addToFeed(data.message, 'error');
});

// Insufficient supplies
socket.on('insufficient_supplies', (data) => {
    addToFeed(`Cannot cook ${data.dish} - missing supplies!`, 'error');
    
    // Re-enable the cook button
    const btn = document.querySelector(`button[data-order-id="${data.order_id}"]`);
    if (btn) btn.disabled = false;
});

// ===== UNIFIED ORDER SYSTEM =====

// Customer arrives with an order
socket.on('customer_arrived', (order) => {
    const cashStr = order.cash_reward > 0 ? ` (+$${order.cash_reward})` : '';
    addToFeed(`Customer #${order.order_number} wants ${order.name}${cashStr}`);
    playSound('order_ding');
    addOrderToQueue(order);
});

function addOrderToQueue(order) {
    const queue = document.getElementById('order-queue');
    
    // Remove empty state
    const emptyState = queue.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    
    const card = document.createElement('div');
    card.className = 'order-card order-waiting';
    card.dataset.orderId = order.id;
    card.dataset.status = 'waiting';
    
    // Check if we have supplies for this order
    const hasSupplies = checkSupplies(order.supplies);
    const suppliesNeeded = Object.entries(order.supplies || {})
        .map(([name, qty]) => `${qty}x ${name.replace('_', ' ')}`)
        .join(', ');
    
    card.innerHTML = `
        <div class="order-info">
            <div class="order-number">Order #${order.order_number}</div>
            <div class="order-name">${order.name} ${order.cash_reward > 0 ? `<span class="cash-reward">+$${order.cash_reward}</span>` : ''}</div>
            <div class="order-items">${order.items.join(', ')}</div>
            ${suppliesNeeded ? `<div class="supplies-needed ${!hasSupplies ? 'missing-supplies' : ''}">Needs: ${suppliesNeeded}</div>` : ''}
            <div class="order-timer" data-timer-type="waiting">Time left: <span class="timer-value">30s</span></div>
        </div>
        <button class="action-btn cook-btn" data-order-id="${order.id}" 
                data-cook-time="${order.cook_time}" ${!hasSupplies ? 'disabled' : ''}>
            Cook (${order.cook_time}s)
        </button>
    `;
    
    queue.appendChild(card);
    
    // Start waiting timer
    startWaitingTimer(order.id);
    
    // Add click handler to cook button
    const cookBtn = card.querySelector('.cook-btn');
    cookBtn.addEventListener('click', () => {
        const orderId = parseInt(cookBtn.dataset.orderId);
        socket.emit('start_cooking', { order_id: orderId });
        cookBtn.disabled = true;
    });
}

function checkSupplies(needed) {
    if (!needed || Object.keys(needed).length === 0) return true;
    
    console.log('[SUPPLY CHECK] Checking supplies:', needed);
    console.log('[SUPPLY CHECK] Current supplies:', currentSupplies);
    
    for (const [supply, qty] of Object.entries(needed)) {
        const available = currentSupplies[supply] || 0;
        console.log(`[SUPPLY CHECK] ${supply}: need ${qty}, have ${available}`);
        if (available < qty) {
            console.log(`[SUPPLY CHECK] INSUFFICIENT: ${supply}`);
            return false;
        }
    }
    console.log('[SUPPLY CHECK] All supplies available');
    return true;
}

// Track timers for waiting customers
const waitingTimers = {};

function startWaitingTimer(orderId) {
    const startTime = Date.now();
    const maxWaitTime = 30; // 30 seconds
    
    waitingTimers[orderId] = setInterval(() => {
        const card = document.querySelector(`.order-card[data-order-id="${orderId}"]`);
        if (!card || card.dataset.status !== 'waiting') {
            clearInterval(waitingTimers[orderId]);
            delete waitingTimers[orderId];
            return;
        }
        
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const remaining = maxWaitTime - elapsed;
        const timerEl = card.querySelector('.timer-value');
        
        if (timerEl) {
            if (remaining > 0) {
                timerEl.textContent = `${remaining}s`;
                
                // Warning color if running out of time
                if (remaining <= 10) {
                    card.classList.add('order-urgent');
                }
            } else {
                timerEl.textContent = '0s';
                card.classList.add('order-urgent');
            }
        }
    }, 1000);
}

// Cooking started - update card in place
socket.on('cooking_started', (data) => {
    addToFeed(`${data.username} started cooking ${data.dish}`);
    playSound(data.sound);
    
    const card = document.querySelector(`.order-card[data-order-id="${data.order_id}"]`);
    if (!card) return;
    
    // Update card to cooking state
    card.className = 'order-card order-cooking';
    card.dataset.status = 'cooking';
    
    // Update timer display
    const timerEl = card.querySelector('.order-timer');
    if (timerEl) {
        timerEl.dataset.timerType = 'cooking';
        timerEl.innerHTML = 'Cooking: <span class="timer-value">0s</span>';
    }
    
    // Replace button with countdown
    const btn = card.querySelector('.cook-btn');
    if (btn) {
        btn.remove();
    }
    
    // Start cooking countdown
    let timeLeft = data.cook_time;
    const timerValue = card.querySelector('.timer-value');
    
    const interval = setInterval(() => {
        timeLeft--;
        if (timerValue) {
            timerValue.textContent = `${timeLeft}s`;
        }
        
        if (timeLeft <= 0) {
            clearInterval(interval);
            socket.emit('complete_cooking', { order_id: data.order_id });
        }
    }, 1000);
});

// Cooking completed - update card to ready state
socket.on('cooking_completed', (data) => {
    addToFeed(`${data.dish} is ready!`);
    playSound(data.sound);
    
    const card = document.querySelector(`.order-card[data-order-id="${data.order_id}"]`);
    if (!card) return;
    
    // Update card to ready state
    card.className = 'order-card order-ready';
    card.dataset.status = 'ready';
    
    // Update display
    const timerEl = card.querySelector('.order-timer');
    if (timerEl) {
        timerEl.innerHTML = '<span class="ready-indicator">✓ READY - Click to Deliver!</span>';
    }
    
    // Make entire card clickable for delivery
    card.style.cursor = 'pointer';
    card.addEventListener('click', () => {
        if (card.dataset.status === 'ready') {
            socket.emit('deliver_order', { order_id: data.order_id });
            card.style.pointerEvents = 'none';
            card.style.opacity = '0.5';
        }
    });
});

// Order delivered - remove card
socket.on('order_delivered', (data) => {
    const cashStr = data.cash_earned ? ` (+$${data.cash_earned})` : '';
    addToFeed(`${data.username} delivered Order #${data.order_number}${cashStr}!`);
    playSound(data.sound);
    
    const card = document.querySelector(`.order-card[data-order-id="${data.order_id}"]`);
    if (card) {
        card.classList.add('order-completed');
        setTimeout(() => {
            card.style.opacity = '0';
            setTimeout(() => {
                card.remove();
                
                // Check if queue is empty
                const queue = document.getElementById('order-queue');
                if (queue && queue.children.length === 0) {
                    queue.innerHTML = '<div class="empty-state">No customers yet... waiting for the rush!</div>';
                }
            }, 300);
        }, 500);
    }
});

// ===== CLEANING SYSTEM =====

document.querySelectorAll('.clean-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const taskType = btn.dataset.task;
        const location = btn.dataset.location;
        
        socket.emit('start_cleaning', { 
            task_type: taskType,
            location: location
        });
        
        playSound('spray_bottle');
        
        btn.disabled = true;
        
        // Re-enable after 20 seconds (cooldown)
        setTimeout(() => {
            btn.disabled = false;
        }, 20000);
    });
});

socket.on('cleaning_completed', (data) => {
    addToFeed(`${data.username} finished cleaning ${data.location}!`);
    playSound(data.sound);
});

// ===== SURREAL EVENTS =====

socket.on('surreal_event', (event) => {
    showEventOverlay(event);
    addToFeed(`Event: ${event.title}`, 'event');
    playSound('achievement');
});

function showEventOverlay(event) {
    const overlay = document.getElementById('event-overlay');
    const title = document.getElementById('event-title');
    const type = document.getElementById('event-type');
    const description = document.getElementById('event-description');
    const effects = document.getElementById('event-effects');
    const resolutions = document.getElementById('event-resolutions');
    const timeRemaining = document.getElementById('event-time-remaining');
    
    title.textContent = event.title;
    type.textContent = event.type;
    type.className = `event-type ${event.type}`;
    description.textContent = event.description;
    
    // Show effects
    const effectsList = Object.keys(event.effects).map(key => 
        key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    ).join(' • ');
    effects.textContent = `Effects: ${effectsList}`;
    
    // Add resolution options
    resolutions.innerHTML = event.resolution_options.map((option, index) => `
        <button class="resolution-btn" data-resolution="${option}">
            ${option}
        </button>
    `).join('');
    
    // Add click handlers to resolution buttons
    document.querySelectorAll('.resolution-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const resolution = btn.dataset.resolution;
            socket.emit('resolve_event', { resolution });
            hideEventOverlay();
            playSound('achievement');
        });
    });
    
    // Start countdown timer
    let secondsLeft = event.duration;
    updateTimer(secondsLeft);
    
    const timerInterval = setInterval(() => {
        secondsLeft--;
        updateTimer(secondsLeft);
        
        if (secondsLeft <= 0) {
            clearInterval(timerInterval);
        }
    }, 1000);
    
    function updateTimer(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        timeRemaining.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    overlay.classList.remove('hidden');
}

function hideEventOverlay() {
    const overlay = document.getElementById('event-overlay');
    overlay.classList.add('hidden');
}

socket.on('event_resolved', (data) => {
    const rewardMsg = `+${data.xp_earned} XP, +$${data.cash_earned}`;
    addToFeed(`${data.username} resolved: ${data.resolution} - ${data.outcome} (${rewardMsg})`);
    playSound(data.sound);
    hideEventOverlay();
});

socket.on('event_expired', (data) => {
    addToFeed(`The event has passed...`, 'warning');
    hideEventOverlay();
});

// ===== SUPPLY ORDERING MODAL =====

const supplyModal = document.getElementById('supply-modal');
const orderSuppliesBtn = document.getElementById('order-supplies-btn');
const closeModalBtn = document.getElementById('close-supply-modal');

orderSuppliesBtn.addEventListener('click', () => {
    openSupplyModal();
});

closeModalBtn.addEventListener('click', () => {
    supplyModal.classList.add('hidden');
});

function openSupplyModal() {
    const modalCash = document.getElementById('modal-cash');
    modalCash.textContent = currentCash.toFixed(2);
    
    const orderList = document.getElementById('supply-order-list');
    orderList.innerHTML = Object.entries(SUPPLY_COSTS)
        .map(([supply, cost]) => {
            const currentQty = currentSupplies[supply] || 0;
            return `
                <div class="supply-order-item">
                    <div class="supply-order-info">
                        <div class="supply-order-name">${supply.replace('_', ' ')}</div>
                        <div class="supply-order-current">Current: ${currentQty}</div>
                    </div>
                    <div class="supply-order-actions">
                        <span class="supply-order-cost">$${cost} each</span>
                        <button class="action-btn order-btn" data-supply="${supply}" data-cost="${cost}">
                            Order 5x
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    
    // Add click handlers
    orderList.querySelectorAll('.order-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const supply = btn.dataset.supply;
            const cost = parseFloat(btn.dataset.cost);
            const quantity = 5;
            const totalCost = cost * quantity;
            
            if (currentCash >= totalCost) {
                socket.emit('order_supplies', { supply, quantity });
                btn.disabled = true;
                setTimeout(() => btn.disabled = false, 1000);
            } else {
                addToFeed(`Not enough cash! Need $${totalCost.toFixed(2)}`, 'error');
            }
        });
    });
    
    supplyModal.classList.remove('hidden');
}

// Visual effects for button clicks
document.addEventListener('click', (e) => {
    if (e.target.matches('button')) {
        // Ripple effect
        const ripple = document.createElement('span');
        ripple.style.position = 'absolute';
        ripple.style.width = '20px';
        ripple.style.height = '20px';
        ripple.style.background = 'rgba(244, 208, 63, 0.6)';
        ripple.style.borderRadius = '50%';
        ripple.style.pointerEvents = 'none';
        ripple.style.left = e.clientX + 'px';
        ripple.style.top = e.clientY + 'px';
        ripple.style.transform = 'translate(-50%, -50%)';
        ripple.style.animation = 'ripple 0.6s ease-out';
        
        document.body.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            width: 100px;
            height: 100px;
            opacity: 0;
        }
    }
    
    .pulse {
        animation: pulse 0.3s ease;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(0.95); }
    }
`;
document.head.appendChild(style);

console.log('Waffle House Simulator loaded');
console.log('May your hash browns always be scattered, smothered, and covered.');
