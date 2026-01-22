# Waffle House Simulator 🧇

A relaxing, surreal, multiplayer web experience set in a Waffle House diner. Cook orders, manage supplies, clean tables, and witness bizarre events with other players in real-time.

## Features

### 🍳 Unified Order Management
- **Single streamlined interface** - All orders in one view that updates in place
- **Auto-spawning customers** - Customers arrive randomly with orders (max 5 at once)
- **30-second countdown** - Serve customers before they leave angry
- **In-place state updates** - Watch orders move from waiting → cooking → ready to serve
- **Supply economy** - Orders require specific ingredients (batter, eggs, bacon, etc.)
- **Mobile-first design** - Optimized for phone and tablet screens

### 💰 Economic System
- **Cash rewards** - Earn $2-$35 per order based on complexity
- **Supply ordering** - Use cash to restock ingredients
- **Starter supplies** - Begin with 10 batter, 12 eggs, 8 bacon, etc.
- **Dynamic pricing** - Different supplies have different costs
- **Low supply alerts** - Visual warnings when ingredients run low

### 🎯 Progression & Rewards
- **Experience points** - Earn XP for cooking and cleaning
- **Level system** - Gain levels (100 XP per level)
- **Level-up bonuses** - Receive $50 cash reward for each level gained
- **Achievement system** - Unlock 7 achievements for milestones
- **Stat tracking** - Orders completed, dishes cooked, cleanings done

### 🧹 Cleaning Mini-Game
- **Quick cleanings** - 4 different tasks (wipe counter, mop floor, polish chrome, clear table)
- **20-second cooldowns** - Per-task cooldowns prevent spam
- **Bonus XP** - Earn 8 XP for each cleaning task
- **Side activity** - Keep busy while food is cooking

### 🌀 Surreal Events System
Experience random surreal events every 30 seconds (20% chance):
- Parking lot brawls, alien customers, time travelers
- Monks meditating on the griddle, cryptids, ghosts
- Multiple resolution options with different outcomes:
  - **Risky choice** (first option): 2.5x rewards
  - **Balanced choice** (middle options): 1x rewards
  - **Safe choice** (last option): 0.5x rewards
- Event-specific bonuses (supply boosts, tip multipliers, XP boosts)

### 👥 Real-time Multiplayer
- See other players' actions in real-time
- Watch cooking and cleaning in the activity feed
- Shared responsibility for customer satisfaction
- Live leaderboard showing top performers
- Player count indicator

### ⚠️ Penalties & Consequences
- **Customer timeouts** - Lose 15 XP if customers wait too long
- **Streak resets** - Penalty also resets your order streak
- **No cash penalties** - Keep your buying power for supplies
- **Shared consequences** - All active players share timeout penalties

### 🎨 Authentic Waffle House Aesthetic
- Dark blue and yellow color scheme
- Chrome accents and retro diner vibes
- Smooth animations and transitions
- Neon-sign title screen
- Pulsing "ready" indicators for completed orders

## Tech Stack

- **Backend**: Flask 3.0.0 + Flask-SocketIO 5.3.6 (threading mode)
- **Database**: SQLite with persistent disk storage
- **Frontend**: Vanilla JavaScript + Socket.IO 4.5.4 client
- **Styling**: Custom CSS with responsive design and animations
- **Real-time**: WebSocket communication for multiplayer

## Installation

### Prerequisites
- Python 3.8+ (tested on Python 3.13)
- pip

### Setup

1. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies (Flask, Flask-SocketIO, etc.)
   - Initialize the SQLite database with all tables

2. **Start the server:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   Or manually:
   ```bash
   source venv/bin/activate
   python3 app.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3333`

4. **Create an account** and start your shift!

## Project Structure

```
.
├── app.py                  # Main Flask application with SocketIO handlers
├── models.py              # Database models and business logic
├── requirements.txt       # Python dependencies
├── surreal_events.json   # Configuration for 20 surreal events (easily expandable!)
├── wafflehouse.db        # SQLite database (created on first run)
├── setup.sh              # Setup script (creates venv, installs deps, init DB)
├── run.sh                # Run script (activates venv and starts server)
├── templates/
│   ├── index.html        # Landing page with login/register
│   └── diner.html        # Main unified diner interface
├── static/
│   ├── css/
│   │   └── style.css     # Responsive styling with mobile-first design
│   ├── js/
│   │   └── diner.js      # Client-side logic and real-time Socket.IO handlers
│   └── sounds/
│       └── README.md     # Instructions for adding sound files (optional)
└── __pycache__/          # Python bytecode (auto-generated)
```

## Gameplay Loop

1. **Customer arrives** with an order (e.g., "Bacon & Eggs")
2. **Check supplies** - Green = good, Red = need to order
3. **Click "Cook"** - Consumes supplies and starts timer
4. **Watch countdown** - Order cooks automatically (8-15 seconds)
5. **Click to deliver** - Earn cash ($2-$35) and XP (20)
6. **Order supplies** - Use cash to restock ingredients
7. **Clean between orders** - Earn bonus XP (8 per task)
8. **Respond to events** - Random surreal events with choice-based rewards

## Menu Items

