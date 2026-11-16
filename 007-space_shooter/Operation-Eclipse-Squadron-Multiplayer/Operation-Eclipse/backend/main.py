import asyncio
import math
import random
import socket
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles


def resource_path(relative):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / relative


app = FastAPI(title="Operation Eclipse")
web_dir = resource_path("frontend")
app.mount("/assets", StaticFiles(directory=str(web_dir)), name="assets")

W, H = 900, 650
clients = {}  # player_id -> websocket
players = {}  # player_id -> authoritative player state
inputs = {}   # player_id -> input state
host_id = None
ROOM_ID = uuid.uuid4().hex[:6].upper()
room_mode = "duo"
MAX_PLAYERS = 8
MODE_CAPACITY = {"solo": 1, "duo": 2, "squadron": 8}
SHIP_LOADOUTS = {
    "VANGUARD": {"label": "Vanguard", "color": "#54eaff", "speed": 5.2, "damage": 1.0},
    "PHANTOM": {"label": "Phantom", "color": "#c18aff", "speed": 6.0, "damage": 0.9},
    "TITAN": {"label": "Titan", "color": "#ffb45f", "speed": 4.4, "damage": 1.25},
    "MEDIC": {"label": "Medic", "color": "#68ffb4", "speed": 5.0, "damage": 0.95},
}
bullets, enemies, enemy_shots, particles, pickups = [], [], [], [], []
lock = asyncio.Lock()

MISSIONS = [
    {
        "name": "BROKEN PERIMETER",
        "subtitle": "DEFEND THE OUTER COLONY",
        "location": "ORBITAL FRONTIER // SECTOR 07",
        "boss": "IRONCLAD DREADNOUGHT",
        "boss_type": "dreadnought",
        "objective": "Destroy the enemy vanguard and disable the Ironclad Dreadnought.",
        "comic": [
            {"tag": "PAGE 01 // THE LAST SIGNAL", "title": "THE FRONTIER GOES DARK",
             "text": "The Helios Colony has stopped responding. A damaged patrol beacon sends one final transmission: unidentified warships crossing the perimeter.",
             "speaker": "COMMAND: ALL PILOTS, THIS IS NOT A DRILL."},
            {"tag": "PAGE 02 // SCRAMBLE", "title": "TWO FIGHTERS. ONE CHANCE.",
             "text": "The assault fighter leads the attack. The support fighter keeps the squadron alive. Together, they launch from the carrier Asterion.",
             "speaker": "CAPTAIN: Stay close. Cover each other."},
            {"tag": "PAGE 03 // CONTACT", "title": "HOSTILE FLEET DETECTED",
             "text": "Enemy scouts are screening a heavily armored command ship. Break through the escort formation before the dreadnought reaches the colony.",
             "speaker": "TACTICAL AI: HOSTILE SIGNATURES LOCKED."}
        ],
    },
    {
        "name": "GHOSTS OF TITAN",
        "subtitle": "BREACH THE CARRIER SCREEN",
        "location": "TITAN DEBRIS FIELD // SECTOR 09",
        "boss": "WRAITH CARRIER",
        "boss_type": "carrier",
        "objective": "Survive the carrier's escort wings and destroy its launch core.",
        "comic": [
            {"tag": "PAGE 04 // AFTERMATH", "title": "A VICTORY WITH A COST",
             "text": "The Dreadnought breaks apart, but its final transmission reveals the truth: the attack is coordinated. A hidden carrier is assembling a second strike force near Titan.",
             "speaker": "COMMAND: You stopped the first wave. The war has only begun."},
            {"tag": "PAGE 05 // INTO THE WRECKAGE", "title": "THE TITAN GRAVEYARD",
             "text": "The fighters enter a maze of frozen wrecks and drifting metal. Enemy interceptors emerge from the shadows, guided by the Wraith Carrier.",
             "speaker": "SUPPORT PILOT: I have movement between the wrecks!"},
            {"tag": "PAGE 06 // THE HIVE", "title": "CARRIER INBOUND",
             "text": "The Wraith is not just a battleship. It manufactures fighters during combat. Destroy its launch systems before the screen overwhelms you.",
             "speaker": "TACTICAL AI: MULTIPLE LAUNCH SIGNATURES."}
        ],
    },
    {
        "name": "ECLIPSE PROTOCOL",
        "subtitle": "STOP THE FINAL TRANSMISSION",
        "location": "DARKSIDE ARRAY // SECTOR 00",
        "boss": "ECLIPSE CORE",
        "boss_type": "core",
        "objective": "Destroy the Eclipse Core before it activates the planetary weapon.",
        "comic": [
            {"tag": "PAGE 07 // THE REVELATION", "title": "THE SIGNAL WAS A TRAP",
             "text": "The Wraith's data reveals a hidden command network beneath the dark side of the moon. The attacks were designed to draw the colony fleet away.",
             "speaker": "COMMAND: The source is the Eclipse Array."},
            {"tag": "PAGE 08 // NO RETURN", "title": "THE FINAL APPROACH",
             "text": "The two fighters dive toward an ancient orbital weapon. Its core is charging, and the surrounding space bends with unstable energy.",
             "speaker": "ASSAULT PILOT: We're going in. Together."},
            {"tag": "PAGE 09 // OPERATION ECLIPSE", "title": "END THE WAR",
             "text": "Only a coordinated strike can break the core's shields. One pilot draws its fire while the other attacks the exposed conduits. This is the final operation.",
             "speaker": "TACTICAL AI: ECLIPSE PROTOCOL ACTIVE."}
        ],
    },
]

