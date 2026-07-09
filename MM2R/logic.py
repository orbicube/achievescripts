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
			if not isinstance(note_dict[key_str], list):
				note_dict[key_str] = [note_dict[key_str], val]
			else:
				note_dict[key_str].append(val)
		else:
			note_dict[key_str] = val

	return note_dict
maps = note2dict("D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data\\24022-Notes.json", "0x119740")

## Helper functions
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
					bit_logic = bit_logic.with_flag(MEASURED)
				case Measured.MEASURED_PCT:
					bit_logic = bit_logic.with_flag(MEASURED_PCT)
		logic[-1] = bit_logic

	return logic


def bitcount_range(start_addr: int, start_bit: int, end_addr: int, end_bit: int, goal: int = 0):
	return "foo"


def add_maps(logic: list, map_ids: list|int):
	if isinstance(map_ids, list):
		for m in map_ids:
			logic.append(or_next(mem.current_map == m))

		logic[-1] = (mem.current_map == m)
	else:
		logic.append(mem.current_map == map_ids)

	return logic

def party_stat(party_index: int, offset: int):
	return mem.party[party_index] * mem.offsets["Character"] >> byte(mem.char_base + offset)

## Constants
IN_COMBAT = (mem.game_state == value(2))
# Not strictly needed, save data is loaded while on main menu
SAVE_PROTECTION = (delta(mem.current_map) < maps["Loading Save"])

## Quests/Flag-based Achievements
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
	(0, 0, "!!Stingy Hunter", 'After completing the quest "Motorcycle of Revenge", decline to give the Hunter any money, earning the title of "Stingy Hunter"',
		1, None, bit5(0x0019e759), maps["Nameless Bar"], [(bit5(0x0019e925), True)]),
	(0, 0, "!!Save Rinka", "Find the missing girl Rinka and return her to her parents",
		3, AchievementType.MISSABLE, bit1(0x0019e926), maps["Trader Camp (Rinka Parents)"], None),
	(0, 0, "!!Last Chihuahua", "Find evidence of the last remaining Chihuahua for Mack in Hatoba",
		3, None, bit5(0x0019e949), maps["Hatoba Ferry Terminal"], None),
	(0, 0, "!!Rescue Moriniu", "Rescue Moriniu from Adam Ant's captivity after he gets captured collecting wood for Mado's new building",
		3, AchievementType.MISSABLE, bit7(0x0019e922), maps["Forest Watchtower"], None),
	(0, 0, "!!Bombdelion Quest", "Bring Sakae at the Trader Camp north of Hatoba his Bombdelion Fluff, receiving a supply of explosives",
		3, None, bit3(0x0019e946), maps["Trader Camp Tent (Bombdelion)"], None),
	(0, 0, "!!Azusa Escort", "Escort the traders safely from Hatoba to Azusa",
		3, None, bit2(0x0019e931), maps["Azusa Bottom"], None),
	(0, 0, "!!Signal Bullet Quest", "Hunt down the Greater Manta using Zushio's Signal Bullet technology",
		4, None, bit1(0x0019e925), maps["Bazaarska Vehicle Shop"], None),
	(0, 0, "!!Sally Quest", "Show Sally of Bazaarska the wider world, then return her home",
		2, None, bit5(0x0019e948), maps["Bazaarska"], None),
	(0, 0, "The Power of Music", "Unlock the ability to assign subclasses by using a strange man's Potential Headphones",
		2, None, bit5(0x0019e81d), maps["Bar Thirsty 2F"], None),
	(0, 0, "!!Richie Weapons Trafficking", "Perform some light weapons trafficking for Richie in the Mindless hideout",
		3, None, bit5(0x0019e954), maps["El Nino Teleporter"], None),
	(0, 0, "!!Iron Shark", "Hunt the Iron Shark for the traders near Bar Thirsty",
		3, None, bit0(0x0019e928), maps["Trader Camp (Iron Shark)"], None),
	(0, 0, "!!Cowardly Choice", 'Upon arriving at Delta Rio by boat, accept the Grappler\'s invitation to join, earning the title of "Bad Rookie"',
		1, AchievementType.MISSABLE, bit2(0x0019e9d4), maps["Delta Rio Ferry Terminal"], [(bit2(0x0019e759), True)])
]
for ach_id, badge, title, desc, points, type, addr, map_id, flags in ach_flags:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=type)
	ach.add_core([
		SAVE_PROTECTION,
		mem.current_map == map_id,
		delta(addr) == value(0),
		addr == value(1)
	])

	if flags:
		for f in flags:
			ach.add_core(f[0] == int(f[1]))

	ach_set.add_achievement(ach)
	#print(title)

