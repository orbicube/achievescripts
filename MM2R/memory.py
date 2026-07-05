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

	pocket_money = byte(0x0019ea2b)


	def __init__(self):
		self.chars = [
			{"name": "Player", "human": True},
			{"name": "Axel", "human": True},
			{"name": "Miska", "human": True}
		]

		self.inventory = {"tools": []}
		for i in range(0x00194c78, 0x00194ff0, 4):
			self.inventory["tools"].append((word(i), word(i+2)))

		self.enemies = []
		for i in range(0x001ab610, 0x001abcad, 188):
			enemy = {
				"id": word(i),
				"hp": dword(i+8)
			}
			self.enemies.append(enemy)