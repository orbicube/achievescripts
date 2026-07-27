from pycheevos.core.helpers import *
from pycheevos.core.constants import *
from pycheevos.models.achievement import Achievement
from pycheevos.models.set import AchievementSet
from pycheevos.models.leaderboard import Leaderboard

from enum import Enum
import collections

ach_set = AchievementSet(game_id = 24022, title = "Metal Max 2: Reloaded")

from memory import Memory
mem = Memory()

import json
#	Converts a simple non-pointer code note into a dict with descriptions as keys
#	Notes should be formatted as Description\r\n\0xValue1 = Key1\r\n0xValue2 = Key2
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

###################
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


def add_maps(map_ids: tuple|int):
	logic = []

	if isinstance(map_ids, tuple):
		for m in map_ids:
			logic.append(or_next(mem.current_map == m))

		logic[-1] = (mem.current_map == m)
	else:
		logic.append(mem.current_map == map_ids)

	return logic

def party_stat(party_index: int, offset: int):
	return mem.party[party_index] * mem.offsets["Character"] >> byte(mem.char_base + offset)

def vehicle_stat(party_index: int, offset: int):
	return mem.party_vehicles[party_index] * mem.offsets["Vehicle"] >> byte(mem.vehicle_base + offset)

def combat_logic(map_ids: tuple|int, enemies: tuple|int):
	logic = [IN_COMBAT]
	logic.extend(add_maps(map_ids))

	if isinstance(enemies, tuple):
		for i in range(0, len(enemies)):
			logic.append(mem.enemies[i]["ID"] == value(enemies[i]))

		for i in range(0, len(enemies)):
			logic.append(or_next(delta(mem.enemies[i]["HP"]) > value(0)))
		logic[-1] = (delta(mem.enemies[i]["HP"]) > value(0))

		for i in range(0, len(enemies)):
			logic.append(mem.enemies[i]["HP"] == value(0))

	else:
		logic.extend([
			mem.enemies[0]["ID"] == value(enemies),
			delta(mem.enemies[0]["HP"]) > value(0),
			mem.enemies[0]["HP"] == value(0)
		])

	return logic

class Region(Enum):
	EN = 0x73657551
	JP = 0x2f651c11

def dialogue_logic(dialogue_pre: int, dialogue_post: int, region: Region):
	logic = [
		mem.region == value(region.value),
		delta(mem.dialogue) == dialogue_pre,
		mem.dialogue == dialogue_post
	]
	return logic

## Constants
IN_COMBAT = (mem.game_state == value(2))
# Not strictly needed, save data is loaded while on main menu
SAVE_PROTECTION = (delta(mem.current_map) < maps["Loading Save"])

