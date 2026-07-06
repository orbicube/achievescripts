from pycheevos.core.helpers import *
from pycheevos.core.constants import *
from pycheevos.models.achievement import Achievement
from pycheevos.models.set import AchievementSet

from enum import Enum
import collections

ach_set = AchievementSet(game_id = 24022, title = "Metal Max 2: Reloaded")

from memory import Memory
mem = Memory()

import json
#	Converts a simple non-pointer code note into a dict with descriptions as keys
#	Notes should be formatted as Description\r\n\0xAddress1 = Key1\r\n0xAddress2 = Key2
#	If duplicate keys, addresses will be in a List
def note2dict(notefile: str, addr: str):
	with open(notefile) as data_file:
	    json_data = data_file.read()
	notes = json.loads(json_data)

	note = [note["Note"] for note in notes if note["Address"] == addr]
	note = note[0]

	# Remove header line
	note = note.split("\r\n", 1)[1]

	note_dict = {}
	for line in note.split("\r\n"):
		val, key_str = line.split(" = ")
		val = int(val, 16)

		if key_str in note_dict:
			if type(note_dict[key_str]) != List:
				note_dict[key_str] = [note_dict[key_str], val]
			else:
				note_dict[key_str].append(val)
		else:
			note_dict[key_str] = val

	return note_dict
maps = note2dict("D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data\\24022-Notes.json", "0x119740")

class Operator(Enum):
	EQUAL = 0
	LESS_THAN = 1
	LESS_THAN_EQ = 2
	GREATER_THAN = 3
	GREATER_THAN_EQ = 4
	NOT_EQUAL = 5

class Measured(Enum):
	NOT_MEASURED = 0
	MEASURED = 1
	MEASURED_PCT = 2

def partial_bitcount(
	addr: int, bits: collections.abc.Iterable[int], is_delta: bool = False, 
	count: int = None, operator: Operator = Operator.EQUAL,
	measured: Measured = Measured.NOT_MEASURED):

	logic = []
	for bit in bits:
		match bit:
			case 7:
				bit_obj = bit7(addr)
			case 6:
				bit_obj = bit6(addr)
			case 5:
				bit_obj = bit5(addr)
			case 4:
				bit_obj = bit4(addr)
			case 3:
				bit_obj = bit3(addr)
			case 2:
				bit_obj = bit2(addr)
			case 1:
				bit_obj = bit1(addr)
			case 0:
				bit_obj = bit0(addr)

		if is_delta:
			bit_obj = delta(bit_obj)

		logic.append((add_source(bit_obj)))

	if count:
		match operator:
			case Operator.EQUAL:
				bit_logic = (bit_obj == count)
			case Operator.LESS_THAN:
				bit_logic = (bit_obj < count)
			case Operator.LESS_THAN_EQ:
				bit_logic = (bit_obj <= count)
			case Operator.GREATER_THAN:
				bit_logic = (bit_obj > count)
			case Operator.GREATER_THAN_EQ:
				bit_logic = (bit_obj >= count)
			case Operator.NOT_EQUAL:
				bit_logic = (bit_obj != count)

		if measured:
			match measured:
				case Measured.MEASURED:
					bit_logic = measured(bit_logic)
				case Measured.MEASURED_PCT:
					bit_logic = measured_percent(bit_logic)

		logic[-1] = bit_logic

	return logic


def bitcount_range(start_addr: int, start_bit: int, end_addr: int, end_bit: int, goal: int = 0):
	return "foo"


