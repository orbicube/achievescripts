from pycheevos.core.helpers import *
from pycheevos.models.generic import GameObject

game_state = dword(0x00119750)
region = dword(0x10)

class Memory:

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
	difficulty = byte(0x0019483d)

	char_base = 0x00195dbc	
	vehicle_base = 0x00196d0c
	offsets = {
		"Class": 0xc,
		"Level": 0x12,
		"HP": 0x1c,
		"Character": 0xc4,
		"Subclass": 0x7d,
		"Vehicle": 0x25c,
		"SP": 0x10
	}

	map_base = tbyte(0x0019d2dc)
	map_ptr = map_base >> tbyte(0x10)

	movable = dword(0x001295c4)
	dialogue = tbyte(0x001910d4) >> dword(0xb0)

	naming_type = word(0x0019ca9c)
	naming_char = word(0x0019ca9e)
	naming_vehicle = word(0x0019caa0)

	money = dword(0x001947d8)
	pocket_money = word_be(0x0019ea2b)

	detector_count = byte(0x0019e82c)
	shell_count = byte(0x0019e82d)
	furniture_bought = tbyte_be(0x0019e833)
	winnings = tbyte_be(0x0019e82f)
	stamps = word(0x00194844)
	rental_fees = tbyte_be(0x0019e829)

	def __init__(self):
		self.region = region
		self.game_state = game_state

		self.chars = []
		#char_names = ["Player", "Axel", "Miska", "Clint", "Atena", "Sara",
		#	"Flor", "Hans", "Pablo", "Pochi", "Licky", "Hachi",
		#	"Money Eater 1", "Money Eater 2", "Money Eater 3", "NG+ Player",
		#	"Maria", "Garcia", "Fei", "Apache"]
		#char_index = 0
		for i in range(self.char_base, 0x00196c49, 196):
			self.chars.append(Character(i))

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

		self.map_vals = []
		for i in range(0, 560):
			self.map_vals.append(self.map_base >> bitcount(0x2b0 + i))

		self.inventory = {
			"Tools": [],
			"Medicine": [],
			"Battle": [],
			"Equipment": []
		}
		for i in range(0x00194a3c, 0x00194a93, 2):
			self.inventory["Battle"].append(
				{"ID": byte(i), "Amount": byte(i+1)}
			)
		for i in range(0x0019491c, 0x00194951, 2):
			self.inventory["Medicine"].append(
				{"ID": byte(i), "Amount": byte(i+1)}
			)
		for i in range(0x00194c78, 0x00194ff0, 4):
			self.inventory["Tools"].append(
				{"ID": word(i), "Amount": word(i+2)}
			)
		for i in range(0x00194ff0, 0x001955c1, 4):
			self.inventory["Equipment"].append(
				{"ID": word(i), "Amount": word(i+2)}
			)

		self.frog = Frog(tbyte(0x0012d66c))
		self.tanks = Tanks(tbyte(0x00278f30))
		self.slots = Slots(tbyte(0x0027782c))
		self.vending = Vending(tbyte(0x00129690))


class Character(GameObject):
	def __init__(self, address):
		super().__init__(address)

		self.portrait = self.offset(0xd, byte)
		self.available = self.offset(0x10, word)
		self.level = self.offset(0x12, word)
		self.hp = {
			"Current": self.offset(0x1c, word),
			"Max": self.offset(0x1e, word)
		}
		self.subclass = {
			"Index": self.offset(0x7d, byte),
			"Levels": {
				"Hunter": self.offset(0x7e, byte),
				"Mechanic": self.offset(0x7f, byte),
				"Soldier": self.offset(0x80, byte),
				"Nurse": self.offset(0x81, byte),
				"Wrestler": self.offset(0x82, byte),
				"Artist": self.offset(0x83, byte)
			}
		}


class Frog(GameObject):
	def __init__(self, address):
		super().__init__(
			address >> tbyte(0x06c) >> tbyte(0x0c) >> tbyte(0x170))

		self.state = self.offset(0x20, word)
		self.bet_cost = self.offset(0x24, dword)
		self.bet_value = self.offset(0x1e4, dword)
		self.payout = self.offset(0x16c, dword)
		self.winnings = self.offset(0x22c, dword)

	def active(self):
		return self.state > 0 and self.state < 11


class Tanks(GameObject):
	def __init__(self, address):
		super().__init__(address)

		self.in_tanks = self.offset(0x2c, dword)
		self.winnings = self.offset(0xc0, dword)
		self.combo = word(0x00278f0c)
		self.movable = dword(0x00278f20)
		self.state = dword(0x00278f28)
		self.score = dword(0x00278f5c)

	def active(self):
		return self.in_tanks == 1

class Slots(GameObject):
	def __init__(self, address):
		super().__init__(address >> tbyte(0))

		self.active_ptr = self.offset(0, tbyte)
		self.winnings = dword(0x00277828)

	def active(self):
		return self.active_ptr == 0x1aa5c4


class Vending(GameObject):
	def __init__(self, address):
		super().__init__(
			address >> tbyte(0x24) >> tbyte(0x2d0) >> tbyte(0x44))

		self.items = [self.offset(i, dword) for i in range(0x20, 0xb1, 0x30)]

		self.spin = self.offset(0x230, dword)
		self.win = self.offset(0x234, dword)

	def active(self):
		return items[0] > 0