## Quests/Flag-based Achievements
ach_flags = [ # ID, Badge, Title, Description, Points, Type, Flag Address, Map ID, Extra Flags
	(625233, 0, "Surveying the Damage", "Clear away the rubble of Mado's destroyed buildings, paving the way for new structures",
		1, None, bit0(0x0019e91a), maps["Mado"], None),
	(625234, 0, "Ol' Reliable", "Receive a repaired vehicle from Nile at the Mado Garage",
		2, None, bit2(0x0019e91a), maps["Mado Garage"], None),	
	(625235, 0, "Early Check Out", "Rescue Khatia from the Grapplers running the El Niño Inn",
		3, None, bit1(0x0019e952), maps["El Nino Inn"], None),
	(625236, 0, "Neither Toothless nor Gutless", "Become a member of the Mindless, gaining access to party member recruitment",
		3, None, bit7(0x0019e952), maps["El Nino Mindless Hideout"], None),
	(625237, 0, "Chip Shortage", "Give Schriette in the Mindless hideout 25 Electronic Parts",
		3, None, bit4(0x0019e957), maps["El Nino Mindless Hideout"], None),
	(625238, 0, "Amateur Detectorist", "Find and return Anne's Ring to Irish in the camp east of Mado",
		2, None, bit1(0x0019e924), maps["Trader Camp (Harley Ring)"], None),
	(625239, 0, "Wheels of Freedom", "Purchase the vehicle being offered for sale at the trader camp east of Mado",
		1, None, bit7(0x0019e9fa), maps["Trader Camp (Harley Ring)"], None),
	(625240, 0, "Welcome to Flavortown", "Fulfil Irit's culinary curiosity by giving her a Cookbook and Curry Powder",
		2, None, bit3(0x0019e93a), maps["Mado Garage"], None),
	(625241, 0, "Antares Antagonist", "Destroy Antares for a Hunter in a bar east of Mado, receiving the keys to a vehicle as your reward",
		4, None, bit5(0x0019e925), maps["Nameless Bar"], None),
	(625242, 0, "Not Even a Penny?", 'After completing the quest "Motorcycle of Revenge", decline to give the Hunter any money, earning the title of "Stingy Hunter"',
		1, None, bit5(0x0019e759), maps["Nameless Bar"], [(bit5(0x0019e925), True)]),
	(625243, 0, "No Child Left Behind", "Find the missing girl Rinka and return her to her parents",
		3, AchievementType.MISSABLE, bit1(0x0019e926), maps["Trader Camp (Rinka Parents)"], None),
	(625244, 0, "Life Finds a Way", "Find evidence of the last remaining Chihuahua for Mack in Hatoba",
		3, None, bit5(0x0019e949), maps["Hatoba Ferry Terminal"], None),
	(625245, 0, "Them!", "Rescue Moriniu from Adam Ant's captivity after he gets abducted collecting wood for Mado's new building",
		3, AchievementType.MISSABLE, bit7(0x0019e922), maps["Forest Watchtower"], None),
	(625246, 0, "Improvised Explosive Dandelion", "Bring Sakae at the Trader Camp north of Hatoba his Bombdelion Fluff, receiving a supply of explosives",
		3, None, bit3(0x0019e946), maps["Trader Camp (Bombdelion) Tent"], None),
	(625247, 0, "Towards Sanctuary", "Escort the traders safely from Hatoba to Azusa",
		3, None, bit2(0x0019e931), maps["Azusa Bottom"], None),
	(626287, 0, "Just Needed a Push", "Open the tunnel from Hatoba to Bazaarska",
		1, None, bit0(0x0019e91d), maps["Bito's Tunnel"], None),
	(625248, 0, "Can't Run, Can't Hide", "Hunt the Greater Manta using Zushio's Signal Bullet technology",
		4, None, bit1(0x0019e925), maps["Bazaarska Vehicle Shop"], None),
	(625249, 0, "No Place Like Home", "Show Sally of Bazaarska the wider world, then return her home",
		2, None, bit5(0x0019e948), maps["Bazaarska"], None),
	(625250, 0, "The Power of Music", "Unlock the ability to assign subclasses by using a strange man's Potential Headphones",
		2, None, bit5(0x0019e81d), maps["Bar Thirsty 2F"], None),
	(625251, 0, "Arming the Resistance", "Perform some light weapons trafficking for Richie in the Mindless hideout",
		3, None, bit5(0x0019e954), maps["El Nino Teleporter"], None),
	(625252, 0, "Squirrelly Shark", "Hunt the Iron Shark for the traders near Bar Thirsty",
		4, None, bit0(0x0019e928), maps["Trader Camp (Iron Shark)"], None),
	(625253, 0, "You'll Turn That Easily?", 'Upon arriving at Delta Rio by boat, accept the Grappler\'s invitation to join, earning the title of "Bad Rookie"',
		1, AchievementType.MISSABLE, bit2(0x0019e9d4), maps["Delta Rio Ferry Terminal"], [(bit2(0x0019e759), True)]),
	(625254, 0, "In from the Cold", "Find the spy within Mendoza's inner circle and deliver their report to Richie",
		2, None, bit7(0x0019e956), maps["El Nino Mindless Hideout"], None),
	(625255, 0, "Cooking the Books", 'Report 300G of sales while tending the ill trader\'s shop, earning the title of "Shrewd Salesperson"',
		1, AchievementType.MISSABLE, bit6(0x0019e75a), maps["Trader Camp (Shopkeep) Left Tent"], None),
	(625256, 0, "MarilynLivingSpace", 'Buy an apartment for Marilyn in Delta Rio and fulfil her request to decorate it, earning the title of "Marilyn\'s Daddy"',
		2, AchievementType.MISSABLE, bit6(0x0019e75e), maps["Delta Rio Boat Shops"], None),
	(625257, 0, "Caught with Your Pants Down", "Defeat the monster hiding in Natalie's closet in Delta Rio",
		3, None, bit7(0x0019e946), maps["Delta Rio Apartments 3F"], None),
	(625258, 0, "Pichi Pichi on the Coast", "Defeat the Pichi Pichi Brothers after falling into their trap west of Delta Rio",
		3, None, bit3(0x0019e932), maps["Mundane Ruins (Delta Rio)"], None),
	(625259, 0, "Salvaged Love", "Salvage and return the Silver Music Box to Saki at Bennett's House",
		3, None, bit4(0x0019e92a), maps["Bennett's House"], None),
	(625260, 0, "Mechanical Grudge", 'Complete "Mechanical Employee" without Brute dying',
		2, AchievementType.MISSABLE, bit7(0x0019e941), maps["Islaporto Dock"], [(bit1(0x0019ea13), False)]),
	(625261, 0, "Unusual Delicacy", "Retrieve and Ant Egg for the barkeep in Hatoba",
		5, None, bit5(0x0019e943), maps["Hatoba Bar"], None),
	(625262, 0, "I've Lost My Mojo!", "Return Kenzie's macho extract that was stolen from him near Salon du Princess",
		3, AchievementType.MISSABLE, bit0(0x0019e931), maps["Overworld"], None),
	(625263, 0, "Petrochemical Potential", "Deliver Oiholotoxin to the doctor in Isalporto, gaining access to an endless supply of medication",
		2, None, bit4(0x0019e9d6), maps["Islaporto Hospital"], None),
	(625264, 0, "Am I Me?", "Help Danny in Islaporto eliminate his clones",
		3, None, bit6(0x0019e94c), maps["Islaporto"], None),
	(625265, 0, "Marble Madness", "Return the item believed to be stolen from the tourist visiting Taisha",
		2, None, bit2(0x0019e94e), maps["Taisha"], None),
	(625266, 0, "Profane Profit", "Destroy the saisen outside Taisha's shrine, taking the offerings to the God of War for yourself",
		3, None, bit3(0x0019e945), maps["Taisha"], None),
	(625267, 0, "Big Egg", 'Complete "The Ice Excavator" after destroying all of Taisha\'s ice walls',
		4, AchievementType.MISSABLE, bit3(0x0019e92f), maps["Taisha Ice Cave"], [(bit1(0x0019e9e6), True)]),
	(625268, 0, "Roadside Assistance", "Give the stranded vehicle near Taisha a new engine",
		3, None, bit2(0x0019e938), maps["Overworld"], None),
	(625269, 0, "Stay Hydrated", "Complete Dan's request to help his sister Cecile in Islaporto",
		3, None, bit5(0x0019e923), maps["Islaporto Sewers"], None),
	(625270, 0, "What Happened Last Night?", "Hunt the Trash Giant for Jin in Delta Rio, stopping the rampage of Wild Buses",
		5, None, bit4(0x0019e928), maps["Trader Camp (Scrap Metal)"], None),
	(625271, 0, "Lighthouse Liberation", "Defeat Mendoza and free El Niño from the Grappler tyranny",
		10, None, bit0(0x0019e958), maps["El Nino Observatory"], None),
	(625272, 0, "Precious Family... Appliance?", "Find the golden fridge that was stolen from Emma in El Niño",
		2, None, bit2(0x0019e959), maps["El Nino Observatory 2F"], None),
	(625273, 0, "Messy Business Arrangements", "Tow the lost ship back to Delta Rio",
		2, None, bit7(0x0019e944), maps["Delta Rio"], None),
	(625274, 0, "Unbothered. Moisturized. Happy. In My Tent. Focused. Flourishing", "Help the witch Jella in brewing a potion north of Islaporto",
		4, None, bit7(0x0019e92f), maps["Witch Tent"], None),
	(625275, 0, "Pichi Pichi in the Wind", "Defeat the Pichi Pichi Brothers after falling into their trap near the Wind Farm",
		4, None, bit7(0x0019e933), maps["Trader Camp (Wind Farm)"], None),
	(625276, 0, "Stablizing Succor", "After finding the Combotron for Anri in Taisha, give them some Atomic Stabilizer to heal their child",
		5, None, bit4(0x0019ea36), maps["Taisha Residential Building 3F"], [(bit6(0x0019e94f), True)]),
	(625277, 0, "Loch Locusts", "Clear the pleague of Aqua Walkers near Helmets island for the salvager in Isalporto",
		5, None, bit2(0x0019e93f), maps["Islaporto Salvage"], None),
	(625278, 0, "Shooting Blanks", "Settle the duel between Marco and Izu in Swan with neither dying",
		3, AchievementType.MISSABLE, bit2(0x0019e944), maps["Swan Inside"], [(bit0(0x0019ea1f), False)]),
	(625279, 0, "The Master of Unlocking", "After acquiring the Lock Hacker, use it to open every lock in the world",
		5, None, bit1(0x0019e94d), None, [(bit3(0x0019e94d), True)]),
	(625280, 0, "None of My Business", "Free the man stuck in a closet in the Delta Rio apartments",
		1, None, bit4(0x0019e9a3), maps["Delta Rio Apartments"], None),
	(625281, 0, "Chariot of the Lake", "Return Swan to its former glory, gaining its use as a ship",
		5, None, bit6(0x0019e92d), maps["Swan Outside"], None),
	(625282, 0, "Nostalgic Nourishment", "Give Bennett a taste of his youth with some canned ramen",
		3, None, bit6(0x0019e92b), maps["Bennett's House"], None),
	(625283, 0, "Without a Trace", "Figure out what happened to Toko of Islaporto's husband",
		5, None, bit0(0x0019e92b), maps["Islaporto Bar 2F"], None),
	(625284, 0, "Case Closed", "Solve the murder mystery at the Nadir hotel",
		5, None, bit0(0x0019e93b), maps["Nadir Outside"], None),
	(625285, 0, "Eye for an Eye", "Find Tony's murderer hiding from society and deliver retribution",
		3, None, bit6(0x0019e935), (maps["Freak Island Cave to Groween"], maps["Freak Island Jungle"]), None),
	(625286, 0, "Escape from Freak Island", "Find Latoya on Freak Island and bring her back to her family",
		4, None, bit4(0x0019e935), maps["Latoya's House"], None),
	(625287, 0, "Built for Love", "Figure out Marilyn's secret at her apartment in Delta Rio",
		1, None, bit6(0x0019e9d6), maps["Delta Rio Apartments 2F"], [(bit5(0x0019e9d6), False), (bit3(0x0019e8c7), True)]),
	(625288, 0, "Alleviating Ailments", "Fulfill Dan's second request to help his sister Cecile in Islaporto",
		2, None, bit3(0x0019e923), maps["Islaporto Sewers"], None),
	(625289, 0, "Empty Nester", "Find and return Cecile's missing Money Eater",
		4, None, bit6(0x0019e924), maps["Islaporto Sewers"], None),
	(625290, 0, "Enthralled in Ecstasy", "Bring Luckyna some Blue Crab Pincers for... personal use",
		3, None, bit5(0x0019e930), maps["Trader Camp (Luckyna)"], None),
	(625291, 0, "Arm Wrestling Contest Winner", 'Complete "Single Arm on the Lakebed" with Goodman and Irena surviving',
		4, AchievementType.MISSABLE, bit6(0x0019e93f), maps["Abandoned Building (Armgun)"], [(bit1(0x0019ea00), False)]),
	(625292, 0, "Bickering Until the End", "Settle the feud between the three brothers trying to marry Jenny in Moro Poco",
		3, None, bit5(0x0019e94b), maps["Moro Poco 3F"], None),
	(625499, 0, "Look Around You", "Repair Michael inside Devil Island, then find eight Space Parts using his scanner",
		4, None, bit0(0x0019e934), maps["Overworld"], None),
	(625500, 0, "Comfort at What Cost?", "Complete all three of Hyde's escalating requests to alleviate his suffering at the Staff Housing",
		10, None, bit6(0x0019e938), maps["Staff Housing"], None),
	(625501, 0, "Radical Radish Remedies", "Fulfil Dan's third and final request to help Cecile's illness",
		5, None, bit1(0x0019e923), maps["Islaporto Sewers"], None),
	(625502, 0, "No Rehabilitation, Only Revolution", "Defeat the warden of Deathcruz, liberating the prison town",
		10, None, bit1(0x0019e921), maps["Deathcruz Roof"], None),
	(625503, 0, "Monster Closet", "Retrieve the lost coin for Dallas in Deathcruz",
		3, None, bit6(0x0019e940), maps["Deathcruz Interior"], None),
	(625504, 0, "Would Hate to See Their Overdue Fees", "Find and return the missing 13th rental tank for the receptionist at Melt-Town",
		2, None, bit6(0x0019e931), maps["Melt-town Interior"], None),
	(625505, 0, "Cross-Continental Courier", 'Carry cargo shipments from Hoc\'s Trading Post to Melt-town, earning the title of "Wasteland Courier"',
		4, AchievementType.MISSABLE, bit5(0x0019e93a), maps["Melt-town Interior"], None),
	(625506, 0, "Pichi Pichi in the Fog", "Defeat the Pichi Pichi Brothers after falling into their trap west of Melt-town",
		5, None, bit5(0x0019e933), maps["Mundane Ruins (Rain Valley)"], None),
	(625507, 0, "Become Eternal", "Open the path from the Eternal Gate to Bias City",
		5, None, bit7(0x0019ea29), maps["Eternal Gate MB"], None),
	(625508, 0, "Leave Your Biases at the Door", "Use the Synchronizer to unlock the entrance to Bias City",
		5, None, bit5(0x0019e91b), maps["Bias City Outside"], None),
	(625509, 0, "Melon Madness", "Reload your completed save and exterminate the Meloween infestation in Deathcruz",
		4, None, bit6(0x0019e939), maps["Deathcruz Interior"], None),
	(625510, 0, "With Friends Like These...", "Help Professor Bato find some new friends",
		50, None, bit0(0x0019e93d), maps["Bato Lab"], None),
	(625511, 0, "New Development", "Rebuild the first building in Mado",
		3, None, bit4(0x0019e950), maps["Mado"], None),
	(625512, 0, "Bustling Suburb", "Rebuild the second building in Mado",
		4, None, bit7(0x0019e951), maps["Mado"], None),
	(625513, 0, "Practically a Metropolis", "Rebuild the third building in Mado",
		5, None, bit6(0x0019ea3c), maps["Mado"], None),
	(625514, 0, "Worth the Wait", "Hold the wrestler's spot in line at the rebuilt Mado Pharmacy",
		1, None, bit7(0x0019e953), maps["Mado Pharmacy"], None),
	(625515, 0, "Back to School", 'Complete both combat lessons in the rebuilt Mado School, earning the title of "Super Adult"',
		3, None, bit1(0x0019e75b), maps["Mado School"], [(bit4(0x0019ea60), True), (bit3(0x0019ea60), True)]),
	(625516, 0, "Long Lost Libations", "Sell 10 bottles of vintage liquor to the rebuilt Mado Bar",
		2, None, bit5(0x0019e953), maps["Mado Bar"], None),
	(625517, 0, "Skittish Customer", "Deliver a package from Smith in the rebuilt Mado Bar to the Human Village",
		2, None, bit2(0x0019e933), maps["Human Village"], None),
	(625518, 0, "Sin City", "Repair all machines in the rebuilt Mado Casino",
		4, None, bit3(0x0019e91b), maps["Mado Casino"], None),
]
for ach_id, badge, title, desc, points, type, addr, map_id, flags in ach_flags:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=type)
	ach.add_core(SAVE_PROTECTION)
	if map_id is not None:
		ach.add_core(add_maps(map_id))
	ach.add_core([delta(addr) == value(0), addr == value(1)])
	if flags:
		for f in flags:
			ach.add_core(f[0] == int(f[1]))
	ach_set.add_achievement(ach)
	#print(title)

