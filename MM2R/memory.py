from pycheevos.core.helpers import *

class Memory:

	CURRENT_MAP = dword(0x00119740)
	PARTY = [
		byte(0x00194882),
		byte(0x00194883),
		byte(0x00194884),
		byte(0x00194885)
	]

	def __init__(self):
		chars = [
			{"name": "Player", "human": True},
			{"name": "Axel", "human": True},
			{"name": "Miska", "human": True}
		]