## Enemy Bounties
bounty_types = []
ach_bounties = [ # ID, Badge, Title, Description, Points, Type, Name, Map
	(0, 0, "!!Sand Shark", "Defeat the Sand Shark in the desert east of Mado",
		3, None, "Sand Shark", maps["Overworld"]),
	(0, 0, "!!Desperoid", "Defeat the Desperoid near El Niño",
		3, None, "Desperoid", maps["Overworld"]),
	(0, 0, "Adam Ant-ium", "Defeat Adam Ant inside its nest near the Forest Watchtower",
		5, None, "Adam Ant", maps["Giant Ant Cave B4F"]),
	(0, 0, "!!Thousand Radiata", "Defeat the Thousand Radiata in the forest west of Hatoba",
		5, None, "Thousand Radiata", maps["Overworld"]),
	(0, 0, "Rhino? Gone", "Defeat the Rhinogon in the deserts near Bar Thirsty",
		4, None, "Rhinogon", maps["Overworld"]),
	(0, 0, "!!Skunks", "Defeat Skunks atop the Grappler Tower",
		10, AchievementType.PROGRESSION, "Skunks", maps["Grappler Tower 10F"]),
	(0, 0, "!!Myth Ladybug", "Defeat the Myth Ladybug near Nobotoke Village",
		10, None, "Myth Ladybug", maps["Overworld"]),
	(0, 0, "!!Madam Muscle", "Defeat Madam Muscle in the Protein Palace",
		10, None, "Madam Muscle", maps["Protein Palace B5F"]),
	(0, 0, "!!Kamikaze King", "Defeat the Kamikaze King northeast of Islaporto",
		10, None, "Kamikaze King", maps["Overworld"]),
	(0, 0, "From Hell's Heart I Shoot at Thee", "Defeat U-Shark, completing Captain Beihab's quest for vengeance and acquiring your own ship",
		10, AchievementType.PROGRESSION, "U-Shark", maps["Overworld"]),
	(0, 0, "!!Flying Fish", "Defeat the Flying Fish lurking in the waters near Delta Rio",
		5, None, "Flying Fish", maps["Overworld"]),
	(0, 0, "!!Dust Hominid", "Defeat the Dust Hominid inside the Wind Farm",
		5, None, "Dust Hominid", maps["Wind Farm B1F"]),
	(0, 0, "!!Total Turtle", "Defeat the Total Turtle in the waters west of Islaporto",
		5, None, "Total Turtle", maps["Overworld"]),
	(0, 0, "!!Vile Vendor", "Defeat the Vile Vendor within the Vending Paradise",
		10, None, "Vile Vendor", maps["Vending Paradise Inside"]),
	(0, 0, "!!Nadir Ghost", "Defeat the ghost haunting hotel Nadir",
		10, None, "Nadir Ghost", maps["Nadir 13F"]),
	(0, 0, "!!Groween", "Defeat Groween in the depths of Freak Island",
		10, None, "Groween", maps["Groween"]),
	(0, 0, "!!Cagliostro", "Defeat Cagliostro within the Dark Canal",
		10, None, "Cagliostro", maps["Dark Canal 2F"]),
	(0, 0, "!!Sea Mon-Star", "Defeat the Sea Mon-Star in the valley near Moro Poco",
		5, None, "Sea Mon-Star", maps["Overworld"]),
	(0, 0, "!!Mimic Stairs", "Defeat the Mimic Stairs in Moro Poco",
		10, None, "Mimic Stairs", [maps["Moro Poco"], maps["Moro Poco 2F"]]),
	(0, 0, "!!Bullfrog", "Defeat Bullfrog at Devil island",
		10, None, "Bullfrog", maps["Devil Island"]),
	(0, 0, "!!Sandy Dandy", "Sense and defeat Sandy Dandy in the desert east of South Gate",
		10, None, "Sandy Dandy", maps["Overworld"]),
	(0, 0, "!!Daedalus", "Defeat the Daedalus in the desert west of South Gate",
		10, None, "Daedalus", maps["Overworld"]),
	(0, 0, "!!Hovering Dog", "Defeat the Hovering Dog in Rain Valley",
		10, None, "Hovering Dog", maps["Rain Valley"]),
	(0, 0, "!!Battleshipsaurus", "Defeat the Battleshipsaurus in Rain Valley",
		10, None, "Battleshipsaurus", maps["Rain Valley"]),
	(0, 0, "!!Ted Broiler", "Defeat Ted Broiler within Bias City, completing your quest for vengeance",
		25, AchievementType.PROGRESSION, "Ted Broiler", maps["Bias City B3F"]),
	(0, 0, "!!U-U-Shark", "Defeat the U-U-Shark at the Water Bypass",
		50, AchievementType.MISSABLE, "U-U-Shark", maps["Water Bypass"]),
	(0, 0, "EX-Daedalus", "Defeat the EX-Daedalus in the desert west of Deathcruz",
		50, None, "EX-Daedalus", maps["Overworld"]),
	(0, 0, "!!Mothershipsaurus", "Defeat the Mothershipsaurus and its gaggle of Battleshipsauri in Rain Valley",
		50, None, "Mothershipsaurus", maps["Rain Valley"])
]
for ach_id, badge, title, desc, points, ach_type, bounty_name, map_id in ach_bounties:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=ach_type)

	logic = add_maps([SAVE_PROTECTION], map_id)
	logic.append([
		delta(mem.bounties[bounty_name]) == value(0),
		mem.bounties[bounty_name] == value(1)
	])

	ach.add_core(logic)
	ach_set.add_achievement(ach)

