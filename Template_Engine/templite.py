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
        #If the tag type is 'if'
        if words[0] == 'if':
	        if len(words) != 2:
	            self._syntax_error("Don't understand if", token)
	        ops_stack.append('if')
	        code.add_line("if %s:" % self._expr_code(words[1]))
	        code.indent()
	    #If the tag type is 'for'
		elif words[0] == 'for':
	        # A loop: iterate over expression result.
	        if len(words) != 4 or words[2] != 'in':
	            self._syntax_error("Don't understand for", token)
	        ops_stack.append('for')
	        self._variable(words[1], self.loop_vars)
	        code.add_line(
	            "for c_%s in %s:" % (
	                words[1],
	                self._expr_code(words[3])
	            )
	        )
	        code.indent()
	    #If the tag type is 'end'
        elif words[0].startswith('end'):
            # Endsomething.  Pop the ops stack.
            if len(words) != 1:
                self._syntax_error("Don't understand end", token)
            end_what = words[0][3:]
            if not ops_stack:
                self._syntax_error("Too many ends", token)
            start_what = ops_stack.pop()
            if start_what != end_what:
                self._syntax_error("Mismatched end tag", end_what)
            code.dedent()
        else:
            self._syntax_error("Don't understand tag", words[0])
    #If literal content
    else:
    # Literal content.  If it isn't empty, output it.
    if token:
        buffered.append(repr(token))