ach_cannon = Achievement(id=626131, badge=0, title="Cannon Connoisseur",
	description='Complete both the "Vintage Cannon" and "The Desert Tank Freak" quests',
	points=4, type=AchievementType.MISSABLE)
ach_cannon.add_core([
	SAVE_PROTECTION,
	bit2(0x0019e941) == value(1),
	bit1(0x0019e942) == value(1)
])
ach_cannon.add_alt([
	mem.current_map == maps["Deathcruz Interior"],
	delta(bit2(0x0019e941)) == value(0)
])
ach_cannon.add_alt([
	mem.current_map == maps["Caterpillar Villa"],
	delta(bit1(0x0019e942)) == value(0)
])
ach_set.add_achievement(ach_cannon)

ach_allie = Achievement(id=625644, badge=0, title="Reunited Lovers",
	description="Listen to Allie and Hunt discuss their future in Hatoba",
	points=2, type=AchievementType.MISSABLE)
ach_allie.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Hatoba"],
	bit1(0x0019e927) == value(1),
	bit3(0x0019e9ea) == value(0),
])
ach_allie.add_alt(dialogue_logic(0x26f8, 0x26fa, Region.EN))
ach_allie.add_alt(dialogue_logic(0x16d8, 0x16da, Region.JP))
ach_set.add_achievement(ach_allie)