# Pichi Pichi Bounty achievement requires quest completion as well
ach_pichipichi = Achievement(id=0, badge=0, title="!!Pichi Pichi Finale", points=10, type=None,
	description="Defeat the Pichi Pichi Brothers once and for all and return the stolen goods to Old Wolf in Hatoba")
ach_pichipichi.add_core([
	SAVE_PROTECTION,
	mem.bounties["Pichi Pichi Bros"] == value(1),
	bit3(0x0019e955) == value(1)
])
ach_pichipichi.add_alt([
	mem.current_map == maps["Melt-town Sewers"],
	delta(mem.bounties["Pichi Pichi Bros"]) == value(0)
])
ach_pichipichi.add_alt([
	mem.current_map == maps["Hatoba Ferry Terminal 3F"],
	delta(bit3(0x0019e955)) == value(0)
])

## Challenge Hunts
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
	logic = [ SAVE_PROTECTION,
		(mem.current_map == maps["Hatoba Hunt Office"]) | (mem.current_map == maps["Villain Museum"]
	)]

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
	logic.append(measured(bit7(0x0019e9c1) == hunts_req))

	ach.add_core(logic)
	ach_set.add_achievement(ach)


## Monster Database
ach_database = [ # ID, Badge, Title, Description, Points, Type, Threshold
	(0, 0, "!!Monster Data 25%", "25%", 5, None, 120),
	(0, 0, "!!Monster Data 50%", "50%", 10, None, 242),
	(0, 0, "!!Monster Data 99%", "99%", 50, AchievementType.MISSABLE, 488)
]
for ach_id, badge, title, desc, points, ach_type, threshold in ach_database:
	ach = Achievement(id=ach_id, badge=badge, title=title, type=ach_type,
		description=f"Fill {desc} of the monster database", points=points)
	logic = [ IN_COMBAT ]

	logic.append(add_source(delta(bit0(0x0019e761))))
	for addr in range(0x0019e762, 0x0019e79f):
		logic.append(add_source(delta(bitcount(addr))))
	logic.extend(partial_bitcount(addr=0x0019e79f, bits=range(4, 8),
		is_delta=True, count=threshold-1))

	logic.append(add_source(bit0(0x0019e761)))
	for addr in range(0x0019e762, 0x0019e79f):
		logic.append(add_source(bitcount(addr)))
	logic.extend(partial_bitcount(addr=0x0019e79f, bits=range(4, 8),
		count=threshold, measured=Measured.MEASURED))

	ach.add_core(logic)
	ach_set.add_achievement(ach)


