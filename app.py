"""
Waffle House Simulator - A relaxing multiplayer diner experience
with surreal, satisfying interactions
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import check_password_hash
import json
import random
import time
from datetime import datetime, timedelta
import os

from models import init_db, User, GameState, Supplies, Achievements, get_db

app = Flask(__name__)
# Use a fixed secret key for development (change in production!)
app.config['SECRET_KEY'] = 'waffle-house-dev-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Load surreal events
with open('surreal_events.json', 'r') as f:
    SURREAL_EVENTS = json.load(f)['events']

# Global game state
ACTIVE_PLAYERS = {}  # session_id -> user_data
CURRENT_EVENT = None
EVENT_TIMER = None
ACTIVE_ORDERS = {}  # order_id -> order_data
ORDER_COUNTER = 100

# Menu items for random customer orders
MENU_ITEMS = [
    # Orders requiring supplies
    {
        "name": "Basic Breakfast",
        "items": ["Waffle", "Coffee"],
        "cook_time": 8,
        "cash_reward": 15,
        "supplies": {"batter": 1, "coffee_beans": 1}
    },
    {
        "name": "Hash Brown Special",
        "items": ["Hash Browns (Scattered)", "Bacon", "Toast"],
        "cook_time": 12,
        "cash_reward": 22,
        "supplies": {"hash_browns": 1, "bacon": 2, "bread": 1}
    },
    {
        "name": "All Star Special",
        "items": ["Waffle", "Hash Browns", "Eggs", "Sausage"],
        "cook_time": 15,
        "cash_reward": 35,
        "supplies": {"batter": 1, "hash_browns": 1, "eggs": 2, "sausage": 2}
    },
    {
        "name": "Pecan Waffle",
        "items": ["Pecan Waffle", "Whipped Cream"],
        "cook_time": 10,
        "cash_reward": 18,
        "supplies": {"batter": 1}
    },
    {
        "name": "Bacon & Eggs",
        "items": ["Bacon", "Eggs", "Toast"],
        "cook_time": 10,
        "cash_reward": 20,
        "supplies": {"bacon": 3, "eggs": 2, "bread": 2}
    },
    {
        "name": "Coffee & Toast",
        "items": ["Coffee", "Toast"],
        "cook_time": 5,
        "cash_reward": 10,
        "supplies": {"coffee_beans": 1, "bread": 2}
    },
    # No-supply orders (always available)
    {
        "name": "Ice Water",
        "items": ["Ice Water"],
        "cook_time": 2,
        "cash_reward": 2,
        "supplies": {}
    },
    {
        "name": "A Hug",
        "items": ["Warm Hug"],
        "cook_time": 3,
        "cash_reward": 5,
        "supplies": {}
    },
    {
        "name": "Directions",
        "items": ["Directions to Nearest Gas Station"],
        "cook_time": 4,
        "cash_reward": 3,
        "supplies": {}
    },
    {
        "name": "Life Advice",
        "items": ["Unsolicited Life Advice"],
        "cook_time": 5,
        "cash_reward": 8,
        "supplies": {}
    },
]

# Supply costs for ordering
SUPPLY_COSTS = {
    'batter': 5,
    'eggs': 8,
    'bacon': 10,
    'sausage': 10,
    'coffee_beans': 6,
    'hash_browns': 7,
    'bread': 4,
}

def load_random_event():
    """Load a random surreal event based on weights"""
    total_weight = sum(event['weight'] for event in SURREAL_EVENTS)
    random_weight = random.uniform(0, total_weight)
    
    current_weight = 0
    for event in SURREAL_EVENTS:
        current_weight += event['weight']
        if random_weight <= current_weight:
            return event.copy()
    
    return random.choice(SURREAL_EVENTS).copy()

def trigger_event():
    """Trigger a new surreal event"""
    global CURRENT_EVENT, EVENT_TIMER
    
    if CURRENT_EVENT is None:
        event = load_random_event()
        event_log_id = GameState.log_event(event['id'], event)
        event['log_id'] = event_log_id
        event['triggered_at'] = datetime.now().isoformat()
        
        CURRENT_EVENT = event
        EVENT_TIMER = time.time() + event['duration']
        
        socketio.emit('surreal_event', event, room='diner')
        print(f"🌀 Event triggered: {event['title']}")

def check_event_timer():
    """Check if current event should expire"""
    global CURRENT_EVENT, EVENT_TIMER
    
    if CURRENT_EVENT and EVENT_TIMER:
        if time.time() > EVENT_TIMER:
            socketio.emit('event_expired', {'event_id': CURRENT_EVENT['id']}, room='diner')
            CURRENT_EVENT = None
            EVENT_TIMER = None

@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        return redirect(url_for('diner'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.create(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'redirect': url_for('diner')})
    else:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    """Login existing user"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    user = User.verify_password(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'redirect': url_for('diner')})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/diner')
