"""
Lakshya, Bhujanga Kotian
DS02
S10273110D
"""

from random import randint
import pickle

# ---------------- CONFIG / CONSTANTS ----------------
MAP_FILENAME = r"C:\Users\laksh\Downloads\level1.txt"
SAVE_FILENAME = "save_game.pkl"
SCORES_FILENAME = "scores.txt"

TURNS_PER_DAY = 20
GOAL_GP = 500

# ore metadata
ORE_ORDER = ["copper", "silver", "gold"]   # index => level
ORE_SYMBOL_TO_NAME = {"C": "copper", "S": "silver", "G": "gold"}
ORE_SELL_RANGE = {"copper": (1, 3), "silver": (5, 8), "gold": (10, 18)}

# pickaxe upgrade costs: idx 0: L1->L2 cost, idx1: L2->L3 cost
PICKAXE_UPGRADE_COSTS = [50, 150]

# ---------------- GAME STATE ----------------
state = {
    "player": {},        # dictionary for player attributes
    "map": [],           # 2D list of map chars
    "fog": [],           # 2D list of fog chars ('?' or revealed char)
    "map_w": 0,
    "map_h": 0
}


# ---------------- MAP LOADING & FOG ----------------
def load_map(filepath):
    """Load level file into state['map'] and initialize dimensions."""
    m = state["map"]
    m.clear()
    try:
        with open(filepath, "r") as f:
            for line in f:
                m.append(list(line.rstrip("\n")))
    except FileNotFoundError:
        print(f"Map file '{filepath}' not found. Make sure it is in the same folder.")
        raise

    # pad rows to same width
    maxw = max(len(row) for row in m)
    for row in m:
        while len(row) < maxw:
            row.append(" ")

    state["map_w"] = maxw
    state["map_h"] = len(m)


def init_fog():
    """Create fog layer (all '?') matching map dimensions."""
    fw = state["map_w"]
    fh = state["map_h"]
    state["fog"] = [["?"] * fw for _ in range(fh)]


def reveal_around_player():
    """Clear fog in 3x3 area centered on player."""
    px = state["player"]["x"]
    py = state["player"]["y"]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = px + dx, py + dy
            if 0 <= nx < state["map_w"] and 0 <= ny < state["map_h"]:
                state["fog"][ny][nx] = state["map"][ny][nx]


# ---------------- PLAYER UTILITIES ----------------
def total_load():
    p = state["player"]
    return p["copper"] + p["silver"] + p["gold"]


# ---------------- GAME INITIALISATION ----------------
def start_new_game():
    load_map(MAP_FILENAME)
    init_fog()

    name = input("Greetings, miner! What is your name? ").strip()
    while not name:
        print("Name cannot be empty.")
        name = input("Please enter your name: ").strip()

    # initialize player
    player = {
        "name": name,
        "x": 0,
        "y": 0,
        "copper": 0,
        "silver": 0,
        "gold": 0,
        "GP": 0,
        "day": 1,
        "steps": 0,
        "capacity": 10,
        "pickaxe": 1,   # 1=copper, 2=silver, 3=gold
        "portal": None,
        "turns": TURNS_PER_DAY
    }
    state["player"] = player

    # find Town 'T' starting location (if present)
    for y, row in enumerate(state["map"]):
        for x, tile in enumerate(row):
            if tile == "T":
                player["x"], player["y"] = x, y
                break

    print(f"Pleased to meet you, {player['name']}. Welcome to Sundrop Town!")
    reveal_around_player()


# ---------------- DISPLAY ----------------
def draw_map():
    """Print the full map with fog applied. Miner shown as 'M' and portal 'P'."""
    w = state["map_w"]
    h = state["map_h"]
    p = state["player"]
    print("+" + "-" * w + "+")
    for y in range(h):
        print("|", end="")
        for x in range(w):
            if (x, y) == (p["x"], p["y"]):
                print("M", end="")
            elif p["portal"] == (x, y):
                print("P", end="")
            else:
                print(state["fog"][y][x], end="")
        print("|")
    print("+" + "-" * w + "+")