## Looting
ach_loots = [ # ID, Badge, Title, Description, Points, Addresses, Maps
	(0, 0, "Loot Mado", "Mado", 5, (0x00, 0, 0x00, 0), [0x00])
]


## Character Recruits
ach_chars = [ # ID, Badge, Title, Description, Points, Character, Maps
	(0, 0, "!!Axel Recruit", "Free Axel from captivity in El Niño, recruiting him to your party",
		4, "Axel", maps["El Nino"]),
	(0, 0, "!!Pochi Recruit", "Find Pochi in the Dog Village, recruiting them to your party",
		3, "Pochi", maps["Dog Village"]),
	(0, 0, "You Only Live Thrice", "Rekindle Miska's undying spirit, recruiting her to your party",
		4, "Miska", maps["Mado Mince's Lab"]),
	(0, 0, "!!Money Eater Recruit", "Grow a Money Eater, recruiting it into your party",
		3, "Money Eater 1", [maps["Mado Garage"], maps["Bennett's House"], maps["Delta Rio Apartments 2F"]]),
	(0, 0, "!!Licky Recruit", "Encounter and defeat the Demon Dog Licky in the plains of Nobotke, recruiting them to your party",
		4, "Licky", maps["Overworld"]),
	(0, 0, "!!Hachi Recruit", "Feed Hachi its favorite treat in Taisha, recruiting them to your party",
		3, "Hachi", maps["Taisha"])
]
for ach_id, badge, title, desc, points, char_name, map_id in ach_chars:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)

	logic = add_maps([SAVE_PROTECTION], map_id)

	logic.append([
		delta(mem.chars[char_name]["Available"]) == value(0),
		mem.chars[char_name]["Available"] == value(1)
	])

	ach.add_core(logic)
	ach_set.add_achievement(ach)


## Class Levels
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
for ach_id, badge, title, points, char_class, class_index, threshold in ach_levels:
	ach = Achievement(id=ach_id, badge=badge, description="", title=title, points=points, type=None)
	ach.add_core([
		SAVE_PROTECTION,
		mem.chars["Player"]["Level"] > value(1)
	])

	logic = []
	for i in range(0, 4): # All achievements care about primary classes
		temp_logic = [
			delta(party_stat(i, mem.offsets["Level"])) == threshold - 1,
			party_stat(i, mem.offsets["Level"]) == threshold
		]
		if class_index > -1: # Don't need to check what the class is for agnostic achievements
			temp_logic.append(party_stat(i, mem.offsets["Class"]) == value(class_index))
		logic.append(temp_logic)

	if char_class == "Any":
		class_desc = ""
	elif char_class == "Dog":
		class_desc = " with Pochi, Licky or Hachi"
	elif char_class == "Money Eater":
		class_desc = " with a Money Eater"

	else: # Regular classes should account for subclassing
		class_desc = f" with {char_class} as a party member's primary or secondary class"

		sub_index = class_index + 1
		sub_address = mem.offsets["Subclass"] + sub_index
		for i in range(0, 4):
			logic.append([ # Subclasses are index from 1, with 0 being no subclass
				delta(party_stat(i, sub_address)) == threshold - 1,
				party_stat(i, sub_address) == threshold,
				party_stat(i, mem.offsets["Subclass"]) == value(sub_index)
			])

	for l in logic:
		ach.add_alt(l)

	ach.description = f"Reach level {threshold}{class_desc}"
	ach_set.add_achievement(ach)