def diner():
    """Main diner interface"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = User.get_by_id(session['user_id'])
    leaderboard = User.get_leaderboard(5)
    active_players = GameState.get_active_players()
    active_events = GameState.get_active_events()
    
    return render_template('diner.html', 
                         user=user, 
                         leaderboard=leaderboard,
                         active_players=active_players,
                         active_events=active_events)

# SocketIO Events
@socketio.on('connect')
def handle_connect(auth=None):
    """Handle new WebSocket connection"""
    print(f"WebSocket connection attempt - Session keys: {session.keys() if session else 'No session'}")
    if 'user_id' in session:
        user_id = session['user_id']
        username = session['username']
        sid = request.sid
        
        # Join the main diner room
        join_room('diner')
        
        # Track active player
        ACTIVE_PLAYERS[sid] = {
            'user_id': user_id,
            'username': username,
            'station': None,
            'connected_at': datetime.now().isoformat()
        }
        
        print(f"Player {username} connected! SID: {sid}, Active players: {len(ACTIVE_PLAYERS)}")
        
        # Update database
        GameState.update_session(user_id, sid)
        
        # Notify others
        emit('player_joined', {
            'username': username,
            'player_count': len(ACTIVE_PLAYERS)
        }, room='diner')
    else:
        print(f"Connection rejected - no user_id in session")
        
        # Send current event if active
        if CURRENT_EVENT:
            emit('surreal_event', CURRENT_EVENT)
        
        # Send current active orders
        for order in ACTIVE_ORDERS.values():
            emit('customer_arrived', order)
        
        # Send user's current supplies and cash
        supplies = Supplies.get_user_supplies(user_id)
        user = User.get_by_id(user_id)
        achievements = Achievements.get_user_achievements(user_id)
        
        print(f"[CONNECT] Sending supplies to {username}: {supplies}")
        emit('supplies_updated', supplies)
        emit('stats_updated', {
            'experience': user['experience'],
            'total_orders': user['total_orders'],
            'total_cleanings': user['total_cleanings'],
            'total_cooked': user['total_dishes_cooked'],
            'cash': user['cash']
        })
        emit('achievements_loaded', achievements)
        
        print(f"{username} connected ({len(ACTIVE_PLAYERS)} players online)")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    sid = request.sid
    if sid in ACTIVE_PLAYERS:
        username = ACTIVE_PLAYERS[sid]['username']
        del ACTIVE_PLAYERS[sid]
        
        emit('player_left', {
            'username': username,
            'player_count': len(ACTIVE_PLAYERS)
        }, room='diner')
        
        print(f"{username} disconnected ({len(ACTIVE_PLAYERS)} players online)")

@socketio.on('change_station')
def handle_change_station(data):
    """Handle player changing activity station"""
    sid = request.sid
    station = data.get('station')
    
    if sid in ACTIVE_PLAYERS:
        ACTIVE_PLAYERS[sid]['station'] = station
        user_id = ACTIVE_PLAYERS[sid]['user_id']
        GameState.update_session(user_id, sid, station)
        
        emit('station_changed', {
            'username': ACTIVE_PLAYERS[sid]['username'],
            'station': station
        }, room='diner')

@socketio.on('get_supplies')
def handle_get_supplies():
    """Handle explicit request for supplies"""
    sid = request.sid
    if sid in ACTIVE_PLAYERS:
        user_id = ACTIVE_PLAYERS[sid]['user_id']
        supplies = Supplies.get_user_supplies(user_id)
        print(f"[GET_SUPPLIES] User {user_id} requested supplies: {supplies}")
        emit('supplies_updated', supplies, room=sid)
    else:
        print(f"[GET_SUPPLIES] Request from unknown SID: {sid}")

def spawn_customer():
    """Spawn a new customer with a random order"""
    global ORDER_COUNTER, ACTIVE_ORDERS
    
    try:
        if len(ACTIVE_ORDERS) >= 5:  # Max 5 waiting customers
            return
        
        # Pick random menu item
        menu_item = random.choice(MENU_ITEMS).copy()
        order_number = ORDER_COUNTER
        ORDER_COUNTER += 1
        
        # Create order in database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (order_number, items, status)
            VALUES (?, ?, 'waiting')
        ''', (order_number, json.dumps(menu_item)))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add to active orders with arrival timestamp
        order_data = {
            'id': order_id,
            'order_number': order_number,
            'name': menu_item['name'],
            'items': menu_item['items'],
            'cook_time': menu_item['cook_time'],
            'cash_reward': menu_item['cash_reward'],
            'supplies': menu_item.get('supplies', {}),
            'status': 'waiting',
            'cooking_by': None,
            'started_at': None,
            'arrived_at': time.time()
        }
        ACTIVE_ORDERS[order_id] = order_data
        
        # Broadcast to all players
        socketio.emit('customer_arrived', order_data, room='diner')
        print(f"Customer #{order_number} arrived wanting {menu_item['name']}")
    except Exception as e:
        print(f"Error spawning customer: {e}")
        import traceback
        traceback.print_exc()

@socketio.on('start_cooking')
def handle_start_cooking(data):
    """Handle starting to cook an order"""
    sid = request.sid
    if sid not in ACTIVE_PLAYERS:
        return
    
    user_id = ACTIVE_PLAYERS[sid]['user_id']
    username = ACTIVE_PLAYERS[sid]['username']
    order_id = data.get('order_id')
    
    if order_id not in ACTIVE_ORDERS:
        return
    
    order = ACTIVE_ORDERS[order_id]
    
    if order['status'] != 'waiting':
        return
    
    # Check if user has required supplies
    required_supplies = order.get('supplies', {})
    if required_supplies:
        has_supplies, missing_supply = Supplies.check_and_consume(user_id, required_supplies)
        if not has_supplies:
            emit('insufficient_supplies', {
                'dish': order['name'],
                'missing': missing_supply,
                'order_id': order_id
            }, room=sid)
            return
    
    # Update order status
    order['status'] = 'cooking'
    order['cooking_by'] = username
    order['started_at'] = time.time()
    
    # Update database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET status = 'cooking', taken_by = ?
        WHERE id = ?
    ''', (user_id, order_id))
    conn.commit()
    conn.close()
    
    # Send updated supplies to user
    user_supplies = Supplies.get_user_supplies(user_id)
    emit('supplies_updated', user_supplies, room=sid)
    
    # Broadcast cooking started
    emit('cooking_started', {
        'order_id': order_id,
        'order_number': order['order_number'],
        'username': username,
        'dish': order['name'],
        'cook_time': order['cook_time'],
        'sound': 'sizzle'
    }, room='diner')

@socketio.on('complete_cooking')
def handle_complete_cooking(data):
    """Handle finishing cooking an order (it's now ready to deliver)"""
    sid = request.sid
    if sid not in ACTIVE_PLAYERS:
        return
    
    username = ACTIVE_PLAYERS[sid]['username']
    order_id = data.get('order_id')
    
    if order_id not in ACTIVE_ORDERS:
        return
    
    order = ACTIVE_ORDERS[order_id]
    
    if order['status'] != 'cooking':
        return
    
    # Mark order as ready
    order['status'] = 'ready'
    
    # Update database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET status = 'ready'
        WHERE id = ?
    ''', (order_id,))
    conn.commit()
    conn.close()
    
    # Broadcast completion
    emit('cooking_completed', {
        'order_id': order_id,
        'order_number': order['order_number'],
        'username': username,
        'dish': order['name'],
        'sound': 'plate_clang'
    }, room='diner')

@socketio.on('deliver_order')
def handle_deliver_order(data):
    """Handle delivering an order to the customer"""
    sid = request.sid
    if sid not in ACTIVE_PLAYERS:
        return
    
    user_id = ACTIVE_PLAYERS[sid]['user_id']
    username = ACTIVE_PLAYERS[sid]['username']
    order_id = data.get('order_id')
    
    if order_id not in ACTIVE_ORDERS:
        return
    
    order = ACTIVE_ORDERS[order_id]
    
    if order['status'] != 'ready':
        return
    
    # Complete order
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET status = 'delivered', completed_by = ?, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (user_id, order_id))
    conn.commit()
    conn.close()
    
    # Calculate rewards
    cash_reward = order.get('cash_reward', 10)
    xp_reward = 20
    
    # Update user stats
    user = User.get_by_id(user_id)
    new_experience = user['experience'] + xp_reward
    new_orders = user['total_orders'] + 1
    new_dishes = user['total_dishes_cooked'] + 1
    new_cash = user['cash'] + cash_reward
    
    level_up_rewards = User.update_stats(user_id,
                     total_orders=new_orders,
                     total_dishes_cooked=new_dishes,
                     experience=new_experience,
                     cash=new_cash)
    
    # Check for new achievements
    new_achievements = Achievements.check_and_award(user_id)
    
    # Remove from active orders
    del ACTIVE_ORDERS[order_id]
    
    # Get updated user data
    updated_user = User.get_by_id(user_id)
    
    # Broadcast delivery
    emit('order_delivered', {
        'order_id': order_id,
        'order_number': order['order_number'],
        'username': username,
        'cash_earned': cash_reward,
        'sound': 'achievement'
    }, room='diner')
    
    # Send stats update to the user
    emit('stats_updated', {
        'experience': updated_user['experience'],
        'total_orders': updated_user['total_orders'],
        'total_cleanings': updated_user['total_cleanings'],
        'total_cooked': updated_user['total_dishes_cooked'],
        'cash': updated_user['cash']
    }, room=sid)
    
    # Send level-up notification
    if level_up_rewards:
        emit('level_up', level_up_rewards, room=sid)
    
    # Send achievement notifications
    if new_achievements:
        for achievement in new_achievements:
            emit('achievement_unlocked', achievement, room=sid)

@socketio.on('start_cleaning')
def handle_start_cleaning(data):
    """Handle starting and immediately completing a cleaning task"""
    sid = request.sid
    if sid not in ACTIVE_PLAYERS:
        return
    
    user_id = ACTIVE_PLAYERS[sid]['user_id']
    username = ACTIVE_PLAYERS[sid]['username']
    task_type = data.get('task_type')
    location = data.get('location')
    
    # Check cooldown for this specific task (20 seconds)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT MAX(completed_at) as last_clean
        FROM cleaning_tasks
        WHERE cleaned_by = ? AND task_type = ? AND location = ?
    ''', (user_id, task_type, location))
    
    row = cursor.fetchone()
    if row and row['last_clean']:
        # Parse the SQLite timestamp (format: 'YYYY-MM-DD HH:MM:SS' or with microseconds)
        from datetime import datetime
        try:
            # Remove microseconds if present
            timestamp_str = row['last_clean'].split('.')[0]
            last_clean_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            time_since = (datetime.now() - last_clean_time).total_seconds()
            if time_since < 20:
                wait_time = 20 - time_since
                emit('error', {'message': f'Cleaning cooldown: {wait_time:.1f}s remaining'}, room=sid)
                conn.close()
                return
        except Exception as e:
            print(f"Error parsing cleaning timestamp: {e}, timestamp: {row['last_clean']}")
            # If parsing fails, allow cleaning to proceed
    
    # Create and complete cleaning task in one step
    cursor.execute('''
        INSERT INTO cleaning_tasks (task_type, location, cleaned_by, status, completed_at)
        VALUES (?, ?, ?, 'clean', CURRENT_TIMESTAMP)
    ''', (task_type, location, user_id))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Update user stats
    user = User.get_by_id(user_id)
    new_cleanings = user['total_cleanings'] + 1
    new_experience = user['experience'] + 8
    
    level_up_rewards = User.update_stats(user_id,
                     total_cleanings=new_cleanings,
                     experience=new_experience)
    
    # Get updated user data and check achievements
    updated_user = User.get_by_id(user_id)
    new_achievements = Achievements.check_and_award(user_id, updated_user)
    
    emit('cleaning_completed', {
        'task_id': task_id,
        'username': username,
        'task_type': task_type,
        'location': location,
        'sound': 'sparkle'
    }, room='diner')
    
    # Send stats update to the user
    emit('stats_updated', {
        'experience': updated_user['experience'],
        'total_orders': updated_user['total_orders'],
        'total_cleanings': updated_user['total_cleanings'],
        'total_cooked': updated_user['total_dishes_cooked'],
        'cash': updated_user['cash']
    }, room=sid)
    
    # Send level-up notification
    if level_up_rewards:
        emit('level_up', level_up_rewards, room=sid)
    
    # Emit achievement unlocks if any
    for achievement in new_achievements:
        emit('achievement_unlocked', achievement, room='diner')