## Enemy Bounties
bounty_types = []
ach_bounties = [ # ID, Badge, Title, Description, Points, Type, Name, Map
	(625293, 0, "Like a Shark out of Water", "Defeat the Sand Shark in the desert east of Mado",
		3, None, "Sand Shark", maps["Overworld"]),
	(625294, 0, "Desperoid for Attention", "Defeat the Desperoid near El Niño",
		3, None, "Desperoid", maps["Overworld"]),
	(625295, 0, "Adam Ant-ium", "Defeat Adam Ant inside its nest near the Forest Watchtower",
		5, None, "Adam Ant", maps["Giant Ant Cave B4F"]),
	(625296, 0, "Recursive Symmetry", "Defeat the Thousand Radiata in the forest west of Hatoba",
		5, None, "Thousand Radiata", maps["Overworld"]),
	(625297, 0, "Rhino Gone", "Defeat the Rhinogon in the deserts near Bar Thirsty",
		4, None, "Rhinogon", maps["Overworld"]),
	(625298, 0, "Monkey Wrenched", "Defeat Skunks atop the Grappler Tower",
		10, AchievementType.PROGRESSION, "Skunks", maps["Grappler Tower 10F"]),
	(625299, 0, "Myth No Longer", "Defeat the Myth Ladybug near Nobotoke Village",
		10, None, "Myth Ladybug", maps["Overworld"]),
	(625300, 0, "Intense Workout Session", "Defeat Madam Muscle in the Protein Palace",
		10, None, "Madam Muscle", maps["Protein Palace B5F"]),
	(625301, 0, "Intruder Alert", "Defeat the Kamikaze King northeast of Islaporto",
		10, None, "Kamikaze King", maps["Overworld"]),
	(625302, 0, "From Hell's Heart I Shoot at Thee", "Defeat U-Shark, completing Captain Beihab's quest for vengeance and acquiring your own ship",
		10, AchievementType.PROGRESSION, "U-Shark", maps["Overworld"]),
	(625303, 0, "Fighting Flying Fish for Funds", "Defeat the Flying Fish lurking in the waters near Delta Rio",
		5, None, "Flying Fish", maps["Overworld"]),
	(625304, 0, "From the Flash Game?", "Defeat the Dust Hominid inside the Wind Farm",
		5, None, "Dust Hominid", maps["Wind Farm B1F"]),
	(625305, 0, "Totally Turtle! Totally Party", "Defeat the Total Turtle in the waters west of Islaporto",
		5, None, "Total Turtle", maps["Overworld"]),
	(625306, 0, "Broken RNG", "Defeat the Vile Vendor within the Vending Paradise",
		10, None, "Vile Vendor", maps["Vending Paradise Inside"]),
	(625307, 0, "Ethereal Eviction", "Defeat the ghost haunting hotel Nadir",
		10, None, "Nadir Ghost", maps["Nadir 13F"]),
	(625308, 0, "Freak: Matched", "Defeat Groween in the depths of Freak Island",
		10, None, "Groween", maps["Groween"]),
	(625309, 0, "No Castles in Sight", "Defeat Cagliostro within the Dark Canal",
		10, None, "Cagliostro", maps["Dark Canal 2F"]),
	(625310, 0, "Mon-Star See, Mon-Star Do", "Defeat the Sea Mon-Star in the valley near Moro Poco",
		5, None, "Sea Mon-Star", maps["Overworld"]),
	(625311, 0, "Safety Inspection Failed", "Defeat the Mimic Stairs in Moro Poco",
		10, None, "Mimic Stairs", (maps["Moro Poco"], maps["Moro Poco 2F"])),
	(625312, 0, "Bullfrog in Boiling Water", "Defeat Bullfrog at Devil island",
		10, None, "Bullfrog", maps["Devil Island"]),
	(625313, 0, "Don Your Goggles, Sandstorm Approaching", "Sense and defeat Sandy Dandy in the desert east of South Gate",
		10, None, "Sandy Dandy", maps["Overworld"]),
	(625314, 0, "Save the Daedalus", "Defeat the Daedalus in the desert west of South Gate",
		10, None, "Daedalus", maps["Overworld"]),
	(625315, 0, "When Dogs Fly", "Defeat the Hovering Dog in Rain Valley",
		10, None, "Hovering Dog", maps["Rain Valley"]),
	(625316, 0, "You Sunk My Dinosaur", "Defeat the Battleshipsaurus in Rain Valley",
		10, None, "Battleshipsaurus", maps["Rain Valley"]),
	(625317, 0, "Ted and Gone", "Defeat Ted Broiler within Bias City, completing your quest for vengeance",
		25, AchievementType.PROGRESSION, "Ted Broiler", maps["Bias City B3F"]),
	(625318, 0, "Apex Predator", "Defeat the U-U-Shark at the Water Bypass",
		50, AchievementType.MISSABLE, "U-U-Shark", maps["Water Bypass"]),
	(625319, 0, "Brand New Daedalus", "Defeat the EX-Daedalus in the desert west of Deathcruz",
		50, None, "EX-Daedalus", maps["Overworld"]),
	(625320, 0, "Angry Mama", "Defeat the Mothershipsaurus and its gaggle of Battleshipsauri in Rain Valley",
		50, None, "Mothershipsaurus", maps["Rain Valley"])
]
for ach_id, badge, title, desc, points, ach_type, bounty_name, map_id in ach_bounties:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=ach_type)

	logic = [SAVE_PROTECTION]
	logic.extend(add_maps(map_id))
	logic.extend([
		delta(mem.bounties[bounty_name]) == value(0),
		mem.bounties[bounty_name] == value(1)
	])

	ach.add_core(logic)
	ach_set.add_achievement(ach)

# Pichi Pichi Bounty achievement requires quest completion as well
ach_pichipichi = Achievement(id=625378, badge=0, title="Pichi Pichi in the Ground", points=10, type=None,
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
ach_set.add_achievement(ach_pichipichi)

##################
## Challenge Hunts
ach_hunts = [ # ID, Badge, Title, Description Override, Points, Hunts Required
	(625321, 0, "Sprouting Challenger", 'Clear 10 Challenge Hunts, earning the title of "Challenger"', 5, 10),
	(625322, 0, "Budding Challenger", '', 5, 20),
	(625323, 0, "Flowering Challenger", '', 10, 30),
	(625324, 0, "Blooming Challenger", '', 10, 40),
	(625325, 0, "Evergreen Challenger", 'Clear all 56 Challenge Hunts', 25, 56)
]
for ach_id, badge, title, desc, points, hunts_req in ach_hunts:
	if not desc:
		desc = f"Clear {hunts_req} Challenge Hunts"
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)

	# Only two maps where you can hand in Challenge Hunts
	logic = [ pause_if(~SAVE_PROTECTION),
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


###################
## Monster Database
ach_database = [ # ID, Badge, Title, Description, Points, Type, Threshold
	(625326, 0, "Research Assistant", "25%", 5, None, 120),
	(625327, 0, "Adept Biographer", "50%", 10, None, 242),
	(625328, 0, "Comprehensive Taxonomist", "99%", 50, AchievementType.MISSABLE, 488)
]
for ach_id, badge, title, desc, points, ach_type, threshold in ach_database:
	ach = Achievement(id=ach_id, badge=badge, title=title, type=ach_type,
		description=f"Fill {desc} of the monster database", points=points)
	logic = [ pause_if(~IN_COMBAT) ]

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


#####################
## Character Recruits
ach_chars_human = [ # ID, Badge, Title, Description, Points, Character, Maps
	(625329, 0, "El Niño Espionage", "Free Axel from captivity in El Niño, recruiting him to your party",
		4, 1, maps["El Nino"]),
	(625331, 0, "You Only Live Thrice", "Rekindle Miska's undying spirit, recruiting her to your party",
		4, 2, maps["Mado Mince's Lab"]),
]
for ach_id, badge, title, desc, points, char, map_id in ach_chars_human:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)
	ach.add_core([
		SAVE_PROTECTION,
		add_maps(map_id),
		delta(mem.chars[char].available) == value(0),
		mem.chars[char].available == value(1)
	])
	ach_set.add_achievement(ach)