## Progression / Challenges

# Grapplers on the bridge
# Progression encounter in map without any other encounters, so we can just check if all enemies have died in an encounter
bridge_logic = [
	delta(mem.game_state) == value(2),
	mem.game_state == value(2),
	mem.current_map == maps["Bay Bridge"],
	(delta(mem.enemies[0]["HP"]) > value(0)) | (delta(mem.enemies[1]["HP"]) > value(0)) | (delta(mem.enemies[2]["HP"]) > value(0)) | (delta(mem.enemies[3]["HP"]) > value(0)),
	mem.enemies[0]["HP"] == value(0), mem.enemies[1]["HP"] == value(0),
	mem.enemies[2]["HP"] == value(0), mem.enemies[3]["HP"] == value(0)
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
challenge_bridge.add_core(mem.party[1] == value(0xff))
ach_set.add_achievement(challenge_bridge)

challenge_skunks = Achievement(id=0, badge=0, title="!!Skunks Challenge",
	description="Defeat Skunks while all vehicles have at least 1 SP remaining",
	points=10, type=AchievementType.MISSABLE)
challenge_skunks.add_core([
	IN_COMBAT,
	delta(mem.bounties["Skunks"]) == value(0),
	trigger(mem.bounties["Skunks"] == value(1)),
	(mem.combat_vehicles[0]["Max HP"] == 0) | (mem.combat_vehicles[0]["HP"] > 0),
	(mem.combat_vehicles[1]["Max HP"] == 0) | (mem.combat_vehicles[1]["HP"] > 0),
	(mem.combat_vehicles[2]["Max HP"] == 0) | (mem.combat_vehicles[2]["HP"] > 0)
])
ach_set.add_achievement(challenge_skunks)

challenge_ushark = Achievement(id=0, badge=0, title="Feel the Lake Breeze",
	description="Defeat U-Shark with only the Harley and Sentry as your party's vehicles",
	points=10, type=AchievementType.MISSABLE)
challenge_ushark.add_core([
	delta(mem.game_state) == value(2),
	mem.game_state == value(2),
	mem.enemies[0]["ID"] == value(0x15f),
	delta(mem.bounties["U-Shark"]) == value(0),
	mem.bounties["U-Shark"] == value(1)
])
challenge_ushark.add_alt([
	mem.ngplus_count < value(4),
	(mem.party_vehicles[0] == value(8)) | (mem.party_vehicles[0] == value(9)) | (mem.party_vehicles[0] == value(0xff)),
	(mem.party_vehicles[1] == value(8)) | (mem.party_vehicles[1] == value(9)) | (mem.party_vehicles[1] == value(0xff)),
	(mem.party_vehicles[2] == value(8)) | (mem.party_vehicles[2] == value(9)) | (mem.party_vehicles[2] == value(0xff)),
	(mem.party_vehicles[3] == value(8)) | (mem.party_vehicles[3] == value(9)) | (mem.party_vehicles[3] == value(0xff)),
])
challenge_ushark.add_alt([
	mem.ngplus_count == value(4),
	(mem.party_vehicles[0] == value(1)) | (mem.party_vehicles[0] == value(0xff)),
	(mem.party_vehicles[1] == value(1)) | (mem.party_vehicles[1] == value(0xff)),
	(mem.party_vehicles[2] == value(1)) | (mem.party_vehicles[2] == value(0xff)),
	(mem.party_vehicles[3] == value(1)) | (mem.party_vehicles[3] == value(0xff)),
])
challenge_ushark.add_alt([
	mem.ngplus_count == value(7),
	(mem.party_vehicles[0] == value(3)) | (mem.party_vehicles[0] == value(0xff)),
	(mem.party_vehicles[1] == value(3)) | (mem.party_vehicles[1] == value(0xff)),
	(mem.party_vehicles[2] == value(3)) | (mem.party_vehicles[2] == value(0xff)),
	(mem.party_vehicles[3] == value(3)) | (mem.party_vehicles[3] == value(0xff)),
])
ach_set.add_achievement(challenge_ushark)

# Kills in one combat challenge
challenge_kills = Achievement(id=0, badge=0, title="They Just Keep Coming",
	description="Defeat 30 enemies in a single combat encounter", points=5)
challenge_kills.add_core([
	IN_COMBAT,
	measured(mem.kills > delta(mem.kills)).with_hits(30),
	reset_if(mem.game_state == value(1))
])
ach_set.add_achievement(challenge_kills)


## Enemy Kills
ach_kills = [ # ID, Badge, Title, Description, Points, Threshold, Title
	(0, 0, "!!Defeat 1000 Enemies", 'Defeat 1,000 enemies, earning the title of "Thousand Killer"',
		5, 1000, bit3(0x0019e75f)),
	(0, 0, "!!Defeat 5555 Enemies", 'Defeat 5,555 enemies, earning the title of "5555 Kills Leader"',
		10, 5555, bit1(0x0019e75f)),
	(0, 0, "!!Defeat 10000 Enemies", 'Defeat 10,000 enemies, earnign the title of "The Ace"',
		25, 10000, bit7(0x0019e760)),
]
for ach_id, badge, title, desc, points, threshold, title_bit in ach_kills:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)
	ach.add_core([
		measured_if(mem.kills > delta(mem.kills)),
		delta(mem.kills) == threshold - 1,
		measured(mem.kills == threshold),
		delta(title_bit) == value(0),
		title_bit == value(1)
	])
	ach_set.add_achievement(ach)