@socketio.on('order_supplies')
def handle_order_supplies(data):
    """Handle ordering supplies with cash"""
    sid = request.sid
    if sid not in ACTIVE_PLAYERS:
        return
    
    user_id = ACTIVE_PLAYERS[sid]['user_id']
    username = ACTIVE_PLAYERS[sid]['username']
    supply_name = data.get('supply')
    quantity = data.get('quantity', 1)
    
    if supply_name not in SUPPLY_COSTS:
        emit('error', {'message': 'Invalid supply'})
        return
    
    # Calculate cost
    unit_cost = SUPPLY_COSTS[supply_name]
    total_cost = unit_cost * quantity
    
    # Check if user has enough cash
    user = User.get_by_id(user_id)
    if user['cash'] < total_cost:
        emit('error', {'message': f'Not enough cash. Need ${total_cost:.2f}, have ${user["cash"]:.2f}'})
        return
    
    # Deduct cash and add supplies
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET cash = cash - ? WHERE id = ?', (total_cost, user_id))
    conn.commit()
    conn.close()
    
    Supplies.update_supply(user_id, supply_name, quantity)
    
    # Get updated data
    updated_user = User.get_by_id(user_id)
    updated_supplies = Supplies.get_user_supplies(user_id)
    
    emit('supplies_ordered', {
        'username': username,
        'supply': supply_name,
        'quantity': quantity,
        'cost': total_cost
    }, room='diner')
    
    emit('supplies_updated', updated_supplies, room=sid)
    emit('stats_updated', {
        'experience': updated_user['experience'],
        'total_orders': updated_user['total_orders'],
        'total_cleanings': updated_user['total_cleanings'],
        'total_cooked': updated_user['total_dishes_cooked'],
        'cash': updated_user['cash']
    }, room=sid)