state = {
    "phase": "lobby",
    "mission": 1,
    "wave": 1,
    "boss": None,
    "message": "AWAITING PILOTS",
    "tick": 0,
    "mission_kills": 0,
    "mission_score": 0,
    "elapsed": 0,
}


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def mission_data():
    return MISSIONS[state["mission"] - 1]


@app.get("/")
async def index():
    return FileResponse(web_dir / "index.html")


@app.get("/qr.png")
async def qr():
    try:
        import io
        import qrcode
        url = f"http://{lan_ip()}:8000/?join=1"
        img = qrcode.make(url)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return Response(out.getvalue(), media_type="image/png")
    except Exception:
        return Response(b"", status_code=503)


@app.get("/health")
async def health():
    return {"ok": True, "players": len(clients), "mode": room_mode, "game": "Operation Eclipse", "phase": state["phase"]}


def clear_combat():
    bullets.clear()
    enemies.clear()
    enemy_shots.clear()
    particles.clear()
    pickups.clear()


def reset_players():
    count = max(1, len(players))
    for index, (pid, p) in enumerate(players.items()):
        p.update({
            "x": 90 + (index + 1) * (W - 180) / (count + 1),
            "y": 535.0, "hp": 100, "score": 0, "alive": True,
            "weapon": 1, "shield": 0, "rapid": 0,
        })
        inputs[pid] = {"x": 0, "y": 0, "fire": False, "special": False}


def begin_campaign():
    clear_combat()
    reset_players()
    state.update({
        "phase": "comic",
        "mission": 1,
        "wave": 1,
        "boss": None,
        "message": "BRIEFING INCOMING",
        "tick": 0,
        "mission_kills": 0,
        "mission_score": 0,
        "elapsed": 0,
    })


def deploy_mission():
    clear_combat()
    reset_players()
    state.update({
        "phase": "playing",
        "wave": 1,
        "boss": None,
        "message": "ENGAGE",
        "tick": 0,
        "mission_kills": 0,
        "mission_score": 0,
        "elapsed": 0,
    })