### Supply-Based Orders
- **Basic Breakfast** ($15) - Waffle + Coffee | 1 batter, 1 coffee_beans | 8s
- **Hash Brown Special** ($22) - Hash Browns + Bacon + Toast | 1 hash_browns, 2 bacon, 1 bread | 12s
- **All Star Special** ($35) - Waffle + Hash Browns + Eggs + Sausage | 1 batter, 1 hash_browns, 2 eggs, 2 sausage | 15s
- **Pecan Waffle** ($18) - Pecan Waffle + Whipped Cream | 1 batter | 10s
- **Bacon & Eggs** ($20) - Bacon + Eggs + Toast | 3 bacon, 2 eggs, 2 bread | 10s
- **Coffee & Toast** ($10) - Coffee + Toast | 1 coffee_beans, 2 bread | 5s

### No-Supply Orders (Always Available)
- **Ice Water** ($2) - 2s
- **A Hug** ($5) - Warm Hug | 3s
- **Directions** ($3) - Directions to Nearest Gas Station | 4s
- **Life Advice** ($8) - Unsolicited Life Advice | 5s

## Supply Costs

- **Batter**: $5 per unit
- **Eggs**: $8 per unit
- **Bacon**: $10 per unit
- **Sausage**: $10 per unit
- **Coffee Beans**: $6 per unit
- **Hash Browns**: $7 per unit
- **Bread**: $4 per unit

*Starter supplies: 10 batter, 12 eggs, 8 bacon, 8 sausage, 10 coffee beans, 10 hash browns, 15 bread*

## Adding New Surreal Events

Events are stored in `surreal_events.json` and can be easily expanded! Each event has:

- `id`: Unique identifier
- `title`: Display name
- `description`: Event narrative
- `type`: Category (surreal, dramatic, mystical, wholesome, spooky, stressful, supernatural)
- `duration`: How long the event lasts (seconds)
- `effects`: Gameplay modifiers
- `resolution_options`: Player choices (array with outcome-based rewards)
- `weight`: Probability weight (higher = more common)

Example:
```json
{
  "id": "griddle_gnomes",
  "title": "Griddle Gnomes",
  "description": "Tiny gnomes have appeared on the griddle, offering to cook for tips.",
  "type": "surreal",
  "duration": 60,
  "effects": {
    "cooking_speed_up": true,
    "chaos": true
  },
  "resolution_options": [
    {"choice": "Hire them immediately", "cash": 50, "xp": 30},
    {"choice": "Politely decline", "xp": 10},
    {"choice": "Take a picture", "cash": 20, "xp": 15}
  ],
  "weight": 10
}
```

**Resolution rewards**: Each choice can include `cash` (positive or negative) and `xp` bonuses. Just add your event to the `events` array in `surreal_events.json` - no code changes needed!

## Adding Sound Files

The app supports audio but will work silently without sound files. To add sounds:

1. Obtain MP3 files for:
   - `order_ding.mp3` - Order bell
   - `sizzle.mp3` - Cooking sound
   - `plate_clang.mp3` - Dish completion
   - `spray_bottle.mp3` - Cleaning sound
   - `sparkle.mp3` - Task completion
   - `achievement.mp3` - Event notification
   - `ambient.mp3` - Background loop

2. Place them in `static/sounds/`

Free sound resources:
- [Freesound.org](https://freesound.org)
- [Zapsplat.com](https://www.zapsplat.com)
- [Sonniss GDC Bundles](https://sonniss.com/gameaudiogdc)

## Multiplayer

The app uses WebSockets (Socket.IO) for real-time multiplayer:
- All players see each other's actions
- Events trigger for everyone simultaneously
- Activity feed shows what other players are doing
- Leaderboard updates in real-time

## Database Schema

### Tables
- `users` - Player accounts (username, password_hash, cash, level, xp, streak)
- `supplies` - Inventory tracking (user_id, supply_type, quantity)
- `orders` - Order history (user_id, menu_item, status, timestamp)
- `cleaning_tasks` - Cleaning cooldowns (user_id, task_type, location, last_cleaned)
- `events_log` - Event occurrences (user_id, event_id, timestamp, resolution)
- `achievements` - Unlocked achievements (user_id, achievement_name, unlocked_at)

### Key Features
- SQLite for simplicity and portability
- Automatic database initialization on first run via `setup.sh`
- Cooldown tracking per specific cleaning task (task_type + location)
- Supply consumption tracked individually per user

## Future Enhancements

Potential additions for v2.0:
- **Achievement system**: Unlock badges for milestones (implemented in DB, needs UI)
- **Expanded menu**: More recipes with complex supply requirements
- **Station upgrades**: Faster griddles, larger supply storage
- **Leaderboards**: Weekly/monthly rankings
- **Day/night cycles**: Time-based events and customer patterns
- **Weather events**: Impact customer spawn rates and surreal event probabilities
- **Enhanced multiplayer**: Team mode, competitive challenges
- **Mobile app**: Native iOS/Android versions
- **Voice/text chat**: Real-time communication between players
- **Seasonal events**: Holiday-themed orders and decorations

## Contributing

This is v1.0! To expand:

1. **Add more events**: Edit `surreal_events.json`
2. **New activities**: Add stations in `diner.html` and handlers in `app.py`
3. **Enhanced visuals**: Modify `static/css/style.css`
4. **New features**: Extend database models in `models.py`

## License

Open source - use, modify, and enjoy!

## Credits

Inspired by the legendary Waffle House diners of the southeastern United States - beacons in the storm, open 24/7, always there when you need them.

---

**Remember**: If the Waffle House is closed, it's time to evacuate. 🌪️

🧇 Scattered, Smothered, Covered, and Multiplayer! 🧇
