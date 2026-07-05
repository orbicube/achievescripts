#
#	Converts a simple non-pointer code note into a dict with descriptions as keys
#	Notes should be formatted as Description\r\n\0xAddress1 = Key1\r\n0xAddress2 = Key2
#	If duplicate keys, addresses will be in a List
#

import json


def note2dict(notefile: str, addr: int):
	notes = json.load(notefile)

	note = [note["Note"] for note in notes if note["Address"] == str(addr)]
	note = note[0]

	# Remove header line
	note = note.split("\r\n", 1)[1]

	note_dict = {}
	for line in note.split("\r\n"):
		val, key_str = line.split(" = ")

		if key_str in note_dict:
			if type(note_dict[key_str]) != List:
				note_dict[key_str] = [note_dict[key_str], val]
			else:
				note_dict[key_str].append(val)
		else:
			note_dict[key_str] = val

	return note_dict