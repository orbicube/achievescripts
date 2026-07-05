from pycheevos.core.helpers import byte, word, dword
from pycheevos.models.rich_presence import RichPresence
rp = RichPresence()

rp.add_lookup("Map", {
	0x0: "Overworld",
	range(0x6, 0x17): "Mado",
	range(0x1a, 0x27): "El Niño",
	range(0x28, 0x34): "Hatoba",
	range(0x35, 0x3b): "Bazaarska",
	range(0x3c, 0x47): "Azusa",
	range(0x79, 0x7d): "Swan",
	range(0x8f, 0x96): "Deathcruz",
	range(0x97, 0x99): "Melt-town",
	range(0x115, 0x120): "Grappler Tower",
	range(0x147, 0x161): "Bias City",
	range(0x182, 0x187): "Eternal Gate",
	range(0x188, 0x18d): "Trader Camp",
	0x1a2: "Abandoned Camp"
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

rp.add_display([mem_map == 0xffff], "On the Title Screen")

for i in range(1,4):
	rp.add_display([mem_party[i] == 0xff, mem_ngp > 0], f"NG+@Number({mem_ngp})@Difficulty({mem_diff}) | 🗺️@Map({mem_map}) | {party_info(i)}")
	rp.add_display([mem_party[i] == 0xff], f"🗺️@Map({mem_map}) | {party_info(i)}")

rp.add_display([mem_map < 0xffff], f"🗺️@Map({mem_map}) | {party_info(4)}")

rp.add_display([], "Crawling the wastes")

rp.save(game_id=24022, title="MM2R RP", path="D:\\Games\\Emulation\\Emulators\\RALibertro\\RACache\\Data")