# Animals can technically go
ach_chars_animal = [  # ID, Badge, Title, Description, Points, Character, Maps
	(625330, 0, "Pick of the Litter", "Find Pochi in the Dog Village, recruiting them to your party",
		3, 0x0f, maps["Dog Village"]),
	(625332, 0, "They Grow Up So Fast", "Grow a Money Eater, recruiting it into your party",
		3, 0x13, (maps["Mado Garage"], maps["Bennett's House"], maps["Delta Rio Apartments 2F"])),
	(625333, 0, "Truly Ferocious", "Encounter and defeat the Demon Dog Licky in the plains of Nobotke, recruiting them to your party",
		4, 0x10, maps["Overworld"]),
	(625334, 0, "Tempting the Guardian", "Feed Hachi its favorite treat in Taisha, recruiting them to your party",
		3, 0x11, maps["Taisha Shrine"])
]
for ach_id, badge, title, desc, points, char, map_id in ach_chars_animal:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)
	ach.add_core([
		SAVE_PROTECTION,
		add_maps(map_id)
	])

	for i in range(9, 15):
		ach.add_alt([
			mem.chars[i].portrait == char,
			delta(mem.chars[i].available) == value(0),
			mem.chars[i].available == value(1)
		])

	ach_set.add_achievement(ach)

################
## Class Levels
ach_levels = [ # ID, Badge, Title, Points, Class, Index, Threshold
	(625335, 0, "Following in Maria's Footsteps", 3, "Any", -1, 20),
	(625336, 0, "Forging a New Path", 5, "Any", -1, 40),
	(625337, 0, "To the Ends of the Earth", 10, "Hunter", 0, 60),
	(625338, 0, "Vehicle Whisperer", 10, "Mechanic", 1, 60),
	(625339, 0, "Guns Blazing", 10, "Soldier", 2, 60),
	(625340, 0, "Nurturing Touch", 10, "Nurse", 3, 60),
	(625341, 0, "Who Grapples the Grapplers?", 10, "Wrestler", 4, 60),
	(625342, 0, "Flourishing Art Scene", 10, "Artist", 5, 60),
	(625343, 0, "Max's Best Friend", 10, "Dog", 6, 60),
	(625344, 0, "Paying Dividends", 10, "Money Eater", 7, 60)
]
for ach_id, badge, title, points, char_class, class_index, threshold in ach_levels:
	ach = Achievement(id=ach_id, badge=badge, description="", title=title, points=points, type=None)
	ach.add_core([
		SAVE_PROTECTION,
		mem.chars[0].level > value(1)
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


###########################
## Progression / Challenges

# Progression encounter in map without any other encounters
# So we can just check if all enemies have died in an encounter
bridge_logic = combat_logic(maps["Bay Bridge"], (0x13c, 0x13c, 0x12d, 0x12d))
progression_bridge = Achievement(id=625345, badge=0, title="Unpaid Tolls",
	description="Clear the Grappler blockade on the bridge to Hatoba",
	points=5, type=AchievementType.PROGRESSION)
progression_bridge.add_core(bridge_logic)
ach_set.add_achievement(progression_bridge)

challenge_bridge = Achievement(id=625346, badge=0, title="You and What Army?",
	description="Defeat the Grapplers occupying the bridge with only a single party member",
	points=5, type=AchievementType.MISSABLE)
challenge_bridge.add_core(bridge_logic)
# Party members get added sequentially so we only need to check if the second slot has no one in it
challenge_bridge.add_core(mem.party[1] == value(0xff))
ach_set.add_achievement(challenge_bridge)

challenge_skunks = Achievement(id=625347, badge=0, title="It'll Buff Out",
	description="Defeat Skunks while all vehicles have at least 1 SP remaining",
	points=10, type=AchievementType.MISSABLE)
challenge_skunks.add_core([
	IN_COMBAT,
	mem.current_map == maps["Grappler Tower 10F"],
	delta(mem.bounties["Skunks"]) == value(0),
	trigger(mem.bounties["Skunks"] == value(1)),
	(mem.combat_vehicles[0]["Max HP"] == 0) | (mem.combat_vehicles[0]["HP"] > 0),
	(mem.combat_vehicles[1]["Max HP"] == 0) | (mem.combat_vehicles[1]["HP"] > 0),
	(mem.combat_vehicles[2]["Max HP"] == 0) | (mem.combat_vehicles[2]["HP"] > 0)
])
ach_set.add_achievement(challenge_skunks)

challenge_ushark = Achievement(id=625348, badge=0, title="Feel the Lake Breeze",
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
	remember(mem.ngplus_count % 8),
	recall() < value(4),
	(mem.party_vehicles[0] == value(8)) | (mem.party_vehicles[0] == value(9)) | (mem.party_vehicles[0] == value(0xff)),
	(mem.party_vehicles[1] == value(8)) | (mem.party_vehicles[1] == value(9)) | (mem.party_vehicles[1] == value(0xff)),
	(mem.party_vehicles[2] == value(8)) | (mem.party_vehicles[2] == value(9)) | (mem.party_vehicles[2] == value(0xff))
])
challenge_ushark.add_alt([
	remember(mem.ngplus_count % 8),
	recall() == value(4),
	(mem.party_vehicles[0] == value(1)) | (mem.party_vehicles[0] == value(0xff)),
	(mem.party_vehicles[1] == value(1)) | (mem.party_vehicles[1] == value(0xff)),
	(mem.party_vehicles[2] == value(1)) | (mem.party_vehicles[2] == value(0xff))
])
challenge_ushark.add_alt([
	remember(mem.ngplus_count % 8),
	recall() == value(7),
	(mem.party_vehicles[0] == value(3)) | (mem.party_vehicles[0] == value(0xff)),
	(mem.party_vehicles[1] == value(3)) | (mem.party_vehicles[1] == value(0xff)),
	(mem.party_vehicles[2] == value(3)) | (mem.party_vehicles[2] == value(0xff))
])
ach_set.add_achievement(challenge_ushark)

challenge_cagliostro = Achievement(id=625350, badge=0, title="Trap Sprung",
	description="Defeat Cagliostro without ever having a party member inside a vehicle",
	points=10, type=AchievementType.MISSABLE)
challenge_cagliostro.add_core([
	mem.current_map == maps["Dark Canal 2F"],
	IN_COMBAT,
	mem.enemies[0]["ID"] == value(0x161),
	delta(mem.bounties["Cagliostro"]) == value(0),
	mem.bounties["Cagliostro"] == value(1),
	mem.party_vehicles[0] == value(0xff),
	mem.party_vehicles[1] == value(0xff),
	mem.party_vehicles[2] == value(0xff)
])
ach_set.add_achievement(challenge_cagliostro)

challenge_bullfrog = Achievement(id=625351, badge=0, title="Careful Dissection",
	description="Defeat Bullfrog without inflicting status effects on him or the Bull Crusher",
	points=10, type=AchievementType.MISSABLE)
challenge_bullfrog.add_core([
	(mem.game_state == value(1)).with_hits(1),
	IN_COMBAT,
	mem.current_map == maps["Devil Island"],
	or_next(mem.enemies[0]["ID"] == value(0x16f)),
	mem.enemies[0]["ID"] == value(0x16e),
	delta(mem.bounties["Bullfrog"]) == value(0),
	trigger(mem.bounties["Bullfrog"] == value(1)),
	or_next(mem.enemies[0]["Status"][0] > value(0)),
	reset_if(mem.enemies[0]["Status"][1] > value(0))
])
ach_set.add_achievement(challenge_bullfrog)

challenge_fog = Achievement(id=625519, badge=0, title="Cryptid Sighting",
	description='During the quest "In the Fog", defeat the Huge Recon UFO and King Saurus in one session',
	points=25, type=AchievementType.MISSABLE)
challenge_fog.add_core([
	reset_if(mem.current_map >= 0xfffe),
	mem.current_map == maps["Mundane Ruins (Rain Valley)"],
	IN_COMBAT,
	and_next(mem.enemies[0]["ID"] == value(0x7)),
	and_next(delta(mem.enemies[0]["HP"]) > value(0)),
	(mem.enemies[0]["HP"] == value(0)).with_hits(1),
	and_next(mem.enemies[0]["ID"] == value(0x165)),
	and_next(delta(mem.enemies[0]["HP"]) > value(0)),
	(mem.enemies[0]["HP"] == value(0)).with_hits(1),
])
ach_set.add_achievement(challenge_fog)

challenge_ted = Achievement(id=625352, badge=0, title="Searing Critique",
	description="Defeat Ted Broiler with two human party members having Artist as a class or subclass",
	points=25, type=AchievementType.MISSABLE)
challenge_ted.add_core([
	combat_logic(maps["Bias City B3F"], 0x16b),
	reset_if(mem.game_state == value(1))
])
for i in range(0, 3):
	challenge_ted.add_core([
		or_next(party_stat(i, mem.offsets["Class"]) == value(5)),
		and_next(party_stat(i, mem.offsets["Subclass"]) == value(6)),
		add_hits(delta(mem.game_state) == value(1))
	])
challenge_ted.add_core(always_false().with_hits(2))
ach_set.add_achievement(challenge_ted)

progression_vlad = Achievement(id=625353, badge=0, title="Vlad Vanquisher",
	description="Defeat Vlad, ridding the world of the Bias menace",
	points=25, type=AchievementType.WIN_CONDITION)
progression_vlad.add_core(combat_logic(maps["Bias City B7F (Final Boss)"], 0x173))
ach_set.add_achievement(progression_vlad)

challenge_vlad = Achievement(id=625354, badge=0, title="No Camping Within City Limits",
	description="Defeat all forms of Vlad in a single session without healing outside of combat",
	points=25, type=AchievementType.MISSABLE)
challenge_vlad.add_core(add_maps(maps["Bias City B7F (Final Boss)"]))
challenge_vlad.add_core(
	(mem.enemies[0]["ID"] == value(0x172)) &
	(delta(mem.enemies[0]["HP"]) > value(0)) &
	(mem.enemies[0]["HP"] == value(0)).with_hits(1)
)
# We only want the achievement to prime when it could be affected by player action
challenge_vlad.add_core(
	(mem.enemies[0]["ID"] == value(0x173)) &
	(delta(mem.enemies[0]["HP"]) > value(0)) &
	(trigger(mem.enemies[0]["HP"] == value(0)).with_hits(1))
)
for i in range(0, 4):
	challenge_vlad.add_core([
		and_next(mem.game_state == value(1)),
		and_next(mem.party[i] != value(0xff)),
		sub_source(delta(party_stat(i, mem.offsets["HP"]))),
		reset_if(party_stat(i, mem.offsets["HP"]) > value(0))
	])
ach_set.add_achievement(challenge_vlad)


###############
## Enemy Kills
ach_kills = [ # ID, Badge, Title, Description, Points, Threshold, Title
	(625355, 0, "Why's Everyone So Hostile?", 'Defeat 1,000 enemies, earning the title of "Thousand Killer"',
		5, 1000, bit3(0x0019e75f)),
	(625356, 0, "Cycle of Violence", 'Defeat 5,555 enemies, earning the title of "5555 Kills Leader"',
		10, 5555, bit1(0x0019e75f)),
	(625357, 0, "Maximum Carnage", 'Defeat 10,000 enemies, earning the title of "The Ace"',
		25, 10000, bit7(0x0019e760)),
]
for ach_id, badge, title, desc, points, threshold, title_bit in ach_kills:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)
	if threshold == 10000:
		ach.add_core(pause_if(~IN_COMBAT))
	else:
		ach.add_core(IN_COMBAT)

	ach.add_core([
		delta(title_bit) == value(0),
		title_bit == value(1),
		delta(mem.kills) < threshold,
	])

	if threshold == 10000:
		ach.add_core(
			measured_percent(mem.kills >= threshold))
	else:
		ach.add_core(mem.kills >= threshold)

	ach_set.add_achievement(ach)