ENEMY_STATS = {
    "SCOUT":       {"hp": 2,  "speed": 2.8, "cool": (95, 150), "score": 100},
    "INTERCEPTOR": {"hp": 3,  "speed": 3.3, "cool": (70, 120), "score": 140},
    "GUNSHIP":     {"hp": 9,  "speed": 1.25,"cool": (55, 90),  "score": 220},
    "BOMBER":      {"hp": 6,  "speed": 1.55,"cool": (85, 125), "score": 190},
    "PHANTOM":     {"hp": 4,  "speed": 2.65,"cool": (65, 105), "score": 200},
    "ELITE":       {"hp": 11, "speed": 2.0, "cool": (48, 78),  "score": 320},
    "SNIPER":      {"hp": 4,  "speed": 1.65,"cool": (100, 145),"score": 210},
    "SWARMER":     {"hp": 1,  "speed": 3.8, "cool": (140, 190),"score": 80},
    "REPAIR_DRONE":{"hp": 5,  "speed": 1.35,"cool": (130, 180),"score": 240},
}


def spawn_enemy():
    mission = state["mission"]
    pools = {
        1: [("SCOUT", 24), ("INTERCEPTOR", 20), ("GUNSHIP", 14), ("BOMBER", 12), ("SNIPER", 10), ("SWARMER", 14), ("REPAIR_DRONE", 6)],
        2: [("INTERCEPTOR", 18), ("GUNSHIP", 14), ("BOMBER", 17), ("PHANTOM", 15), ("SNIPER", 10), ("SWARMER", 12), ("REPAIR_DRONE", 8), ("ELITE", 6)],
        3: [("PHANTOM", 16), ("BOMBER", 16), ("ELITE", 15), ("SNIPER", 12), ("SWARMER", 14), ("GUNSHIP", 10), ("INTERCEPTOR", 10), ("REPAIR_DRONE", 7)],
    }
    names, weights = zip(*pools[mission])
    kind = random.choices(names, weights=weights, k=1)[0]
    spec = ENEMY_STATS[kind]
    hp = spec["hp"] + max(0, mission - 1)
    enemies.append({
        "x": random.randint(65, W - 65), "y": -45,
        "hp": hp, "maxhp": hp, "kind": kind,
        "speed": random.uniform(spec["speed"] * .78, spec["speed"] * 1.12) + (mission - 1) * .2,
        "phase": random.random() * math.tau,
        "cool": random.randint(*spec["cool"]),
        "special": random.random(),
    })


def spawn_boss():
    kind = mission_data()["boss_type"]
    hp = int({"dreadnought": 330, "carrier": 390, "core": 450}[kind] * (1 + max(0, len(players) - 2) * 0.32))
    state["boss"] = {
        "type": kind, "name": mission_data()["boss"],
        "x": 450.0, "y": 110.0, "hp": hp, "maxhp": hp,
        "phase": 0, "attack": 0, "spawn_timer": 0,
    }
    state["message"] = "BOSS CONTACT"


def add_burst(x, y, color="#65eaff", count=18):
    for _ in range(count):
        a = random.random() * math.tau
        speed = random.uniform(1.0, 5.0)
        particles.append({
            "x": x, "y": y, "vx": math.cos(a) * speed,
            "vy": math.sin(a) * speed, "life": random.randint(18, 42),
            "color": color, "size": random.uniform(1.5, 4.0),
        })


def finish_mission(success):
    state["phase"] = "stage_clear" if success else "defeat"
    state["message"] = "MISSION COMPLETE" if success else "MISSION FAILED"
    state["elapsed"] = state["tick"] // 30
    state["mission_score"] = sum(p["score"] for p in players.values())


def next_mission():
    if state["mission"] >= len(MISSIONS):
        state["phase"] = "campaign_complete"
        state["message"] = "CAMPAIGN COMPLETE"
        return
    state["mission"] += 1
    state["phase"] = "comic"
    state["message"] = "NEW THREAT DETECTED"
    state["wave"] = 1
    state["boss"] = None
    state["tick"] = 0
    state["mission_kills"] = 0
    state["mission_score"] = 0


