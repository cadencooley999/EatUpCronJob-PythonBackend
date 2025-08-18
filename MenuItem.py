def getItemId(name, period, calories, category):
    id = f'{name.replace(" ", "")}{period[:2]}{calories}{category[:2]}'
    id = id.replace("/", "")
    id = id.replace(".", "")
    return id

class MenuItem:

    def __init__(self, name, calories, protein, today, tomorrow, harrisToday, harrisTomorrow, category, period):
        self.id = getItemId(name, period, calories, category)
        self.name = name
        self.calories = calories
        self.protein = protein
        self.today = today
        self.tomorrow = tomorrow
        self.harrisToday = harrisToday
        self.harrisTomorrow = harrisTomorrow
        self.category = category
        self.period = period

    def toJson(self):
        selfDict = {
            "id" : self.id,
            "name" : self.name,
            "calories" : self.calories,
            "protein" : self.protein,
            "today" : str(self.today),
            "tomorrow" : str(self.tomorrow),
            "harrisToday" : str(self.harrisToday),
            "harrisTomorrow" : str(self.harrisTomorrow),
            "category" : self.category,
            "period" : self.period
        }
        return selfDict
    