# Quests/Flag-based Achievements
ach_flags = [ # ID, Badge, Title, Description, Points, Type, Flag Address, Map ID, Extra Flags
	(0, 0, "!!Start Mado Rebuild", "Clear away the rubble of Mado's destroyed buildings, paving the way for new structures",
		1, None, bit0(0x0019e91a), maps["Mado"], None),
	(0, 0, "!!Nile's Car", "Receive a repaired vehicle from Nile at the Mado Garage",
		2, None, bit2(0x0019e91a), maps["Mado Garage"], None),
	(0, 0, "!!Khatia Quest", "Rescue Khatia from the Grapplers running the El Niño Inn",
		3, None, bit1(0x0019e952), maps["El Nino Inn"], None),
	(0, 0, "Neither Toothless nor Gutless", "Become a member of the Mindless, gaining access to party member recruitment",
		3, None, bit7(0x0019e952), maps["El Nino Mindless Hideout"], None),
	(0, 0, "!!Schriette Quest", "Give Schriette in the Mindless hideout 25 Electronic Parts",
		3, None, bit4(0x0019e957), maps["El Nino Mindless Hideout"], None),
	(0, 0, "!!Anne Ring Quest", "Find and return Anne's Ring to Irish in the camp east of Mado",
		2, None, bit1(0x0019e924), maps["Trader Camp (Harley Ring)"], None),
	(0, 0, "!!Harley", "Purchase the vehicle being offered for sale at the trader camp east of Mado",
		2, None, bit7(0x0019e9fa), maps["Trader Camp (Harley Ring)"], None),
	(0, 0, "!!Curry Powder", "Fulfil Irit's culinary curiosity by giving her a Cookbook and Curry Powder",
		2, None, bit3(0x0019e93a), maps["Mado Garage"], None),
	(0, 0, "!!Antares", "Hunt Antares for a Hunter in a bar east of Mado, receiving the keys to a vehicle as your reward",
		4, None, bit5(0x0019e925), maps["Nameless Bar"], None),
	(0, 0, "!!Last Chihuahua", "Find evidence of the last remaining Chihuahua for Mack in Hatoba",
		3, None, bit5(0x0019e949), maps["Hatoba Ferry Terminal"], None),
	(0, 0, "!!Rescue Moriniu", "Rescue Moriniu from Adam Ant's captivity after he gets captured collecting wood for Mado's new building",
		3, AchievementType.MISSABLE, bit7(0x0019e922), maps["Forest Watchtower"], None),
	(0, 0, "!!Bombdelion Quest", "Bring Sakae at the Trader Camp north of Hatoba his Bombdelion Fluff, receiving a supply of explosives",
		3, None, bit3(0x0019e946), maps["Trader Camp Tent (Bombdelion)"], None),
	(0, 0, "!!Azusa Escort", "Escort the traders safely from Hatoba to Azusa",
		3, None, bit2(0x0019e931), maps["Azusa Bottom"], None),
	(0, 0, "!!Signal Bullet Quest", "Hunt down the Greater Manta using Zushio's Signal Bullet technology",
		4, None, bit1(0x0019e925), maps["Bazaarska Vehicle Shop"], None)
]
for ach_id, badge, title, desc, points, type, addr, map_id, flags in ach_flags:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=type)
	ach.add_core([
		(mem.current_map == map_id),
		(delta(addr) == value(0)),
		(addr == value(1))
	])

	ach_set.add_achievement(ach)

# Enemy Bounties
bounty_types = []
ach_bounties = [ # ID, Badge, Title, Description, Points, Type, Address
	(0, 0, "Sand Shark", "Defeat the Sand Shark in the desert east of Mado",
		3, None, bit3(0x0019e8bb))
]