def update():
    if state["phase"] != "playing":
        return

    state["tick"] += 1
    tick = state["tick"]
    mission = state["mission"]

    # Player movement and weapon systems
    for pid, p in players.items():
        inp = inputs[pid]
        if not p["alive"]:
            continue
        if p.get("shield", 0) > 0:
            p["shield"] -= 1
        if p.get("rapid", 0) > 0:
            p["rapid"] -= 1
        ship_spec = SHIP_LOADOUTS.get(p.get("ship", "VANGUARD"), SHIP_LOADOUTS["VANGUARD"])
        p["x"] = max(28, min(W - 28, p["x"] + inp["x"] * ship_spec["speed"]))
        p["y"] = max(55, min(H - 35, p["y"] + inp["y"] * ship_spec["speed"]))
        fire_gap = max(2, 7 - (p.get("weapon", 1) - 1) - (2 if p.get("rapid", 0) > 0 else 0))
        if inp["fire"] and tick % fire_gap == 0:
            level = p.get("weapon", 1)
            bullets.append({"x": p["x"], "y": p["y"] - 22, "owner": pid, "dmg": int((2 + level - 1) * ship_spec["damage"])})
            if p.get("ship") in ("MEDIC", "VANGUARD") or level >= 2:
                bullets.append({"x": p["x"] + 13, "y": p["y"] - 13, "owner": pid, "dmg": int(level * ship_spec["damage"])})
                bullets.append({"x": p["x"] - 13, "y": p["y"] - 13, "owner": pid, "dmg": int(level * ship_spec["damage"])})
        if inp["special"] and tick % 100 == 0:
            for angle in range(0, 360, 24):
                rad = math.radians(angle)
                bullets.append({
                    "x": p["x"], "y": p["y"],
                    "vx": math.cos(rad) * 6, "vy": math.sin(rad) * 6,
                    "owner": pid, "dmg": 3,
                })

    # Enemy wave progression: three escalating waves before the boss
    if state["boss"] is None:
        if tick % 420 == 0 and state["wave"] < 3:
            state["wave"] += 1
        spawn_interval = max(34, 72 - mission * 8 - state["wave"] * 5)
        if tick % spawn_interval == 0 and len(enemies) < 7 + mission:
            spawn_enemy()
        if state["wave"] == 3 and tick > 1150 and not enemies:
            spawn_boss()

    # Player bullets
    for b in bullets[:]:
        b["x"] += b.get("vx", 0)
        b["y"] += b.get("vy", -9)
        if b["y"] < -25 or b["y"] > H + 25 or b["x"] < -25 or b["x"] > W + 25:
            bullets.remove(b)
            continue
        hit = False
        for e in enemies[:]:
            if math.hypot(b["x"] - e["x"], b["y"] - e["y"]) < (26 if e["kind"] in ("GUNSHIP", "ELITE") else 20):
                e["hp"] -= b.get("dmg", 1)
                hit = True
                if e["hp"] <= 0:
                    state["mission_kills"] += 1
                    for p in players.values():
                        p["score"] += 100
                    add_burst(e["x"], e["y"], "#ff9a61", 16)
                    if random.random() < 0.24:
                        kind = random.choices(["HEALTH", "WEAPON", "RAPID", "SHIELD"], [30, 32, 23, 15], k=1)[0]
                        pickups.append({"x": e["x"], "y": e["y"], "kind": kind, "phase": random.random() * math.tau})
                    enemies.remove(e)
                break
        if not hit and state["boss"]:
            boss = state["boss"]
            if math.hypot(b["x"] - boss["x"], b["y"] - boss["y"]) < (82 if boss["type"] != "core" else 68):
                boss["hp"] -= b.get("dmg", 1)
                hit = True
                if boss["hp"] <= 0:
                    add_burst(boss["x"], boss["y"], "#ffcf68", 100)
                    state["boss"] = None
                    for p in players.values():
                        p["score"] += 2500
                    finish_mission(True)
        if hit and b in bullets:
            bullets.remove(b)

    # Enemy movement and firing
    for e in enemies[:]:
        e["y"] += e["speed"]
        if e["kind"] in ("INTERCEPTOR", "PHANTOM"):
            e["x"] += math.sin(tick * .075 + e["phase"]) * (3.2 if e["kind"] == "PHANTOM" else 2.5)
        elif e["kind"] == "SWARMER":
            e["x"] += math.sin(tick * .12 + e["phase"]) * 4.5
        elif e["kind"] == "SNIPER":
            e["x"] += math.sin(tick * .018 + e["phase"]) * .8
        else:
            e["x"] += math.sin(tick * .035 + e["phase"]) * (1.4 + mission * .2)
        e["x"] = max(25, min(W - 25, e["x"]))
        e["cool"] -= 1
        if e["cool"] <= 0:
            alive = [p for p in players.values() if p["alive"]]
            if alive:
                target = min(alive, key=lambda p: math.hypot(p["x"] - e["x"], p["y"] - e["y"]))
                dx, dy = target["x"] - e["x"], target["y"] - e["y"]
                d = max(1, math.hypot(dx, dy))
                speed = 3.8 + mission * .3 if e["kind"] == "SNIPER" else 2.7 + mission * .35
                shot_kind = "sniper" if e["kind"] == "SNIPER" else ("bomb" if e["kind"] == "BOMBER" else "enemy")
                if e["kind"] in ("BOMBER", "GUNSHIP", "ELITE"):
                    spread = (-0.85, 0, 0.85) if e["kind"] == "BOMBER" else (-0.42, 0, 0.42)
                    for offset in spread:
                        enemy_shots.append({"x": e["x"], "y": e["y"] + 12,
                                            "vx": dx / d * speed + offset, "vy": dy / d * speed,
                                            "kind": "bomb" if e["kind"] == "BOMBER" else "heavy"})
                elif e["kind"] == "PHANTOM":
                    # Short two-shot burst with a slight lead toward the moving pilot.
                    for lead in (-0.28, 0.28):
                        enemy_shots.append({"x": e["x"], "y": e["y"] + 12,
                                            "vx": dx / d * speed + lead, "vy": dy / d * speed,
                                            "kind": "phantom"})
                else:
                    enemy_shots.append({"x": e["x"], "y": e["y"] + 12,
                                        "vx": dx / d * speed, "vy": dy / d * speed,
                                        "kind": shot_kind})
            e["cool"] = random.randint(*ENEMY_STATS[e["kind"]]["cool"])
        if e["kind"] == "REPAIR_DRONE" and tick % 95 == 0:
            for ally in enemies:
                if ally is not e and math.hypot(ally["x"] - e["x"], ally["y"] - e["y"]) < 115:
                    ally["hp"] = min(ally["maxhp"], ally["hp"] + 1)
                    add_burst(ally["x"], ally["y"], "#63ffb5", 3)
                    break
        if e["y"] > H + 35:
            enemies.remove(e)

    # Boss-specific attack patterns
    boss = state["boss"]
    if boss:
        boss["phase"] += 1
        boss["x"] = 450 + math.sin(tick * .012) * (190 if boss["type"] == "dreadnought" else 240)
        boss["attack"] += 1
        if boss["type"] == "dreadnought":
            if boss["attack"] % 48 == 0:
                for dx in (-2.4, -1.2, 0, 1.2, 2.4):
                    enemy_shots.append({"x": boss["x"], "y": boss["y"] + 45, "vx": dx, "vy": 3.8, "kind": "heavy"})
        elif boss["type"] == "carrier":
            if boss["attack"] % 105 == 0 and len(enemies) < 9:
                for offset in (-65, 0, 65):
                    enemies.append({"x": boss["x"] + offset, "y": boss["y"] + 40,
                                    "hp": 3, "maxhp": 3, "kind": "INTERCEPTOR",
                                    "speed": 2.0, "phase": random.random() * math.tau, "cool": 60})
            if boss["attack"] % 70 == 0:
                for dx in (-3, -1.5, 0, 1.5, 3):
                    enemy_shots.append({"x": boss["x"], "y": boss["y"] + 40, "vx": dx, "vy": 3.4, "kind": "carrier"})
        else:  # Eclipse Core: rotating radial pulse
            if boss["attack"] % 82 == 0:
                for angle in range(0, 360, 22):
                    rad = math.radians(angle + boss["phase"] * .7)
                    enemy_shots.append({"x": boss["x"], "y": boss["y"] + 10,
                                        "vx": math.cos(rad) * 3.1, "vy": math.sin(rad) * 3.1,
                                        "kind": "core"})
            if boss["attack"] % 155 == 0:
                for dx in (-2.5, 0, 2.5):
                    enemy_shots.append({"x": boss["x"], "y": boss["y"] + 45, "vx": dx, "vy": 4.8, "kind": "core"})

    # Hostile projectiles and player damage
    for shot in enemy_shots[:]:
        shot["x"] += shot["vx"]
        shot["y"] += shot["vy"]
        if shot["y"] > H + 30 or shot["x"] < -30 or shot["x"] > W + 30 or shot["y"] < -30:
            enemy_shots.remove(shot)
            continue
        for p in players.values():
            if p["alive"] and math.hypot(shot["x"] - p["x"], shot["y"] - p["y"]) < 18:
                if p.get("shield", 0) > 0:
                    p["shield"] -= 1
                else:
                    damage = 14 if shot.get("kind") == "sniper" else (10 if shot.get("kind") in ("core", "bomb", "heavy") else (8 if shot.get("kind") == "phantom" else 6))
                    p["hp"] = max(0, p["hp"] - damage)
                add_burst(shot["x"], shot["y"], "#ff5577", 5)
                if p["hp"] <= 0:
                    p["alive"] = False
                if shot in enemy_shots:
                    enemy_shots.remove(shot)
                break

    # Collect drifting supply capsules; effects are applied by the authoritative server.
    for item in pickups[:]:
        item["y"] += 1.65
        item["phase"] += .08
        collected = False
        for p in players.values():
            if p["alive"] and math.hypot(item["x"] - p["x"], item["y"] - p["y"]) < 27:
                kind = item["kind"]
                if kind == "HEALTH":
                    p["hp"] = min(100, p["hp"] + 32)
                elif kind == "WEAPON":
                    p["weapon"] = min(4, p.get("weapon", 1) + 1)
                elif kind == "RAPID":
                    p["rapid"] = max(p.get("rapid", 0), 420)
                    p["shield"] = max(p.get("shield", 0), 90)
                elif kind == "SHIELD":
                    p["shield"] = max(p.get("shield", 0), 240)
                p["score"] += 75
                add_burst(item["x"], item["y"], "#6bffe0", 14)
                collected = True
                break
        if collected or item["y"] > H + 20:
            pickups.remove(item)

    # Particle effects
    for particle in particles[:]:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["vx"] *= .985
        particle["vy"] *= .985
        particle["life"] -= 1
        if particle["life"] <= 0:
            particles.remove(particle)

    if not any(p["alive"] for p in players.values()):
        finish_mission(False)