@socketio.on('resolve_event')
def handle_resolve_event(data):
    """Handle resolving a surreal event with rewards based on choice"""
    global CURRENT_EVENT, EVENT_TIMER
    
    sid = request.sid
    if sid not in ACTIVE_PLAYERS:
        return
    
    user_id = ACTIVE_PLAYERS[sid]['user_id']
    username = ACTIVE_PLAYERS[sid]['username']
    resolution = data.get('resolution')
    
    if CURRENT_EVENT:
        event_log_id = CURRENT_EVENT.get('log_id')
        if event_log_id:
            GameState.resolve_event(event_log_id, user_id)
        
        # Calculate rewards based on resolution choice and event effects
        event_effects = CURRENT_EVENT.get('effects', {})
        resolution_index = CURRENT_EVENT.get('resolution_options', []).index(resolution) if resolution in CURRENT_EVENT.get('resolution_options', []) else 0
        
        # Base rewards
        base_xp = 25
        base_cash = 20
        
        # Apply different outcomes based on choice (first choice = risky/high reward, last = safe/low reward)
        num_options = len(CURRENT_EVENT.get('resolution_options', []))
        if resolution_index == 0:  # First option - risky choice
            xp_multiplier = 2.0
            cash_multiplier = 2.5
            outcome_msg = "Bold choice! Extra rewards!"
        elif resolution_index == num_options - 1:  # Last option - safe choice
            xp_multiplier = 0.5
            cash_multiplier = 0.5
            outcome_msg = "Safe choice. Modest rewards."
        else:  # Middle options
            xp_multiplier = 1.0
            cash_multiplier = 1.0
            outcome_msg = "Balanced approach."
        
        # Apply event effect bonuses
        if 'tip_boost' in event_effects:
            cash_multiplier *= 1.5
        if 'experience_boost' in event_effects:
            xp_multiplier *= 1.3
        if 'supply_boost' in event_effects:
            # Random supply bonus
            random_supply = random.choice(list(SUPPLY_COSTS.keys()))
            bonus_qty = random.randint(3, 8)
            Supplies.update_supply(user_id, random_supply, bonus_qty)
            outcome_msg += f" +{bonus_qty} {random_supply.replace('_', ' ')}!"
        
        xp_reward = int(base_xp * xp_multiplier)
        cash_reward = int(base_cash * cash_multiplier)
        
        # Update user stats
        user = User.get_by_id(user_id)
        new_events = user['total_events_witnessed'] + 1
        new_experience = user['experience'] + xp_reward
        new_cash = user['cash'] + cash_reward
        
        level_up_rewards = User.update_stats(user_id,
                         total_events_witnessed=new_events,
                         experience=new_experience,
                         cash=new_cash)
        
        # Get updated user data and check for achievements
        updated_user = User.get_by_id(user_id)
        new_achievements = Achievements.check_and_award(user_id, updated_user)
        
        emit('event_resolved', {
            'event_id': CURRENT_EVENT['id'],
            'username': username,
            'resolution': resolution,
            'outcome': outcome_msg,
            'xp_earned': xp_reward,
            'cash_earned': cash_reward,
            'sound': 'achievement'
        }, room='diner')
        
        # Send stats update to the user
        emit('stats_updated', {
            'experience': updated_user['experience'],
            'total_orders': updated_user['total_orders'],
            'total_cleanings': updated_user['total_cleanings'],
            'total_cooked': updated_user['total_dishes_cooked'],
            'cash': updated_user['cash']
        }, room=sid)
        
        # Get updated supplies if any were added
        updated_supplies = Supplies.get_user_supplies(user_id)
        emit('supplies_updated', updated_supplies, room=sid)
        
        # Send level-up notification
        if level_up_rewards:
            emit('level_up', level_up_rewards, room=sid)
        
        # Emit achievement unlocks
        for achievement in new_achievements:
            emit('achievement_unlocked', achievement, room='diner')
        
        CURRENT_EVENT = None
        EVENT_TIMER = None

