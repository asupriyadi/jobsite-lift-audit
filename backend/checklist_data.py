"""Master SIR checklist data for Fujitec REXIA / ZEXIA elevators.

Derived from the official MASTER SIR spreadsheet.
Each item declares which schedule types it applies to (1M / 3M / 12M) and how
many measurement/photo points must be captured (photo_points > 0).
"""

# photo_points: number of measurement+photo data points required for the item.
CHECKLIST_ITEMS = [
    # section, no, description, one_m, three_m, twelve_m, photo_points
    ("ELEVATOR OPERATION", 1, "Running Condition : noise, start-up shock, vibration and level accuracy floor", True, True, True, 0),
    ("ELEVATOR OPERATION", 2, "Door operation : noise, vibration, multibeam, safety edge and sill condition", True, True, True, 0),
    ("ELEVATOR OPERATION", 3, "Car fixture condition : light, fan, COB indicator, car call button and light button", True, True, True, 0),
    ("ELEVATOR OPERATION", 4, "Hall fixture condition : Hall indicator display, hall call button and hall lantern", True, True, True, 0),
    ("ELEVATOR OPERATION", 5, "Check Enhance / EC", True, True, True, 0),

    ("MOTOR ROOM", 6, "Check : Interphone MR to Car, Storage state of brake release device and function brake release", True, True, True, 0),
    ("MOTOR ROOM", 7, "Traction machine : check leakage grease, check temperature of Machine (70℃ or less) and clean", True, True, True, 0),
    ("MOTOR ROOM", 8, "Check status cable motor and encoder (wiring, connector, leaf spring) plate spring for fixing Encoder", False, False, True, 0),
    ("MOTOR ROOM", 9, "Check Greasing of motor bearing", False, False, True, 0),
    ("MOTOR ROOM", 10, "Main Sheave : check undercut (1mm or more), cracks, grease and no rope streak on the groove", False, False, True, 5),
    ("MOTOR ROOM", 11, "Check Brake : noise, vibration, powder of brake pad and without oil at the drum & disk, slip", True, True, True, 0),
    ("MOTOR ROOM", 12, "Annual overhaul / inspection brake", False, False, True, 0),
    ("MOTOR ROOM", 13, "Governor machine : noise, lubrication, no touching rope GV and parts damage", False, False, True, 0),
    ("MOTOR ROOM", 14, "Control Panel (ARD, COP, SPV, PRU, EOP): water leaking, temperature and cleaning", False, True, False, 0),
    ("MOTOR ROOM", 15, "Terminal contactor and relay do not loose connection and corrosion", False, True, False, 0),

    ("CAR", 16, "Car door hanger rail : car door hanger rail clean, check noise from rail and lubricate moving parts", False, True, False, 0),
    ("CAR", 17, "Car door V-belt drive : check tension V-belt and check cracks and damage", False, True, False, 0),
    ("CAR", 18, "Gate switch : check gap GS and car must stop if car door open", True, True, True, 0),
    ("CAR", 19, "CTL / OTL : must be turned on before 3 to 4 mm door fully closed / opened and check CTL position", True, True, True, 0),
    ("CAR", 20, "Terminal holding : check shaft and bearing roller, rust, noise, crack of roller and lubricate shaft", True, True, True, 0),
    ("CAR", 21, "Door hanger roller : check bearing rollers crack or noise", True, True, True, 0),
    ("CAR", 22, "Up thrust rollers / eccentric : Setting must be 0,2-0,4mm", False, True, False, 0),
    ("CAR", 23, "Movable cam : Dimension of Movable cam (Fully closed: 60±0.5)", False, True, False, 0),
    ("CAR", 24, "Movable cam : Clearance with landing sill and gap Movable cam and Interlock roller", False, True, False, 0),
    ("CAR", 25, "Car guide shoe/roller : check gap, check crack/damage and noise and rust roller", False, False, True, 0),
    ("CAR", 26, "Lubricator : Check leaking, oil in the box, clean lubricator and oil if leaking and check oil condition on rails", False, True, False, 0),
    ("CAR", 27, "Sheave car: noise, leaking grease, rope make into groove and lubricate grease", False, False, True, 0),

    ("HOISTWAY", 28, "Check OH sheave : abnormal noise and sheave groove", False, False, True, 0),
    ("HOISTWAY", 29, "Landing door : cleaning door rail (if necessary), check door hanger roller crack and noise", True, True, True, 0),
    ("HOISTWAY", 30, "Up thrust rollers / eccentric : Setting must be 0,2-0,4mm", True, True, True, 0),
    ("HOISTWAY", 31, "The landing door can close by itself, check end stopper rubber not loose", True, True, True, 0),
    ("HOISTWAY", 32, "Check brake slippage (Stop during inspection operation: within 200mm)", False, False, True, 0),
    ("HOISTWAY", 33, "Check lift not stop when landing door shaked by hand", True, True, True, 0),
    ("HOISTWAY", 34, "Check the lift not running when the landing door is opening (CLS off)", True, True, True, 0),
    ("HOISTWAY", 35, "Check interlock device: clearance horizontal, vertical and contact point allowance", True, True, True, 0),
    ("HOISTWAY", 36, "Check 2IR : Gaps between sensors and floor plates", False, True, False, 0),
    ("HOISTWAY", 37, "Check limit switch : installation and operation, crack, peeling and noise of roller", False, True, False, 0),
    ("HOISTWAY", 38, "Main rope : tension, rust, broken, abrasion length and diameter", False, True, False, 0),
    ("HOISTWAY", 39, "Governor rope : rust, broken and rope guide not touching with governor rope", False, True, False, 0),
    ("HOISTWAY", 40, "Counterweight : frame and weight not contact scratch, cracks and loose bolt", False, False, True, 0),
    ("HOISTWAY", 41, "Sheave counterweight : noise, leaking grease, rope make into groove and lubricate grease", False, False, True, 0),
    ("HOISTWAY", 42, "Guide shoe counterweight : When shaked counterweight and check moving smoothly", False, False, True, 0),
    ("HOISTWAY", 43, "Guide shoe counterweight : check fixation and abrasion of GIB", False, True, False, 0),
    ("HOISTWAY", 44, "Guide shoe counterweight : check crack, peeling on surface roller and noise", False, True, False, 0),

    ("PIT", 45, "Pit : leaking, cleaning and oil pan, function all switch (buffer, TPS, CSS) and Run-by", True, True, True, 1),
    ("PIT", 46, "Car sheave under car : check noise and grease and rope make into groove", False, False, True, 0),
    ("PIT", 47, "Check function overload and Load cell and check gap safety device left and right (Safety Gear)", False, False, True, 2),
    ("PIT", 48, "Tension pulley governor : cleaning pulley and distance tension pulley to floor pit", False, True, False, 3),
    ("PIT", 49, "Compensating chain : check twist and check distance with floor pit (200-300mm)", False, True, False, 5),
    ("PIT", 50, "Compensating rope : check distance sheave compensating to floor and SW to cam to bracket", False, True, False, 9),
    ("PIT", 51, "Travelling cable : twist, damage, waving, distance with floor and not nearest to parts", False, True, False, 5),
    ("PIT", 52, "Buffer: Check oil level and installation status", False, False, True, 0),

    ("OTHERS", 53, "Test Landic (ARD) and test emergency light", True, True, True, 0),
    ("OTHERS", 54, "Test seismic sensor, test fire operation and check elvic / WTB if have", False, False, True, 0),
]

SECTIONS = ["ELEVATOR OPERATION", "MOTOR ROOM", "CAR", "HOISTWAY", "PIT", "OTHERS"]


def get_checklist(schedule_type: str):
    """Return the list of checklist items applicable for a schedule type."""
    key = {"1M": 3, "3M": 4, "12M": 5}[schedule_type]
    result = []
    for row in CHECKLIST_ITEMS:
        section, no, desc, one_m, three_m, twelve_m, points = row
        applicable = row[key]
        if applicable:
            result.append({
                "no": no,
                "section": section,
                "description": desc,
                "photo_points": points,
            })
    return result