def draw_viewport():
    """Print the 3x3 viewport centered on the player (walls '#' outside map)."""
    p = state["player"]
    w = state["map_w"]
    h = state["map_h"]
    print("+---+")
    for dy in (-1, 0, 1):
        row = "|"
        for dx in (-1, 0, 1):
            nx, ny = p["x"] + dx, p["y"] + dy
            if (nx, ny) == (p["x"], p["y"]):
                row += "M"
            elif 0 <= nx < w and 0 <= ny < h:
                if state["fog"][ny][nx] != "?":
                    row += "P" if p["portal"] == (nx, ny) else state["map"][ny][nx]
                else:
                    row += "?"
            else:
                row += "#"
        row += "|"
        print(row)
    print("+---+")


def show_player_information():
    p = state["player"]
    # CHANGED: show actual portal (default to (0,0) if None)
    px, py = p["portal"] if p["portal"] is not None else (0, 0)
    print("----- Player Information -----")
    print(f"Name: {p['name']}")
    print(f"Portal position: ({px}, {py})")
    if p['pickaxe'] == 1:
        mineral_name = "copper"
    elif p['pickaxe'] == 2:
        mineral_name = "silver"
    else:
        mineral_name = "gold"
    print(f"Pickaxe level: {p['pickaxe']} ({mineral_name})")
    print(f"Gold: {p['gold']}")
    print(f"Silver: {p['silver']}")
    print(f"Copper: {p['copper']}")
    print("------------------------------")
    print(f"Load: {total_load()} / {p['capacity']}")
    print("------------------------------")
    print(f"GP: {p['GP']}")
    print(f"Steps taken: {p['steps']}")
    print("------------------------------")
    print(f"DAY {p['day']}")


# ---------------- MINING & MOVEMENT ----------------
def sell_ore_all():
    """Sell all ore in inventory with random per-unit prices and add to GP."""
    p = state["player"]
    total = 0
    sold_any = False
    for ore in ORE_ORDER:
        qty = p[ore]
        if qty > 0:
            lo, hi = ORE_SELL_RANGE[ore]
            unit_price = randint(lo, hi)
            gp = qty * unit_price
            print(f"You sell {qty} {ore} ore for {gp} GP.")
            p[ore] = 0
            total += gp
            sold_any = True
    if sold_any:
        p["GP"] += total
        print(f"You now have {p['GP']} GP!")
    else:
        print("You have no ore to sell.")
    return total


def place_portal_and_return():
    """Use portal: place at current spot, sell ore, advance day and reset turns."""
    p = state["player"]
    print("You place your portal stone here and zap back to town.")
    p["portal"] = (p["x"], p["y"])
    sell_ore_all()
    check_win_condition()
    p["day"] += 1
    p["turns"] = TURNS_PER_DAY
    reveal_around_player()


