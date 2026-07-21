from pycheevos.core.helpers import *
from pycheevos.models.generic import GameObject

class Memory:

	game_state = dword(0x00119750)
	current_map = dword(0x00119740)
	party = [
		byte(0x00194882),
		byte(0x00194883),
		byte(0x00194884),
		byte(0x00194885)
	]
	party_vehicles = [
		byte(0x00194878),
		byte(0x00194879),
		byte(0x0019487a),
		byte(0x0019487b)
	]
	kills = dword(0x001949e8)

	ngplus_count = byte(0x001aa3e4)

	char_base = 0x00195dbc	
	vehicle_base = 0x00196d0c
	offsets = {
		"Class": 0xc,
		"Level": 0x12,
		"HP": 0x1c,
		"Character": 0xc4,
		"Subclass": 0x7d,
		"Vehicle": 0x25c,
		"SP": 0x10,
		"Vending Spin": 0x140,
		"Vending Win": 0x144
	}

	naming_type = word(0x0019ca9c)
	naming_char = word(0x0019ca9e)
	naming_vehicle = word(0x0019caa0)

	pocket_money = byte(0x0019ea2b)

	vending_base = tbyte(0x00129690) >> tbyte(0x24) >> tbyte(0x2d0) >> tbyte(0x44)
	vending_spin = vending_base >> word(0x230)
	vending_win = vending_base >> tbyte(0x234)

	frog_base = tbyte(0x0012d66c) >> tbyte(0x06c) >> tbyte(0x0c) >> tbyte(0x170)
	frog_state = frog_base >> tbyte(0x20)
	frog_bet = frog_base >> tbyte(0x24)
	frog_payout = frog_base >> tbyte(0x16c)

	def __init__(self):
		self.chars = {}
		char_names = ["Player", "Axel", "Miska", "Clint", "Atena", "Sara",
			"Flor", "Hans", "Pablo", "Pochi", "Licky", "Hachi",
			"Money Eater 1", "Money Eater 2", "Money Eater 3", "NG+ Player",
			"Maria", "Garcia", "Fei", "Apache"]
		char_index = 0

		for i in range(self.char_base, 0x00196c49, 196):
			char_dict = {}

			char_dict["Available"] = word(i + 0x10)
			char_dict["Level"] = word(i + 0x12)
			char_dict["HP"] = {
				"Current": word(i + 0x1c),
				"Max": word(i + 0x1e)
			}
			char_dict["Subclass"] = {
				"Index": byte(i + 0x7d),
				"Levels": {
					"Hunter": byte(i + 0x7e),
					"Mechanic": byte(i + 0x7f),
					"Soldier": byte(i + 0x80),
					"Nurse": byte(i + 0x81),
					"Wrestler": byte(i + 0x82),
					"Artist": byte(i + 0x83)
				}
			}

			self.chars[char_names[char_index]] = char_dict
			char_index += 1

		self.inventory = {"Tools": [], "Equipment": []}
		for i in range(0x00194c78, 0x00194ff0, 4):
			self.inventory["Tools"].append((word(i), word(i+2)))

		self.enemies = []
		for i in range(0x001ab5cc, 0x001abc69, 188):
			enemy = {
				"Status": [byte(i+0x9), byte(i+0xa)],
				"ID": word(i+0x44),
				"HP": dword(i+0x4c)
			}
			self.enemies.append(enemy)

		self.combat_vehicles = []
		for i in range(0x001ab398, 0x001ab511, 188):
			vehicle = {
				"HP": dword(i+0x4c),
				"Max HP": dword(i+0x50)
			}
			self.combat_vehicles.append(vehicle)

		self.bounties = {}
		bounty_names = ["Sand Shark", "Desperoid", "Thousand Radiata",
			"Adam Ant", "Rhinogon", "Myth Ladybug", "Skunks", "Flying Fish",
			"U-Shark", "Madam Muscle", "Vile Vendor", "Kamikaze King",
			"Cagliostro", "Dust Hominid", "Total Turtle", "Sea Mon-Star",
			"Groween", "Bullfrog", "Nadir Ghost", "Mimic Stairs",
			"Pichi Pichi Bros", "Daedalus", "Sandy Dandy", "Battleshipsaurus",
			"Hovering Dog", "Ted Broiler", "U-U-Shark", "EX-Daedalus",
			"Mothershipsaurus", "Ragna-rok"]
		bounty_county = 0
		for i in range(0x0019e8bb, 0x0019e8d9, 1):
			self.bounties[bounty_names[bounty_county]] = bit3(i)

			bounty_county += 1