# Kills in one combat challenge
challenge_kills = Achievement(id=625358, badge=0, title="They Just Keep Coming",
	description="Defeat 30 enemies in a single combat encounter", points=5)
challenge_kills.add_core([
	reset_if(mem.game_state != value(2)),
	add_source(mem.kills - delta(mem.kills)),
	add_hits(mem.kills > delta(mem.kills)),
	measured(always_false()).with_hits(30)
])
ach_set.add_achievement(challenge_kills)


############
## Vehicles
# For vehicles out in the field, there's no flags to indicate we've acquired them
# There's memory addresses that get used when the screen to name a character or vehicle appears
ach_vehicles = [ # ID, Badge, Title, Description, Points, Vehicle Index, Map, Extra Flags
	(625359, 0, "From Murder Weapons to Hospitals", "Complete a tour of the Vlad Museum, liberating the vehicle housed within",
		4, 4, maps["Vlad Museum B1F"], [(bit7(0x0019e9fc), True)]),
	(625360, 0, "Oh, That's Where I Parked It!", "Find the vehicle buried in the desert near Bar Thirsty",
		3, 2, maps["Overworld"], [(bit0(0x0019e8a8), True)]),
	(625361, 0, "Public Transport", "Find the hidden bus stop near Nobotoke and wrangle a Wild Bus",
		4, 3, maps["Overworld"], [(bit3(0x0019e8aa), True)]),
	(625362, 0, 'Cry "Havoc!" and Let Slip the God of War', "Steal the God of War from Taisha's shrine",
		3, 5, maps["Taisha Shrine"], [(bit1(0x0019e9d6), True)]),
	(625363, 0, "Metal for Nothing and Your Tanks for Free", "Create your very own tank with the help of Professor Bato",
		10, 8, maps["Bato Lab"], [(bit6(0x0019e75b), True)]),
	(625364, 0, "Always Wear a Helmet", "Find the vehicle stored within Helmets Island",
		5, 7, maps["Helmets Island B2F Room 7"], None),
	(625365, 0, "One Way Out", "Find the vehicle deep within Deadend Cave",
		5, 6, maps["Deadend Cave B5F"], [(bit2(0x0019ea13), True)]),
	(625366, 0, "Bury Me with My Tank", "Raise the vehicle out of the Buried Building, claiming it as your own",
		5, 12, maps["Buried Building"], None)
]
for ach_id, badge, title, desc, points, vehicle_index, map_id, flags in ach_vehicles:
	ach = Achievement(id=ach_id, badge=badge, title=title, description=desc, points=points, type=None)
	ach.add_core([
		SAVE_PROTECTION,
		mem.current_map == map_id,
		mem.game_state == value(2),
		mem.naming_char == value(0),
		delta(mem.naming_type) == value(0),
		mem.naming_type == value(1),
		delta(mem.naming_vehicle) == value(0),
		mem.naming_vehicle == value(vehicle_index)
	])

	if flags:
		for flag in flags:
			ach.add_core(flag[0] == int(flag[1]))

	ach_set.add_achievement(ach)