# Challenge Hunts
ach_hunts = [ # ID, Badge, Title, Description Override, Points, Hunts Required
	(0, 0, "Sprouting Challenger", 'Clear 10 Challenge Hunts, earning the title of "Challenger"', 5, 10),
	(0, 0, "Budding Challenger", '', 5, 20),
	(0, 0, "Flowering Challenger", '', 10, 30),
	(0, 0, "Blooming Challenger", '', 10, 40),
	(0, 0, "Evergreen Challenger", 'Clear all 56 Challenge Hunts', 25, 56)
]
for ach_id, badge, title, desc, points, hunts_req in ach_hunts:
	if not desc:
		desc = f"Clear {hunts_req} Challenge Hunts"
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)

	# Only two maps where you can hand in Challenge Hunts
	logic = [(mem.current_map == maps["Hatoba Hunt Office"]) | (mem.current_map == maps["Villain Museum"])]

	# Delta bitcounts for hunt clear flags
	# First byte uses bits 0-6
	logic.extend(partial_bitcount(0x0019e9ba, range(0, 7), is_delta=True))
	# 6 full bytes of bits
	for addr in range(0x0019e9bb, 0x0019e9c1):
		logic.append(add_source(delta(bitcount(addr))))
	# Last byte uses only bit7
	# Since hunts can only increment by 1, we check if it's 1 less than goal
	logic.append((delta(bit7(0x0019e9c1)) == hunts_req - 1))

	# Current memory bitcounts, same addresses as above
	logic.extend(partial_bitcount(0x0019e9ba, range(0, 7)))
	for addr in range(0x0019e9bb, 0x0019e9c1):
		logic.append(add_source(bitcount(addr)))
	logic.append((measured(bit7(0x0019e9c1) == hunts_req)))

	ach.add_core(logic)
	ach_set.add_achievement(ach)


ach_loots = [ # ID, Badge, Title, Description, Points, Addresses, Maps
	(0, 0, "Loot Mado", "Mado", 5, (0x00, 0, 0x00, 0), [0x00])
]


# Levels
ach_levels = [ # ID, Badge, Title, Points, Class, Index, Threshold
	(0, 0, "!!Level 20", 3, "Any", -1, 20),
	(0, 0, "!!Level 40", 5, "Any", -1, 40),
	(0, 0, "!!Level 60 Hunter", 10, "Hunter", 0, 60),
	(0, 0, "!!Level 60 Mechanic", 10, "Mechanic", 1, 60),
	(0, 0, "!!Level 60 Soldier", 10, "Soldier", 2, 60),
	(0, 0, "!!Level 60 Nurse", 10, "Nurse", 3, 60),
	(0, 0, "!!Level 60 Wrestler", 10, "Wrestler", 4, 60),
	(0, 0, "!!Level 60 Artist", 10, "Artist", 5, 60),
	(0, 0, "!!Level 60 Dog", 10, "Dog", 6, 60),
	(0, 0, "!!Level 60 Money Eater", 10, "Money Eater", 7, 60)
]

def party_stat(party_index: int, offset: int):
	return mem.party[party_index] * mem.offsets["Character"] >> byte(mem.char_base + offset)

for ach_id, badge, title, points, char_class, class_index, threshold in ach_levels:
	ach = Achievement(id=ach_id, badge=badge, description="", title=title, points=points, type=None)
	ach.add_core((mem.chars["Player"]["Level"] > 1))

	logic = []
	for i in range(0, 4): # All achievements care about primary classes
		temp_logic = [
			(delta(party_stat(i, mem.offsets["Level"])) == threshold - 1),
			(party_stat(i, mem.offsets["Level"]) == threshold)
		]
		if class_index > -1:
			temp_logic.append((party_stat(i, mem.offsets["Class"]) == value(class_index)))
		logic.append(temp_logic)

	if char_class == "Any":
		class_desc = ""
	elif char_class == "Dog":
		class_desc = " with Pochi, Licky or Hachi"
	elif char_class == "Money Eater":
		class_desc = " with a Money Eater"

	else: # Regular classes should account for subclassing
		class_desc = f" with {char_class} as a party member's primary or secondary class"

		for i in range(0, 4):
			logic.append([ # Subclasses are index from 1, with 0 being no subclass
				(delta(party_stat(i, mem.offsets["Subclass"] + class_index + 1)) == threshold - 1),
				(party_stat(i, mem.offsets["Subclass"] + class_index + 1) == threshold),
				(party_stat(i, mem.offsets["Subclass"]) == value(class_index + 1))
			])

	for l in logic:
		ach.add_alt(l)

	ach.description = f"Reach level {threshold}{class_desc}"
	ach_set.add_achievement(ach)



# Dog / Money Eater Edge Cases


# Progression / Challenges

