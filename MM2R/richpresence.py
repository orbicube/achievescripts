from pycheevos.core.helpers import byte, word, dword
from pycheevos.models.rich_presence import RichPresence
rp = RichPresence()

rp.add_lookup("Map", {
	0x0: "Overworld",
	range(0x6, 0x18): "Mado",
	range(0x1a, 0x28): "El Niño",
	range(0x28, 0x35): "Hatoba",
	range(0x35, 0x3c): "Bazaarska",
	range(0x3c, 0x48): "Azusa",
	range(0x48, 0x65): "Delta Rio",
	range(0x65, 0x79): "Islaporto",
	range(0x79, 0x7d): "Swan",
	range(0x7e, 0x8a): "Taisha",
	range(0x8b, 0x8f): "Moro Poco",
	range(0x8f, 0x97): "Deathcruz",
	range(0x97, 0x9a): "Melt-town",
	0x9a: "Rain Valley",
	[0x9c, 0x9d]: "Nameless Bar",
	range(0x9e, 0xa1): "Bay Bridge",
	range(0xa1, 0xa4): "Dog Village"
	range(0xa5, 0xa8): "Forest Watchtower",
	[0xad, 0xae]: "Bar Thirsty",
	range(0xc2, 0xc5): "Staff Housing",
	[0xd0, 0xd1]: "Bato Lab",
	range(0xe0, 0xef): "Helmets Island",
	range(0xef, 0xf8): "Buried Building",
	[0xf8, 0xf9]: "Bennett's House",
	0xfa: "Hoc's Trading Site",
	[0xfb, 0xfc]: "Villain Museum",
	[0x105, 0x106]: "Vending Paradise"
	[0x107, 0x108]: "Sewer Management",
	range(0x109, 0x10d): "Giant Ant Cave",
	range(0x10d, 0x114): "Vlad Museum",
	range(0x114, 0x121): "Grappler Tower",
	range(0x121, 0x125): "Protein Palace",
	range(0x126, 0x12d): "Dark Canal",
	range(0x12e, 0x134): "Wind Farm",
	0x134: "Deathcruz",
	range(0x135, 0x140): "Deadend Cave",
	range(0x13a, 0x146): "Devil Island"
	0x146: "Melt-town"
	range(0x147, 0x162): "Bias City",
	range(0x167, 0x176): "Hotel Nadir",
	range(0x177, 0x182): "Freak Island",
	range(0x182, 0x188): "Eternal Gate",
	[0x1ae, 0x1af]: "Witch's Tent"
	#range(0x188, 0x1a3): "Trader Camp",
	#0x1a2: "Abandoned Camp"
})

rp.add_lookup("Job", {
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

mem_map = dword(0x00119740)
mem_party = [
	byte(0x00194882),
	byte(0x00194883),
	byte(0x00194884),
	byte(0x00194885)
]
mem_stat_base = 0x00195dbc
mem_ngp = byte(0x001aa3e4)
mem_diff = byte(0x0019483d)
mem_state = dword(0x00119750)

char_offset = 0xc4
job_offset = 0x0c
level_offset = 0x12

def char_info(slot, offset):
	return f"I:{mem_party[slot]}*{char_offset}_M:{byte(mem_stat_base+offset)}"

def party_info(party_size):
	chars = []
	for slot in range(0, party_size):
		chars.append(f"Lv. @Number({char_info(slot, level_offset)}) @Job({char_info(slot, job_offset)})")

	return ", ".join(chars)

rp.add_display([mem_map >= 0xfffe], "On the Title Screen")

for i in range(1,4):
	rp.add_display([mem_party[i] == 0xff, mem_ngp > 0], f"NG+@Number({mem_ngp})@Difficulty({mem_diff}) | 🗺️@Map({mem_map}) | {party_info(i)}")
	rp.add_display([mem_party[i] == 0xff], f"🗺️@Map({mem_map}) | {party_info(i)}")

rp.add_display([mem_map < 0xffff], f"🗺️@Map({mem_map}) | {party_info(4)}")

rp.add_display([], "Crawling the wastes")

rp.save(game_id=24022, title="MM2R RP", path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")