#############
## World Map
ach_worldmaps = [ # ID, Badge, Title, Description, Points, Threshold
	(625520, 0, "Acclimation", "Fill in 25% of the overworld map", 3, 140),
	(625521, 0, "Exploration", "Fill in 50% of the overworld map", 5, 280),
	(625522, 0, "Subjugation", 'Fill in all of the overworld map, earning the title of "World Traveler"',
		10, 560)
]
for ach_id, badge, title, desc, points, threshold in ach_worldmaps:
	ach = Achievement(id=ach_id, badge=badge, title=f"Wasteland {title}", description=desc, points=points)
	ach.add_core(SAVE_PROTECTION)

	if threshold == 560:
		ach.add_core([
			pause_if((mem.map_base > value(0)) & (delta(mem.map_ptr) == value(0))),
			pause_if((mem.map_base > value(0)) & (mem.map_ptr == value(0))),
			pause_if(delta(mem.map_base) == value(0)),
			pause_if(mem.map_base == value(0)),
		])
	else:
		ach.add_core([
			(mem.map_base > value(0)) & (delta(mem.map_ptr) > value(0)),
			(mem.map_base > value(0)) & (mem.map_ptr > value(0)),
		])

	for i in range(0, 559):
		ach.add_core(add_source(delta(mem.map_vals[i])))
	ach.add_core(delta(mem.map_vals[559]) < value(threshold * 8))
	for i in range(0, 559):
		ach.add_core(add_source(mem.map_vals[i]))
	logic = (mem.map_vals[559] >= value(threshold * 8))
	if threshold == 560:
		logic = (measured_percent(logic))
	ach.add_core(logic)

	ach_set.add_achievement(ach)


############
# Minigames
# Cumulative minigame winnings get calculated on exiting a minigame
# To properly measure it in the toolkit, we have to use different values depending on the miigame
ach_minigames = Achievement(id=625609, badge=0, title="Rigged in Your Favour", points=4, type=None,
	 description='Win 10,000G from minigames, earning the title of "Wasteland Gambler"')
ach_minigames.add_core([
	SAVE_PROTECTION
])
# Ribbit Race
ach_minigames.add_alt([
	pause_if((mem.frog.state == value(0)) | (mem.frog.state > value(10))),
	mem.game_state == value(2),
	remember(mem.winnings / value(2)),
	remember(delta(mem.frog.winnings) + recall()),
	recall() < value(10000),
	remember(mem.winnings / value(2)),
	remember(mem.frog.winnings + recall()),
	measured(recall() >= value(10000))
])
# Bang Bang Tanks
ach_minigames.add_alt([
	pause_if(~mem.tanks.active()),
	mem.game_state == value(2),
	remember(mem.winnings / value(2)),
	remember(delta(mem.tanks.winnings) + recall()),
	recall() < value(10000),
	remember(mem.winnings / value(2)),
	remember(mem.tanks.winnings + recall()),
	measured(recall() >= value(10000))
])
# Slots
ach_minigames.add_alt([
	pause_if(~mem.slots.active()),
	mem.game_state == value(3),
	remember(mem.winnings / value(2)),
	remember(delta(mem.slots.winnings) + recall()),
	recall() < value(10000),
	remember(mem.winnings / value(2)),
	remember(mem.slots.winnings + recall()),
	measured(recall() >= value(10000))
])
ach_set.add_achievement(ach_minigames)

ach_ribbitrace = Achievement(id=625371, badge=0, title="Froggy Derby",
	description="Place a winning bet on a pair of frogs with odds of 5 or higher",
	points=5, type=None)
ach_ribbitrace.add_core([
	SAVE_PROTECTION,
	mem.game_state == value(2),
	delta(mem.frog.state) == value(5),
	mem.frog.state == value(6),
	remember(mem.frog.bet_cost),
	mem.frog.bet_value == recall(),
	remember(recall() * value(5)),
	mem.frog.payout >= recall()
])
ach_set.add_achievement(ach_ribbitrace)

ach_tanks_score = Achievement(id=625901, badge=0, title="Pro Wargamer",
	description="Obtain a score of 800 or higher in Bang Bang Tanks! Reloaded",
	points=5, type=None)
ach_tanks_score.add_core([
	mem.tanks.active(),
	mem.game_state == value(2),
	delta(mem.tanks.state) == value(1),
	mem.tanks.state == value(0),
	remember(mem.tanks.score & value(0x80000000)),
	recall() == value(0),
	mem.tanks.score >= value(800)
])
ach_set.add_achievement(ach_tanks_score)

ach_tanks_combo = Achievement(id=625902, badge=0, title="Sharpshooter Supreme",
	description="Reach a combo of 25 hits in Bang Bang Tanks! Reloaded",
	points=5, type=None)
ach_tanks_combo.add_core([
	mem.tanks.active(),
	mem.game_state == value(2),
	mem.tanks.state == value(1),
	delta(mem.tanks.combo) < value(25),
	mem.tanks.combo >= value(25)
])
ach_set.add_achievement(ach_tanks_combo)


###########
## Misc
ach_igoggles = Achievement(id=625367, badge=0, title="From the Ashes",
	description="Receive Maria's iGoggles, beginning your path of vengeance",
	points=1, type=AchievementType.PROGRESSION)
ach_igoggles.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Mado Garage"],
	delta(mem.inventory["Tools"][0]["ID"]) == 0,
	mem.inventory["Tools"][0]["ID"] == 0x05b,
	delta(mem.inventory["Tools"][0]["Amount"]) == 0,
	mem.inventory["Tools"][0]["Amount"] == 1
])
ach_set.add_achievement(ach_igoggles)

ach_pocketmoney = Achievement(id=625368, badge=0, title="Don't Spend It All at Once",
	description="Receive a reward from Karu for gifting him pocket money",
	points=1, type=None)
ach_pocketmoney.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Mado Garage"],
	mem.movable == value(1)
])
ach_pocketmoney.add_alt(dialogue_logic(0x4b7c, 0x4be4, Region.EN))
ach_pocketmoney.add_alt(dialogue_logic(0x2e4a, 0x2e84, Region.JP))
ach_set.add_achievement(ach_pocketmoney)

ach_dogs = Achievement(id=625369, badge=0, title="Free to a Good Home",
	description="Bring all of the dogs from Dog Village to the old man in the greenhouse in Mado",
	points=2, type=AchievementType.MISSABLE)
ach_dogs.add_core([
	pause_if(~SAVE_PROTECTION),
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

ach_modders = Achievement(id=625523, badge=0, title="Pit Crew",
	description="Send every vehicle specialist to Nile's Garage in Mado",
	points=5, type=None)
ach_modders.add_core([
	pause_if(~SAVE_PROTECTION),
	partial_bitcount(0x0019e9d7, range(0, 3), is_delta=True),
	partial_bitcount(0x0019e9d8, range(5, 8), is_delta=True, count=5),
	partial_bitcount(0x0019e9d7, range(0, 3)),
	partial_bitcount(0x0019e9d8, range(5, 8), count=6, measured=Measured.MEASURED),
])
ach_set.add_achievement(ach_modders)

ach_dogsystem = Achievement(id=625524, badge=0, title="Every Dog Has Its System",
	description="Register every location into the Dog System for use as fast travel",
	points=5, type=None)
ach_dogsystem.add_core([
	pause_if(~SAVE_PROTECTION),
	partial_bitcount(0x0019e90d, range(0, 3), is_delta=True),
	add_source(delta(bitcount(0x0019e90e))),
	add_source(delta(bitcount(0x0019e90f))),
	partial_bitcount(0x0019e910, [6, 7], is_delta=True, count=20),
	partial_bitcount(0x0019e90d, range(0, 3)),
	add_source(bitcount(0x0019e90e)),
	add_source(bitcount(0x0019e90f)),
	partial_bitcount(0x0019e910, [6, 7], count=21, measured=Measured.MEASURED),
])
ach_set.add_achievement(ach_dogsystem)

ach_vending = Achievement(id=625370, badge=0, title="Your Lucky Day",
	description="Win a prize from a vending machine", points=2, type=None)
ach_vending.add_core([
	SAVE_PROTECTION,
	mem.game_state == value(2),
	prior(mem.vending.spin) == value(1),
	mem.vending.spin == value(0),
	delta(mem.vending.win) == value(0),
	mem.vending.win == value(1)
])
ach_set.add_achievement(ach_vending)

ach_noguchi = Achievement(id=625525, badge=0, title="Not a Placebo",
	description="Take a sample from the production line at Noguchi Chemicals",
	points=2, type=None)
ach_noguchi.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Noguchi B1F"],
	bit5(0x0019e9e0) == value(1),
	delta(bit5(0x0019e9a3)) == value(1),
	bit5(0x0019e9a3) == value(0)
])
ach_set.add_achievement(ach_noguchi)

