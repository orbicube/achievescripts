from pycheevos.core.helpers import *
from pycheevos.core.constants import *
from pycheevos.models.achievement import Achievement
from pycheevos.models.set import AchievementSet

from enum import Enum
import collections

from memory import Memory
mem = Memory()

ach_set = AchievementSet(game_id = 24022, title = "Metal Max 2: Reloaded")

maps = {
	"Mado Garage": 0x9,
	"Hatoba Hunt Office": 0x2a,
	"Nameless Bar": 0x9c,
	"Villain Museum": 0xfb
}

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

def partial_bitcount(addr: int, bits: collections.abc.Iterable[int], is_delta: bool = False, 
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


# Quests/Flag-based Achievements
ach_quests = [ #ID, Badge, Title, Description, Achievement Points, Type, Flag Address, Map ID, Extra Flags
	(0, 0, "Curry Powder", "Fulfil Irit's culinary curiosity by giving her a Cookbook and Curry Powder",
		2, None, bit3(0x0019e93a), maps["Mado Garage"], None),
	(0, 0, "Antares", "Hunt Antares for a Hunter in a bar east of Mado, receiving the keys to a vehicle as your reward",
		4, None, bit5(0x0019e925), maps["Nameless Bar"], None)
]
for ach_id, badge, title, desc, points, type, addr, map_id, flags in ach_quests:
	ach = Achievement(id=ach_id, title=title, description=desc, points=points, type=type)
	ach.add_core([
		(mem.CURRENT_MAP == map_id),
		(delta(addr) == 0),
		(addr == 1)
	])

	ach_set.add_achievement(ach)

# Enemy Bounties
bounty_types = []
ach_bounties = [
	(None, None, "Sand Shark", "Defeat the Sand Shark in the desert east of Mado",
		3, None, bit3(0x0019e8bb))
]

# Challenge Hunts
ach_hunts = [ #ID, Badge, Title, Description Override, Achievement Points, Hunts Required
	(0, 0, "Clear 10 Challenge Hunts", 'Clear 10 Challenge Hunts, earning the title of "Challenger"', 5, 10),
	(0, 0, "Clear 20 Challenge Hunts", '', 5, 20),
	(0, 0, "Clear 30 Challenge Hunts", '', 10, 30),
	(0, 0, "Clear 40 Challenge Hunts", '', 10, 40),
	(0, 0, "Clear All Challenge Hunts", 'Clear all 56 Challenge Hunts', 25, 56)
]
for ach_id, badge, title, desc, points, hunts_req in ach_hunts:
	if not desc:
		desc = f"Clear {hunts_req} Challenge Hunts"
	ach = Achievement(id=ach_id, title=title, description=desc, points=points, type=None)

	# Only two maps where you can hand in Challenge Hunts
	logic = [(mem.CURRENT_MAP == maps["Hatoba Hunt Office"]) | (mem.CURRENT_MAP == maps["Villain Museum"])]

	# Delta bitcounts for hunt clear flags
	# First byte uses bits 0-6
	logic.extend(
		partial_bitcount(0x0019e9ba, range(0, 7), is_delta=True))

	# 6 full bytes of bits
	for addr in range(0x0019e9bb, 0x0019e9c1):
		logic.append(
			add_source(delta(bitcount(addr))))

	# Last byte uses only bit7
	# Since hunts can only increment by 1, we check if it's 1 less than goal
	logic.append(
		(delta(bit7(0x0019e9c1)) == hunts_req - 1))

	# Current memory bitcounts, same addresses as above
	logic.extend(
		partial_bitcount(0x0019e9ba, range(0, 7)))

	for addr in range(0x0019e9bb, 0x0019e9c1):
		logic.append(
			add_source(bitcount(addr)))
	logic.append(
		(measured(bit7(0x0019e9c1) == hunts_req)))

	ach.add_core(logic)
	ach_set.add_achievement(ach)

ach_set.save(path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")