def step(direction):
    """Handle WASD step. Deduct a turn even when move is blocked."""
    p = state["player"]
    dx = dy = 0
    if direction == "w":
        dy = -1
    elif direction == "s":
        dy = 1
    elif direction == "a":
        dx = -1
    elif direction == "d":
        dx = 1
    else:
        print("Invalid direction.")
        return

    nx = p["x"] + dx
    ny = p["y"] + dy

    # boundary check
    if not (0 <= nx < state["map_w"] and 0 <= ny < state["map_h"]):
        print("You can't go that way.")
        p["turns"] -= 1
        return

    tile = state["map"][ny][nx]

    # CHANGED: stepping on Town 'T' returns to town WITHOUT resetting portal
    if tile == "T":
        p["x"], p["y"] = nx, ny
        print("You return to town.")
        sell_ore_all()
        check_win_condition()
        p["day"] += 1
        p["turns"] = TURNS_PER_DAY
        reveal_around_player()
        return

    # if tile is a mineral node
    ore = ORE_SYMBOL_TO_NAME.get(tile)
    if ore:
        # can your pickaxe mine it?
        required_level = ORE_ORDER.index(ore) + 1
        if required_level > p["pickaxe"]:
            print(f"Your pickaxe can't mine {ore} yet.")
            p["turns"] -= 1
            return

        # check capacity
        if total_load() >= p["capacity"]:
            print("You can't carry any more, so you can't go that way.")
            p["turns"] -= 1
            return

        # mine amount depending on ore type
        if ore == "copper":
            mined = randint(1, 5)
        elif ore == "silver":
            mined = randint(1, 3)
        else:  # gold
            mined = randint(1, 2)

        space_left = p["capacity"] - total_load()
        mined_actual = min(mined, space_left)
        p[ore] += mined_actual
        print(f"You mined {mined_actual} piece(s) of {ore}.")
        # remove node from map after mining
        state["map"][ny][nx] = " "

    # move player into the tile (even if it's floor or mined)
    p["x"], p["y"] = nx, ny
    p["steps"] += 1
    p["turns"] -= 1
    reveal_around_player()

    # if out of turns, auto-portal
    if p["turns"] <= 0:
        print("You are exhausted.")
        place_portal_and_return()


# ---------------- MINE / TOWN LOOPS ----------------
def enter_mine_loop():
    p = state["player"]
    # if portal exists, start at portal; otherwise start at town (assumed T coords)
    if p["portal"] is not None:
        p["x"], p["y"] = p["portal"]
    # ensure fog around player is revealed
    reveal_around_player()

    while p["turns"] > 0:
        draw_viewport()
        print(f"Turns left: {p['turns']} Load: {total_load()} / {p['capacity']} Steps: {p['steps']}")
        print("(WASD) to move")
        print("(M)ap, (I)nformation, (P)ortal, (Q)uit to main menu")
        action = input("Action? ").strip().lower()
        if action in ("w", "a", "s", "d"):
            step(action)
        elif action == "m":
            draw_map()
        elif action == "i":
            show_player_information()
        elif action == "p":
            place_portal_and_return()
            break
        elif action == "q":
            print("You leave the mine.")
            return "main menu"
        else:
            print("Invalid input.")

    # if we exit loop due to turns reaching 0 the portal is already used inside step()
    return


def shop_menu():
    p = state["player"]
    while True:
        print()
        if p["pickaxe"] == 1:
            print("(P)ickaxe upgrade to Level 2 to mine silver ore for 50 GP")
        elif p["pickaxe"] == 2:
            print("(P)ickaxe upgrade to Level 3 to mine gold ore for 150 GP")
        else:
            print("You already have the best pickaxe.")
        bag_cost = p["capacity"] * 2
        print(f"(B)ackpack upgrade to carry {p['capacity'] + 2} items for {bag_cost} GP")
        print("(L)eave shop")
        print("-----------------------------------------------------------")
        print(f"GP: {p['GP']}")
        print("-----------------------------------------------------------")
        choice = input("Your choice? ").strip().lower()
        if choice == "p":
            if p["pickaxe"] < 3:
                cost = PICKAXE_UPGRADE_COSTS[p["pickaxe"] - 1]
                if p["GP"] >= cost:
                    p["GP"] -= cost
                    p["pickaxe"] += 1
                    print(f"Congratulations! You can now mine {ORE_ORDER[p['pickaxe']-1]}!")
                else:
                    print("Not enough GP.")
            else:
                print("You already have the best pickaxe.")
        elif choice == "b":
            if p["GP"] >= bag_cost:
                p["GP"] -= bag_cost
                p["capacity"] += 2
                print(f"Congratulations! You can now carry {p['capacity']} items!")
            else:
                print("Not enough GP.")
        elif choice == "l":
            break
        else:
            print("Invalid input.")