ach_lovemachine = Achievement(id=625860, badge=0, title="Peace, LOVE, Unity, Respect",
	description="Register all ICs into the LOVE Machine", points=10, type=None)
ach_lovemachine.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Love Piece 2F"],
	bit4(0x0019e75e) == value(1),
	add_source(delta(bitcount(0x0019e81e))),
	partial_bitcount(0x0019e81f, range(4, 8), is_delta=True, count=11),
	add_source(bitcount(0x0019e81e)),
	partial_bitcount(0x0019e81f, range(4, 8), count=12, measured=Measured.MEASURED)
])
ach_set.add_achievement(ach_lovemachine)

ach_metaldetector = Achievement(id=625551, badge=0, title="All That Glitters",
	description='Reveal 100 items using a Metal Detector, earning the title of "Detector Ironman"',
	points=5, type=None)
ach_metaldetector.add_core([
	pause_if(~SAVE_PROTECTION),
	delta(bit3(0x0019e75e)) == value(0),
	bit3(0x0019e75e) == value(1),
	delta(mem.detector_count) < value(100),
	measured(mem.detector_count >= value(100)),
	measured_if(mem.detector_count > delta(mem.detector_count))
])
ach_set.add_achievement(ach_metaldetector)

ach_shellcraft = Achievement(id=625552, badge=0, title="World of Shellcraft",
	description='Craft 100 shells using the Artist ability Craft Shell, earning the title of "Artistic Demon"',
	points=5)
ach_shellcraft.add_core([
	pause_if(~SAVE_PROTECTION),
	delta(bit1(0x0019e75e)) == value(0),
	bit1(0x0019e75e) == value(1),
	remember(delta(mem.shell_count) / value(2)),
	recall() == value(99),
	remember(mem.shell_count / value(2)),
	measured(recall() == value(100)),
	measured_if(mem.shell_count > delta(mem.shell_count))
])
ach_set.add_achievement(ach_shellcraft)

ach_millionaire = Achievement(id=626089, badge=0, title="Post-Apocalyptic Monopolist",
	description='Reach 10,000,000G, earning the title of "Millionaire"',
	points=10, type=None)
ach_millionaire.add_core([
	SAVE_PROTECTION,
	delta(bit4(0x0019e760)) == value(0),
	bit4(0x0019e760) == value(1),
	delta(mem.money) < value(10000000),
	mem.money >= value(10000000)
])
ach_set.add_achievement(ach_millionaire)

ach_furniture = Achievement(id=626090, badge=0, title="Extreme Makeover: Wasteland Edition",
	description='Spend 100,000G buying furniture for your girlfriends, earning the title of "Spending Boyfriend"',
	points=4, type=None)
ach_furniture.add_core([
	SAVE_PROTECTION,
	delta(bit5(0x0019e75e)) == value(0),
	bit5(0x0019e75e) == value(1),
	remember(delta(mem.furniture_bought) / value(2)),
	recall() < value(100000),
	remember(mem.furniture_bought / value(2)),
	measured(recall() >= value(100000)),
	measured_if(mem.furniture_bought > delta(mem.furniture_bought))
])
ach_set.add_achievement(ach_furniture)

ach_stamps = Achievement(id=626117, badge=0, title="Prolific Philatelist",
	description="Receive a total of 10,000 stamps by selling items to the Mado Stamp Shop, earning the W-Tornado Cannon",
	points=5, type=None)
ach_stamps.add_core([
	SAVE_PROTECTION,
	mem.current_map == maps["Mado Garage"],
	mem.movable == value(1),
	delta(mem.stamps) < 10000,
	mem.stamps >= 10000 
])
ach_set.add_achievement(ach_stamps)

ach_rental = Achievement(id=626118, badge=0, title="Rising Insurance Premiums",
	description='Pay 10,000G in Rental Tank fees, earning the title of "Rich No-Refunder"',
	points=4, type=None)
ach_rental.add_core([
	SAVE_PROTECTION,
	bit6(0x0019e75f) == value(1),
	delta(bit5(0x0019e75f)) == value(0),
	bit5(0x0019e75f) == value(1),
	remember(delta(mem.rental_fees) * value(2)),
	recall() < value(10000),
	remember(mem.rental_fees * value(2)),
	measured(recall() >= value(10000)),
	measured_if(mem.rental_fees > delta(mem.rental_fees))
])
ach_set.add_achievement(ach_rental)

# No flag for beating them while tending the shop, so we have to detect them being defeated in combat
ach_pichistore = Achievement(id=625372, badge=0, points=2, type=AchievementType.MISSABLE,
	title="Pichi Pichi on the Job", description="Defeat the Pichi Pichi Brothers while tending the ill trader's shop")
ach_pichistore.add_core(combat_logic(maps["Trader Camp (Shopkeep) Left Tent"], (0x15e, 0x15d)))
ach_set.add_achievement(ach_pichistore)

ach_garcia = Achievement(id=625373, badge=0, title="Unrequited Animosity",
	description="Defeat Garcia in a duel atop of Swan", points=10, type=None)
ach_garcia.add_core(combat_logic(maps["Swan Outside"], 0x136))
ach_set.add_achievement(ach_garcia)

ach_marriage = Achievement(id=625374, badge=0, title="Someone Else to Live For", points=1, type=None,
	description="Marry and settle down, moving on from your quest for vengeance")
ach_marriage.add_core(SAVE_PROTECTION)
ach_marriage.add_core(add_maps((maps["Mado Garage"], maps["Bennett's House"], maps["Islaporto Sewers"])))
ach_marriage.add_core([
	delta(mem.game_state) == value(1),
	mem.game_state == value(4)
])
ach_set.add_achievement(ach_marriage)


###############
# Leaderboards
lb_tanks = Leaderboard(id=167853, title="Bang Bang Tanks! - High Score",
	description="Achieve the highest score in Bang Bang Tanks!",
	format=LeaderboardFormat.VALUE)
lb_tanks.set_start([
	SAVE_PROTECTION,
	mem.game_state == value(2),
	mem.tanks.active(),
	delta(mem.tanks.state) == value(1),
	mem.tanks.state == value(0)
])
lb_tanks.set_cancel(always_false())
lb_tanks.set_submit(always_true())
lb_tanks.set_value(measured(mem.tanks.score))
ach_set.add_leaderboard(lb_tanks)

ach_set.save(path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")
