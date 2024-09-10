import time
import datetime
import re
import numpy as np
import globals

g = globals.get_globals()




def timestamp():
	return datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")

def clean_llm_artefacts(prompt):
	"""
	Cleans potential artefacts (artifacts) left behind by large language models (LLMs) from a given prompt.

	This function specifically removes two common artefacts:

		* Newline character at the beginning: This can occur when LLMs generate text that starts on a new line.
		* "Answer: " prefix: This might be added by some LLMs as a prefix to their generated response.

	Args:
		prompt (str): The prompt text to be cleaned.

	Returns:
		str: The cleaned prompt text without the identified artefacts.
	"""
	unfixed = prompt
	prompt = repair_brackets(prompt)
	if prompt == '':
		prompt = unfixed

	prompt = re.sub(r"\s+", " ", prompt)
	if '\n' in prompt:
		prompt = re.sub(r'.*\n', '', prompt)

	artefacts = ['Answer: ','Steps: ','scale: ', 'Seed: ', 'Face restoration: ', 'Size: ', 'Model hash: ', 'Model: ', 'Clip skip: ',
				 'Token merging ratio: ', 'ADetailer .*?: ','"','\[', '\]', '\{', '\}']

	for artefact in artefacts:
		if artefact in prompt:
			prompt = re.sub(rf'.*{artefact}', '', prompt)

	pattern = r"<\|(.*?)\|>"
	prompt = re.sub(pattern, "", prompt)
	pattern = r"<(.*?)>"
	prompt = re.sub(pattern, "", prompt)

	return prompt

def repair_brackets(txt):
	# split the text into words
	words = txt.split()
	# create an empty list to store the repaired words
	repaired_words = []
	# iterate over the words
	for word in words:
		# check if the word starts with a bracket
		if word.startswith('('):
			# check if the word ends with a bracket
			# there might be  punctuation marks in the word that are not brackets
			# check for that situation to not add opening bracket because the word does not end exactly with a closing bracket but a closing bracket is present
			if word.endswith(')'):
				# if the word starts and ends with a bracket, append the word to the repaired words list

				repaired_words.append(word)
			else:
				# if the word starts with a bracket but does not end with a bracket, append the word with a closing bracket to the repaired words list
				# check if there is  punctuation mark in the word
				# the bracket has to be at the end of the word but before the  punctuation mark
				# the bracket has to be at the end of the word if there is no  punctuation mark
				if word[-1] in ',.!?':
					# if there is a  punctuation mark in the word, append the word with a closing bracket before the  punctuation mark to the repaired words list
					repaired_words.append(word[:-1] + ')' + word[-1])
				else:
					# if there is no  punctuation mark in the word, append the word with a closing bracket to the repaired words list
					repaired_words.append(word + ')')

		# check if the word ends with a bracket
		# or with a bracket and a  punctuation mark

		elif word.endswith(')'):

			# if the word ends with a bracket but does not start with a bracket, append the word with an opening bracket to the repaired words list
			# but check for if there is a  punctuation mark in the word
			# the bracket has to be at the start of the word but after the  punctuation mark
			# the bracket has to be at the start of the word if there is no  punctuation mark
			if word[0] in ',.!?':
				# if there is a  punctuation mark in the word, append the word with an opening bracket before the  punctuation mark to the repaired words list
				repaired_words.append(word[0] + '(' + word[1:])
			else:
				# if there is no  punctuation mark in the word, append the word with an opening bracket to the repaired words list
				repaired_words.append('(' + word)
		# elif word ends with ),.!?:
		# if the word ends with a bracket and a  punctuation mark, append the word with an opening bracket before the  punctuation mark to the repaired words list
		# the bracket has to be at the start of the word but after the  punctuation mark
		elif word[-1] in ',.!?':
			if ')' in word:
				repaired_words.append('(' + word[:-1] + word[-1])
			else:
				repaired_words.append(word)
		else:
			# if the word does not start or end with a bracket, append the word to the repaired words list
			repaired_words.append(word)
	# join the repaired words list into a repaired text
	repaired_txt = ' '.join(repaired_words)
	# return the repaired text
	return repaired_txt





def repair_brackets_snipets(text):
	# split the text into a list of characters
	text = list(text)
	out_text = list(text)
	# create a stack to store the indexes of the brackets
	stack = []
	# iterate over the characters in the text
	# create an array of the text

	for i, char in enumerate(text):
		# if the character is an opening bracket
		if char == '(':
			# add the index to the stack
			stack.append(i)
		# if the character is a closing bracket
		elif char == ')':
			# if the stack is not empty
			if stack:
				# pop the last index from the stack
				stack.pop()
			# if the stack is empty
			else:
				# add an opening bracket to the beginning of the text
				out_text.insert(0, '(')

	# iterate over the indexes in the stack
	for i in stack:
		# add a closing bracket at the end of the text
		out_text.append(')')
	# join the characters back into a string
	return ''.join(out_text)


def fix_array_brackets(text):
	out = []
	for word in text:
		if word != '':
			out.append(repair_brackets_snipets(word.strip()))

	return out

def get_negative_prompt():

	negative_out = ''
	if len(g.negative_prompt_list) > 0:

		negative_prompt = fix_array_brackets(g.negative_prompt_list)
		g.last_negative_prompt = ','.join(negative_prompt)

		if len(g.last_negative_prompt) < 30:
			g.last_negative_prompt = g.settings_data['negative_prompt']
		if g.last_negative_prompt != '':
			negative_out = g.last_negative_prompt
	else:
		negative_out = g.settings_data['negative_prompt']

	return negative_out

def check_filtered(prompt):

	not_check = False
	check = False
	if len(g.settings_data['sail_filter_not_text']) > 0:
		not_check = True
		check_count = 0
		search = set(word.strip().lower() for word in g.settings_data['sail_filter_not_text'].split(','))
		for word in search:
			if word in prompt:
				check_count += 1
		if check_count == len(search):
			not_check = False


	if len(g.settings_data['sail_filter_text']) > 0:
		search = set(word.strip().lower() for word in g.settings_data['sail_filter_text'].split(','))
		check_count = 0
		for word in search:
			if word in prompt:
				check_count += 1
		if check_count == len(search):
			check = True


	return not_check + check


def is_image_black(image):
	"""
	Check if a PIL image is completely black.

	Parameters:
	image (PIL.Image): The image to check.

	Returns:
	bool: True if the image is completely black, False otherwise.
	"""
	# Convert the image to a NumPy array
	image_array = np.array(image)

	# If the image has an alpha channel, ignore the alpha channel in the comparison
	if image_array.shape[-1] == 4:
		image_array = image_array[:, :, :3]

	# Check if all values in the array are 0 (black)
	return np.all(image_array == 0)

def sanitize_path_component(component, replacement='_'):
	"""
	Sanitizes a string to make it a valid file path component.

	Parameters:
	- component (str): The string to sanitize.
	- replacement (str): The string to replace invalid characters with. Default is '_'.

	Returns:
	- str: The sanitized string.
	"""
	# List of invalid characters for Windows
	invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'

	# Replace invalid characters with the specified replacement
	sanitized = re.sub(invalid_chars, replacement, component)

	# Trim leading and trailing spaces
	sanitized = sanitized.strip()

	return sanitized

def to_utf8_string(text):
	cleaned_text = re.sub(r'[^\x00-\x7F]+', '?', text)
	try:
		return cleaned_text.encode('utf-8').decode('utf-8')
	except UnicodeDecodeError:
		# Return encoded bytes on error (may contain invalid characters)
		return 'text did contain non utf8 convertible data, therefore lets make a cute kitten prompt'