def check_customer_timeouts():
    """Check for customers who have waited too long and make them leave"""
    global ACTIVE_ORDERS
    current_time = time.time()
    timeout_duration = 30  # 30 seconds
    
    orders_to_remove = []
    for order_id, order in ACTIVE_ORDERS.items():
        if order['status'] == 'waiting' and order.get('arrived_at'):
            wait_time = current_time - order['arrived_at']
            if wait_time > timeout_duration:
                orders_to_remove.append(order_id)
    
    for order_id in orders_to_remove:
        order = ACTIVE_ORDERS[order_id]
        
        # Remove order
        del ACTIVE_ORDERS[order_id]
        
        # Apply penalty to all active players (shared responsibility!)
        # Penalty: lose XP and reset streak (no cash penalty - they need cash to order supplies!)
        penalty_xp = 15
        
        for sid, player_data in ACTIVE_PLAYERS.items():
            user_id = player_data['user_id']
            user = User.get_by_id(user_id)
            
            new_xp = max(0, user['experience'] - penalty_xp)
            new_streak = 0  # Reset their streak as additional penalty
            
            User.update_stats(user_id,
                             experience=new_xp,
                             current_streak=new_streak)
            
            updated_user = User.get_by_id(user_id)
            socketio.emit('stats_updated', {
                'experience': updated_user['experience'],
                'total_orders': updated_user['total_orders'],
                'total_cleanings': updated_user['total_cleanings'],
                'total_cooked': updated_user['total_dishes_cooked'],
                'cash': updated_user['cash'],
                'current_streak': updated_user['current_streak']
            }, room=sid)
        
        # Notify all players
        socketio.emit('customer_left', {
            'order_number': order['order_number'],
            'order_id': order_id,
            'name': order['name'],
            'penalty_xp': penalty_xp,
            'streak_reset': True
        }, room='diner')
        
        print(f"Customer #{order['order_number']} left angry (waited too long)")

