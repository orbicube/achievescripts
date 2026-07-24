from pycheevos.core.helpers import byte, word, dword
from pycheevos.models.rich_presence import RichPresence

from memory import Memory
mem = Memory()

rp = RichPresence()

rp.add_lookup("Map", {
	0x0: "Overworld",
	range(0x6, 0x1a): "Mado",
	range(0x1a, 0x28): "El Niño",
	range(0x28, 0x35): "Hatoba",
	range(0x35, 0x3c): "Bazaarska",
	range(0x3c, 0x48): "Azusa",
	range(0x48, 0x65): "Delta Rio",
	range(0x65, 0x79): "Islaporto",
	range(0x79, 0x7e): "Swan",
	range(0x7e, 0x8b): "Taisha",
	range(0x8b, 0x8f): "Moro Poco",
	range(0x8f, 0x97): "Deathcruz",
	range(0x97, 0x9a): "Melt-town",
	0x9a: "Rain Valley",
	0x9b: "Lone Man's House",
	(0x9c, 0x9d): "Nameless Bar",
	range(0x9e, 0xa1): "Bay Bridge",
	range(0xa1, 0xa5): "Dog Village",
	range(0xa5, 0xa8): "Forest Watchtower",
	range(0xa9, 0xac): "Bito's Tunnel",
	0xac: "Dud Shell Shop",
	(0xad, 0xae): "Bar Thirsty",
	range(0xaf, 0xb3): "Nobotoke Village",
	range(0xb3, 0xb8): "Beihab Island",
	range(0xb8, 0xbb): "Water Bypass",
	(0xbd, 0xbe): "Oil Drilling Site",
	range(0xc0, 0xc2): "Philosophy Pond",
	range(0xc2, 0xc5): "Staff Housing",
	range(0xc5, 0xc9): "Love Piece",
	(0xc9, 0xca): "Blue Moon House",
	range(0xcb, 0xce): "Monkey Center",
	0xce: "North Gate",
	0xcf: "South Gate",
	(0xd0, 0xd1): "Bato Lab",
	(0xd2, 0xd3): "Human Village",
	(0xd4, 0xd5): "Caterpillar Villa",
	range(0xd6, 0xda): "Noguchi Chemicals",
	range(0xda, 0xdd): "Ship",
	range(0xe0, 0xef): "Helmets Island",
	range(0xef, 0xf8): "Buried Building",
	(0xf8, 0xf9): "Bennett's House",
	0xfa: "Hoc's Trading Site",
	(0xfb, 0xfc): "Villain Museum",
	range(0xfd, 0x102): "Salon du Princess",
	range(0x102, 0x105): "Space Parts Lab",
	(0x105, 0x106): "Vending Paradise",
	(0x107, 0x108): "Sewer Management",
	range(0x109, 0x10d): "Giant Ant Cave",
	range(0x10d, 0x114): "Vlad Museum",
	range(0x114, 0x121): "Grappler Tower",
	range(0x121, 0x125): "Protein Palace",
	range(0x126, 0x12d): "Dark Canal",
	range(0x12e, 0x134): "Wind Farm",
	0x134: "Deathcruz",
	range(0x135, 0x13a): "Deadend Cave",
	range(0x13a, 0x146): "Devil Island",
	0x146: "Melt-town",
	range(0x147, 0x162): "Bias City",
	range(0x162, 0x167): "Ruined Building",
	range(0x167, 0x176): "Hotel Nadir",
	range(0x177, 0x182): "Freak Island",
	range(0x182, 0x188): "Eternal Gate",
	#(0x1ae, 0x1af): "Witch's Tent"
	range(0x188, 0x1b6): "Camp",
	#0x1a2: "Abandoned Camp"
})

rp.add_lookup("Class", {
	0x0: "Hunter",
	0x1: "Mechanic",
	0x2: "Soldier",
	0x3: "Nurse",
	0x4: "Wrestler",
	0x5: "Artist",
	0x6: "Dog",
	0x7: "Money Eater"
})

rp.add_lookup("Difficulty", {
	0x0: "",
	0x1: " Hard",
	0x2: " Super Hard",
	0x3: " God Difficulty"
})

def char_info(slot, offset):
	return f"I:{mem.party[slot]}*{mem.offsets['Character']}_M:{byte(mem.char_base+offset)}"

def party_info(party_size):
	chars = []
	for slot in range(0, party_size):
		chars.append(f"Lv. @Number({char_info(slot, mem.offsets['Level'])}) @Class({char_info(slot, mem.offsets['Class'])})")

	return ", ".join(chars)

rp.add_display([mem_map >= 0xfffe], "On the Title Screen")

rp.add_display([mem.game_state == 2, mem.frog_state > 0, mem.frog_state < 11], f"Playing Ribbit Race in @Map({mem.current_map})")

for i in range(1,4):
	rp.add_display([mem.party[i] == 0xff, mem.ngplus_count > 0], f"NG+@Number({mem.ngplus_count})@Difficulty({mem.difficulty}) | @Map({mem.current_map}) | {party_info(i)}")
	rp.add_display([mem.party[i] == 0xff], f"@Map({mem.current_map}) | {party_info(i)}")

rp.add_display([mem_map < 0xfffe], f"@Map({mem.current_map}) | {party_info(4)}")

rp.add_display([], "Crawling the wastes")

rp.save(game_id=24022, title="MM2R RP", path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")