## Misc achievements
ach_igoggles = Achievement(id=0, badge=0, title="!!Received iGoggles",
	description="Receive Maria's iGoggles, beginning your path of vengeance",
	points=1, type=AchievementType.PROGRESSION)
ach_igoggles.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Mado"],
	delta(mem.inventory["Tools"][0][0]) == 0,
	mem.inventory["Tools"][0][0] == 0x05b,
	delta(mem.inventory["Tools"][0][1]) == 0,
	mem.inventory["Tools"][0][1] == 1
])
ach_set.add_achievement(ach_igoggles)

ach_pocketmoney = Achievement(id=0, badge=0, title="!!Pocket Money",
	description="Receive a reward from Karu for gifting him enough pocket money",
	points=1, type=AchievementType.MISSABLE)
ach_pocketmoney.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Mado Garage"],
	delta(mem.pocket_money) > 28,
	mem.pocket_money < 2
])
ach_set.add_achievement(ach_pocketmoney)

ach_dogs = Achievement(id=0, badge=0, title="Free to a Good Home",
	description="Bring all of the dogs from Dog Village to the old man in the greenhouse in Mado",
	points=2, type=AchievementType.MISSABLE)
ach_dogs.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Mado Greenhouse"],
	add_source(delta(bit4(0x19e9c2))), add_source(delta(bit2(0x19e9c2))),
	add_source(delta(bit0(0x19e9c2))), add_source(delta(bit6(0x19e9c3))),
	add_source(delta(bit4(0x19e9c3))), add_source(delta(bit2(0x19e9c3))),
	add_source(delta(bit0(0x19e9c3))), delta(bit6(0x19e9c4)) == value(7),
	add_source(bit4(0x19e9c2) / bit3(0x19e9c2)), add_source(bit2(0x19e9c2) / bit1(0x19e9c2)),
	add_source(bit0(0x19e9c2) / bit7(0x19e9c3)), add_source(bit6(0x19e9c3) / bit5(0x19e9c3)),
	add_source(bit4(0x19e9c3) / bit3(0x19e9c3)), add_source(bit2(0x19e9c3) / bit1(0x19e9c3)),
	add_source(bit0(0x19e9c3) / bit7(0x19e9c4)), remember(bit6(0x19e9c4) / bit5(0x19e9c4)),
	measured(recall() == value(8))
])
ach_set.add_achievement(ach_dogs)


ach_set.save(path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")