# Background task for event generation and customer spawning
def background_tasks():
    """Background task runner"""
    event_check_counter = 0
    print("Background tasks thread started!")
    while True:
        socketio.sleep(5)  # Check every 5 seconds
        
        check_event_timer()
        check_customer_timeouts()
        
        # Spawn customers if players are active
        active_count = len(ACTIVE_PLAYERS)
        print(f"Background check - Active players: {active_count}, Active orders: {len(ACTIVE_ORDERS)}")
        if active_count > 0:
            if random.random() < 0.6:  # 60% chance every 5 seconds
                print("Attempting to spawn customer...")
                spawn_customer()
        
        # Check for surreal events every 30 seconds (6 iterations of 5 seconds)
        event_check_counter += 1
        if event_check_counter >= 6:
            event_check_counter = 0
            # Random chance to trigger new event (if none active)
            if CURRENT_EVENT is None and len(ACTIVE_PLAYERS) > 0:
                if random.random() < 0.2:  # 20% chance every 30 seconds
                    trigger_event()

if __name__ == '__main__':
    # Initialize database
    init_db()
    print("Waffle House Simulator starting...")
    print("Database initialized")
    print(f"{len(SURREAL_EVENTS)} surreal events loaded")
    
    # Start background tasks
    socketio.start_background_task(background_tasks)
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=3333, debug=True)
