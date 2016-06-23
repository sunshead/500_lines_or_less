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