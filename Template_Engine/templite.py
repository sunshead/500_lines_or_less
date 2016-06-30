#Build a Templite object
templite = Templite('''
	<h1>Hello {{name|upper}}!</h1>
	{% for topic in topics %}
		<p>You are interested in {{topic}}.</p>
	{% endfor %}
	''',
	{'upper': str.upper}.
)

#Use it to render some data.
text = templite.rendr({
	'name': "Ned",
	'topics': ['Python', 'Geometry', 'Juggling'],
	})

#A CodeBuilder object keeps a list of strings that will together be the final Python code.
class CodeBuilder(object):
	"""Build source code conviently."""

	def __init__(self, indent=0):
		self.code = []
		self.indent_level = indent

	def add_line(self, line):
		#Add a line of source to the code
		self.code.extend([" " * self.indent_level, line, "\n"])

	INDENT_STEP = 4

	def indent(self):
		#Increase the current indent for following lines.
		self.indent_level += self.INDENT_STEP

	def dedent(self):
		#Decrease the current indent for following lines.
		self.indent_level -= self.INDENT_STEP

	def add_section(self):
		#Add a section -- a sub-CodeBuilder.
		section = CodeBuilder(self.indent_level)
		self.code.append(section)
		return section

	def __str__(self):
		return "".join(str(c) for c in self.code)

	def get_globals(self):
		#Execute the code, and return a dict of globals it defines.

		#Check that the caller has finished all the blocks they started
		assert self.indent_level == 0
		#Get the Python source as a single string
		python_source = str(self)
		#Execute the source, defining globals, and return them
		global_namespace = {}
		exec(python_source, global_namespace)
		return global_namespace

class Templite:
	def __init__(self, text, *contexts):
	#Construct a Templite with given text
	#'contexts' are dictionaries of values to use for future renderings
	self.context = {}
	for context in contexts:
		self.context.update(context)

	#extract context variables into Python locals
	self.all_vars = set()
	self.loop_vars = set()

	#Use the CodeBuilder class to build the compiled function
	code = CodeBuilder()
	#'context' is the data dictionary it should use, 'do_dots' is
	#a function implementing dot attribute access
	code.add_line("def render_funtion(context, do_dots):")	
	code.indent()
	vars_code = code.add_section()
	code.add_line("result = []")
	code.add_line("append_result = result.append")
	code.add_line("extend_result = result.extend")
	code.add_line("to_str = str")

	#An inner function to help with buffering output strings
	buffered = []
	def flush_output():
		#Force 'buffered' to the code builder.
		if len(buffered) == 1:
			code.add_line("append_result(%s)" % buffered[0])
		elif len(buffered) > 1:
			code.add_line("extend_result([%s])" % ", ".join(buffered))
		del buffered[:]

ops_stack = []
# Split a string using a regex
tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)

#The compilation code is a loop over these tokens:
for token in tokens:
	if token.startswith('{#'):
		#ignore it and move on if is comment
		continue
    elif token.startswith('{{'):
        # An expression to evaluate.
        expr = self._expr_code(token[2:-2].strip())
        buffered.append("to_str(%s)" % expr)
    elif token.startswith('{%'):
        # Action tag: split into words and parse further.
        flush_output()
        words = token[2:-2].strip().split()