async def broadcaster():
    while True:
        async with lock:
            update()
            md = mission_data()
            snapshot = {
                "type": "state",
                "players": players,
                "room": {"id": ROOM_ID, "mode": room_mode, "host_id": host_id, "max_players": MODE_CAPACITY[room_mode], "min_players": 1 if room_mode == "solo" else 2, "ship_loadouts": SHIP_LOADOUTS},
                "bullets": bullets,
                "enemies": enemies,
                "enemy_shots": enemy_shots,
                "particles": particles,
                "pickups": pickups,
                "game": state,
                "mission_info": {
                    "name": md["name"], "subtitle": md["subtitle"],
                    "location": md["location"], "boss": md["boss"],
                    "objective": md["objective"], "comic": md["comic"],
                    "boss_type": md["boss_type"],
                    "total_missions": len(MISSIONS),
                },
                "connected": list(clients.keys()),
            }
            targets = list(clients.items())
        for _, ws in targets:
            try:
                await ws.send_json(snapshot)
            except Exception:
                pass
        await asyncio.sleep(1 / 30)


@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcaster())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global host_id, room_mode
    await ws.accept()
    pid = uuid.uuid4().hex[:10]
    async with lock:
        if len(clients) >= MODE_CAPACITY[room_mode]:
            await ws.send_json({"type": "error", "message": "Room is full (8 pilots maximum)."})
            await ws.close(code=1008)
            return
        if state["phase"] != "lobby":
            await ws.send_json({"type": "error", "message": "A mission is already in progress. Join the next lobby."})
            await ws.close(code=1008)
            return
        if host_id is None:
            host_id = pid
        index = len(players)
        ship = list(SHIP_LOADOUTS)[index % len(SHIP_LOADOUTS)]
        players[pid] = {
            "id": pid, "name": f"PILOT {index + 1}", "ship": ship,
            "color": SHIP_LOADOUTS[ship]["color"],
            "x": 90 + (index + 1) * (W - 180) / (index + 2), "y": 535.0,
            "hp": 100, "score": 0, "alive": True, "role": ship,
            "weapon": 1, "shield": 0, "rapid": 0,
        }
        inputs[pid] = {"x": 0, "y": 0, "fire": False, "special": False}
        clients[pid] = ws
    try:
        await ws.send_json({"type": "welcome", "player_id": pid, "is_host": pid == host_id, "ship_loadouts": SHIP_LOADOUTS})
        while True:
            data = await ws.receive_json()
            async with lock:
                action = data.get("type")
                if action == "profile":
                    p = players.get(pid)
                    if p and state["phase"] == "lobby":
                        ship = data.get("ship", p["ship"]).upper()
                        if ship not in SHIP_LOADOUTS:
                            ship = p["ship"]
                        p["ship"] = ship
                        p["role"] = ship
                        p["color"] = SHIP_LOADOUTS[ship]["color"]
                        p["name"] = str(data.get("name", p["name"]))[:16].strip() or p["name"]
                elif action == "mode" and pid == host_id and state["phase"] == "lobby":
                    requested = data.get("mode")
                    if requested in ("solo", "duo", "squadron") and len(players) <= MODE_CAPACITY[requested]:
                        room_mode = requested
                elif action == "input":
                    inputs[pid] = {
                        "x": max(-1, min(1, float(data.get("x", 0)))),
                        "y": max(-1, min(1, float(data.get("y", 0)))),
                        "fire": bool(data.get("fire")),
                        "special": bool(data.get("special")),
                    }
                elif action == "start" and pid == host_id and state["phase"] == "lobby":
                    minimum = 1 if room_mode == "solo" else 2
                    if len(players) >= minimum:
                        begin_campaign()
                elif action == "deploy" and pid == host_id and state["phase"] == "comic":
                    deploy_mission()
                elif action == "retry" and pid == host_id and state["phase"] == "defeat":
                    deploy_mission()
                elif action == "next" and pid == host_id and state["phase"] == "stage_clear":
                    next_mission()
                elif action == "replay" and pid == host_id and state["phase"] == "campaign_complete":
                    begin_campaign()
                elif action == "back_lobby" and pid == host_id and state["phase"] in ("defeat", "stage_clear", "campaign_complete"):
                    clear_combat()
                    state.update({"phase": "lobby", "mission": 1, "wave": 1, "boss": None,
                                  "message": "AWAITING PILOTS", "tick": 0})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        async with lock:
            clients.pop(pid, None)
            players.pop(pid, None)
            inputs.pop(pid, None)
            if host_id == pid:
                host_id = next(iter(clients), None)
            if state["phase"] == "playing" and not players:
                finish_mission(False)


if __name__ == "__main__":
    import threading
    import time
    import webbrowser
    import uvicorn
    print("\nOPERATION ECLIPSE // HOST ONLINE")
    print(f"Host: http://127.0.0.1:8000/?host=1")
    print(f"Join: http://{lan_ip()}:8000/?join=1")
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8000/?host=1")).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
