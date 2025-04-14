import Pyro4

insult_filter = Pyro4.Proxy("PYRONAME:InsultFilter")
text = "You nincompoop, you idiot!"
result = insult_filter.filter_text(text)
print("Filtered text:", result)
print("All filtered results:", insult_filter.get_results())