# Grapplers on the bridge
# Progression encounter in map without any other encounters, so we can just check if all enemies have died in an encounter
bridge_logic = [
	(mem.game_state == 2),
	(mem.current_map == maps["Bay Bridge"]),
	(delta(mem.enemies[0]["HP"]) > value(0)) | (delta(mem.enemies[1]["HP"]) > value(0)) | (delta(mem.enemies[2]["HP"]) > value(0)) | (delta(mem.enemies[3]["HP"]) > value(0)),
	(mem.enemies[0]["HP"] == 0) & (mem.enemies[1]["HP"] == 0) & (mem.enemies[2]["HP"] == 0) & (mem.enemies[3]["HP"] == 0)
]
progression_bridge = Achievement(id=0, badge=0, title="!!Clear the Blockade",
	description="Clear the Grappler blockade on the bridge to Hatoba",
	points=5, type=AchievementType.PROGRESSION)
progression_bridge.add_core(bridge_logic)
ach_set.add_achievement(progression_bridge)

challenge_bridge = Achievement(id=0, badge=0, title="You and What Army?",
	description="Defeat the Grapplers occupying the bridge with only a single party member",
	points=5, type=AchievementType.MISSABLE)
challenge_bridge.add_core(bridge_logic)
# Party members get added sequentially so we only need to check if the second slot has no one in it
challenge_bridge.add_core((mem.party[1] == value(0xff)))
ach_set.add_achievement(challenge_bridge)

# Misc achievements
ach_igoggles = Achievement(id=0, badge=0, title="!!Received iGoggles",
	description="Receive Maria's iGoggles, beginning your path of vengeance",
	points=1, type=AchievementType.PROGRESSION)
ach_igoggles.add_core([
	(mem.current_map == maps["Mado"]),
	(delta(mem.inventory["Tools"][0][0]) == 0),
	(mem.inventory["Tools"][0][0] == 0x05b),
	(delta(mem.inventory["Tools"][0][1]) == 0),
	(mem.inventory["Tools"][0][1] == 1)])
ach_set.add_achievement(ach_igoggles)

ach_pocketmoney = Achievement(id=0, badge=0, title="!!Pocket Money",
	description="Receive a reward from Karu for gifting him enough pocket money",
	points=1, type=AchievementType.MISSABLE)
ach_pocketmoney.add_core([
	(mem.current_map == maps["Mado Garage"]),
	(delta(mem.pocket_money) > 28),
	(mem.pocket_money < 2)
])
ach_set.add_achievement(ach_pocketmoney)

ach_dogs = Achievement(id=0, badge=0, title="Free to a Good Home",
	description="Bring all of the dogs from Dog Village to the old man in the greenhouse in Mado",
	points=2, type=AchievementType.MISSABLE)
ach_dogs.add_core([
	(mem.current_map == maps["Mado Greenhouse"]),
	(add_source(delta(bit4(0x19e9c2)))), (add_source(delta(bit2(0x19e9c2)))),
	(add_source(delta(bit0(0x19e9c2)))), (add_source(delta(bit6(0x19e9c3)))),
	(add_source(delta(bit4(0x19e9c3)))), (add_source(delta(bit2(0x19e9c3)))),
	(add_source(delta(bit0(0x19e9c3)))), (delta(bit6(0x19e9c4)) == 7),
	(add_source(bit4(0x19e9c2) / bit3(0x19e9c2))), (add_source(bit2(0x19e9c2) / bit1(0x19e9c2))),
	(add_source(bit0(0x19e9c2) / bit7(0x19e9c3))), (add_source(bit6(0x19e9c3) / bit5(0x19e9c3))),
	(add_source(bit4(0x19e9c3) / bit3(0x19e9c3))), (add_source(bit2(0x19e9c3) / bit1(0x19e9c3))),
	(add_source(bit0(0x19e9c3) / bit7(0x19e9c4))), (remember(bit6(0x19e9c4) / bit5(0x19e9c4))),
	(measured(recall() == 8))
])
ach_set.add_achievement(ach_dogs)


ach_set.save(path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")