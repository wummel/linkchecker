#
# CSV 0.17  8 June 1999    Copyright ©Laurence Tratt 1998 - 1999
# e-mail: tratt@dcs.kcl.ac.uk
# home-page: http://eh.org/~laurie/comp/python/csv/index.html
#
#
#
# CSV.py is copyright ©1998 - 1999 by Laurence Tratt
#
# All rights reserved
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted, provided that
# the above copyright notice appear in all copies and that both that copyright
# notice and this permission notice appear in supporting documentation.
#
# THE AUTHOR - LAURENCE TRATT - DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
# SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL THE AUTHOR FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
# AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTUOUS ACTION, ARISING OUT OF OR
# IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#





import re, string, types, UserList





###################################################################################################
#
# CSV class
#


class CSV(UserList.UserList):

	""" Manage a CSV (comma separated values) file

        The data is held in a list.
    
        Methods:
          __init__()
          load()    load from file
          save()    save to file
          input()   input from string
          output()  save to string
          append()  appends one entry
          __str__() printable represenation
	"""



	def __init__(self, separator = ','):

		""" Initialise CVS class instance.

            Arguments:
              separator        : The field delimiter. Defaults to ','
        """

		self.separator = separator

		self.data = []
		self.fields__title__have = self.fields__title = None



	def load(self, file__data__name, fields__title__have, convert_numbers = 0, separator = None, comments = None):

		""" Load up a CSV file

            Arguments:
              file__data__name    : The name of the CSV file
              fields__title__have : 0         : file has no title fields
                                    otherwise : file has title fields
              convert_numbers     : 0         : store everything as string's
                                    otherwise : store fields that can be converted
                                                to ints or floats to that Python
                                                type defaults to 0
              separator           : The field delimiter (optional)
              comments            : A list of strings and regular expressions to remove comments
		"""

		file__data = open(file__data__name, 'r')
		self.input(file__data.read(-1), fields__title__have, convert_numbers, separator or self.separator, comments or ["#"])
		file__data.close()



	def save(self, file__data__name, separator = None):

		""" Save data to CSV file.

            Arguments:
              file__data__name : The name of the CSV file to save to
              separator        : The field delimiter (optional)
		"""

		file__data = open(file__data__name, 'w')
		file__data.write(self.output(separator or self.separator))
		file__data.close()



	def input(self, data, fields__title__have, convert_numbers = 0, separator = None, comments = None):

		""" Take wodge of CSV data & convert it into internal format.

            Arguments:
              data                : A string containing the CSV data
              fields__title__have : 0         : file has no title fields
                                    otherwise : file has title fields
              convert_numbers     : 0         : store everything as string's
                                    otherwise : store fields that can be
                                                converted to ints or
                                                floats to that Python type
                                                defaults to 0
              separator           : The field delimiter (Optional)
              comments            : A list of strings and regular expressions to remove comments
                                      (defaults to ["#"])
		"""

		def line__process(line, convert_numbers, separator):

			fields = []
			line__pos = 0
				
			while line__pos < len(line):

				# Skip any space at the beginning of the field (if there should be leading space,
				#   there should be a " character in the CSV file)

				while line__pos < len(line) and line[line__pos] == " ":
					line__pos = line__pos + 1

				field = ""
				quotes__level = 0
				while line__pos < len(line):

					# Skip space at the end of a field (if there is trailing space, it should be
					#   encompassed by speech marks)

					if quotes__level == 0 and line[line__pos] == " ":
						line__pos__temp = line__pos
						while line__pos__temp < len(line) and line[line__pos__temp] == " ":
							line__pos__temp = line__pos__temp + 1
						if line__pos__temp >= len(line):
							break
						elif line[line__pos__temp : line__pos__temp + len(separator)] == separator:
							line__pos = line__pos__temp
					if quotes__level == 0 and line[line__pos : line__pos + len(separator)] == separator:
						break
					elif line[line__pos] == "\"":
						if quotes__level == 0:
							quotes__level = 1
						else:
							quotes__level = 0
					else:
						field = field + line[line__pos]
					line__pos = line__pos + 1
				line__pos = line__pos + len(separator)
				if convert_numbers:
					for char in field:
						if char not in "0123456789.-":
							fields.append(field)
							break
					else:
						try:
							if "." not in field:
								fields.append(int(field))
							else:
								fields.append(float(field))
						except:
							fields.append(field)
				else:
					fields.append(field)
			if line[-len(separator)] == separator:
				fields.append(field)

			return fields


		separator = separator or self.separator
		comments = comments or ["#"]

		self.fields__title__have = fields__title__have

		# Remove comments from the input file

		comments__strings = []
		for comment in comments:
			if type(comment) == types.InstanceType:
				data = comment.sub("", data)
			elif type(comment) == types.StringType:
				comments__strings.append(comment)
			else:
				raise Exception("Invalid comment type '" + comment + "'")

		lines = map(string.strip, string.split(data, "\n"))

		# Remove all comments that are of type string

		lines__pos = 0
		while lines__pos < len(lines):
			line = lines[lines__pos]
			line__pos = 0
			while line__pos < len(line) and line[line__pos] == " ":
				line__pos = line__pos + 1
			found_comment = 0
			for comment in comments__strings:
				if line__pos + len(comment) < len(line) and line[line__pos : line__pos + len(comment)] == comment:
					found_comment = 1
					break
			if found_comment:
				del lines[lines__pos]
			else:
				lines__pos = lines__pos + 1

		# Process the input data

		if fields__title__have:
			self.fields__title = line__process(lines[0], convert_numbers, separator)
			pos__start = 1
		else:
			self.fields__title = []
			pos__start = 0
		self.data = []
		for line in lines[pos__start : ]:
			if line != "":
				self.data.append(Entry(line__process(line, convert_numbers, separator), self.fields__title))



	def output(self, separator = None):

		""" Convert internal data into CSV string.

            Arguments:
              separator        : The field delimiter (optional)

            Returns:
              String containing CSV data
		"""

		separator = separator or self.separator


		def line__make(entry, separator = separator):

			str = ""
			done__any = 0
			for field in entry:
				if done__any:
					str = str + separator
				else:
					done__any = 1
				if type(field) != types.StringType:
					field = `field`
				if len(field) > 0 and (string.find(field, separator) != -1 or (field[0] == " " or field[-1] == " ")):
					str = str + "\"" + field + "\""
				else:
					str = str + field

			return str


		if self.fields__title__have:
			str = line__make(self.fields__title) + "\n\n"
		else:
			str = ""
		str = str + string.join(map(line__make, self.data), "\n") + "\n"

		return str



	def append(self, entry):
	
		""" Add an entry. """

		if self.fields__title:
			entry.fields__title = self.fields__title
		self.data.append(entry)



	def field__append(self, func, field__title = None):

		""" Append a field with values specified by a function

            Arguments:
              func         : Function to be called func(entry) to get the value of the new field
              field__title : Name of new field (if applicable)

        """

		for data__pos in range(len(self)):
			entry = self.data[data__pos]
			entry.append(func(entry))
			self.data[data__pos] = entry

		if self.fields__title__have:
			self.fields__title.append(field__title)



	def duplicates__eliminate(self):

		""" Eliminate duplicates (this may result in a reordering of the entries) """

		# To eliminate duplicates, we first get Python to sort the list for us; then all we have to
		#   do is to check to see whether consecutive elements are the same, and delete them
		# This give us O(<sort>) * O(n) rather than the more obvious O(n * n) speed algorithm

		# XXX Could be done more efficiently for multiplicate duplicates by deleting a slice of
		#       similar elements rather than deleting them individually

		self.sort()
		data__pos = 1
		entry__last = self.data[0]
		while data__pos < len(self.data):
			if self.data[data__pos] == entry__last:
				del self.data[data__pos]
			else:
				entry__last = self.data[data__pos]
				data__pos = data__pos + 1



	def __str__(self):

		""" Construct a printable representation of the internal data. """

		columns__width = []

		# Work out the maximum width of each column

		for column in range(len(self.data[0])):
			if self.fields__title__have:
				width = len(`self.fields__title[column]`)
			else:
				width = 0
			for entry in self:
				width__possible = len(`entry.data[column]`)
				if width__possible > width:
					width = width__possible
			columns__width.append(width)

		if self.fields__title__have:
			str = string.join(map(string.ljust, self.fields__title, columns__width), "  ") + "\n\n"
		else:
			str = ""
		for entry in self:
			str = str + string.join(map(string.ljust, map(lambda a : (type(a) == types.StringType and [a] or [eval("`a`")])[0], entry.data), columns__width), "  ") + "\n"

		return str



###################################################################################################
#
# CSV data entry class
#
#


class Entry(UserList.UserList):

	""" CSV data entry, UserList subclass.

        Has the same properties as a list, but has a few dictionary
        like properties for easy access of fields if they have titles.
    
        Methods(Override):
          __init__
          __getitem__
          __setitem__
          __delitem__
	"""



	def __init__(self, fields, fields__title = None):
	
		""" Initialise with fields data and field title.

            Arguments:
              fields        : a list containing the data for each field
                              of this entry
              fields__title : a list with the titles of each field
                              (an empty list means there are no titles)
		"""

		self.data = fields
		if fields__title != None:
			self.fields__title = fields__title
		else:
			self.fields__title = []



	def __getitem__(self, x):

		if type(x) == types.IntType:
			return self.data[x]
		else:
			return self.data[self.fields__title.index(x)]



	def __setitem__(self, x, item):

		if type(x) == types.IntType:
			self.data[x] = item
		else:
			self.data[self.fields__title.index(x)] = item



	def __delitem__(self, x):

		if type(x) == types.IntType:
			del self.data[x]
		else:
			del self.data[self.fields__title.index(x)]



	def __str__(self):

		return `self.data`