def town_loop():
    while True:
        p = state["player"]
        print(f"\nDAY {p['day']}")
        print("----- Sundrop Town -----")
        print("(B)uy stuff")
        print("See Player (I)nformation")
        print("See Mine (M)ap")
        print("(E)nter mine")
        print("Sa(V)e game")
        print("(Q)uit to main menu")
        print("------------------------")
        choice = input("Your choice? ").strip().lower()
        if choice == "b":
            shop_menu()
        elif choice == "i":
            show_player_information()
        elif choice == "m":
            draw_map()
        elif choice == "e":
            enter_mine_loop()
        elif choice == "v":
            save_game_pickle()
        elif choice == "q":
            break
        else:
            print("Invalid input.")


# ---------------- SAVE / LOAD (pickle) & SCORES ----------------
def save_game_pickle():
    try:
        with open(SAVE_FILENAME, "wb") as f:
            pickle.dump({"map": state["map"], "fog": state["fog"], "player": state["player"]}, f)
        print("Game saved.")
    except Exception as e:
        print("Error saving game:", e)


def load_game_pickle():
    try:
        with open(SAVE_FILENAME, "rb") as f:
            data = pickle.load(f)
        state["map"] = data["map"]
        state["fog"] = data["fog"]
        state["player"] = data["player"]
        # update dims
        state["map_w"] = len(state["map"][0])
        state["map_h"] = len(state["map"])
        reveal_around_player()
        print("Game loaded.")
        return True
    except FileNotFoundError:
        print("No saved game found.")
        return False
    except Exception as e:
        print("Error loading game:", e)
        return False


def record_score():
    p = state["player"]
    try:
        with open(SCORES_FILENAME, "a") as f:
            f.write(f"{p['name']},{p['day']},{p['steps']},{p['GP']}\n")
    except Exception:
        pass


def show_top_scores():
    try:
        with open(SCORES_FILENAME, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        scores = []
        for line in lines:
            name, days, steps, gp = line.split(",")
            scores.append((name, int(days), int(steps), int(gp)))
        # sort: fewer days -> fewer steps -> more GP
        scores.sort(key=lambda x: (x[1], x[2], -x[3]))
        print("\nTop 5 Scores")
        for idx, (name, days, steps, gp) in enumerate(scores[:5], start=1):
            print(f"{idx}. {name} - Days: {days} Steps: {steps} GP: {gp}")
    except FileNotFoundError:
        print("No scores yet.")
    except Exception:
        print("Could not read scores.")


# ---------------- WIN CHECK ----------------
def check_win_condition():
    p = state["player"]
    if p["GP"] >= GOAL_GP:
        print(f"Woo-hoo! Well done, {p['name']}, you have {p['GP']} GP!")
        print("You now have enough to retire and play video games every day.")
        print(f"And it only took you {p['day']} days and {p['steps']} steps! You win!")
        record_score()
        # after winning, go back to main menu by raising SystemExit or returning
        raise SystemExit


# ---------------- MAIN MENU / ENTRY ----------------
def main_menu():
    print("---------------- Welcome to Sundrop Caves! ----------------")
    print("You spent all your money to get the deed to a mine, a small")
    print(" backpack, a simple pickaxe and a magical portal stone.")
    print()
    print("How quickly can you get the 500 GP you need to retire")
    print(" and live happily ever after?")
    print("-----------------------------------------------------------")

    while True:
        print("\n--- Main Menu ----")
        print("(N)ew game")
        print("(L)oad saved game")
        print("(V)iew Top Scores")
        print("(Q)uit")
        print("------------------")
        choice = input("Your choice? ").strip().lower()
        if choice == "n":
            start_new_game()
            try:
                town_loop()
            except SystemExit:
                # when player wins, SystemExit thrown; return to main menu
                pass
        elif choice == "l":
            if load_game_pickle():
                try:
                    town_loop()
                except SystemExit:
                    pass
        elif choice == "v":
            show_top_scores()
        elif choice == "q":
            print("Goodbye!")
            break
        else:
            print("Invalid input.")


# ---------------- START ----------------
if __name__ == "__main__":
    main_menu()
