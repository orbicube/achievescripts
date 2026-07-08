from pycheevos.core.helpers import *

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
	offsets = {
		"Class": 0xc,
		"Level": 0x12,
		"Character": 0xc4,
		"Subclass": 0x7d
	}

	pocket_money = byte(0x0019ea2b)

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
		for i in range(0x001ab610, 0x001abcad, 188):
			enemy = {
				"ID": word(i),
				"HP": dword(i+8)
			}
			self.enemies.append(enemy)


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