class Voiture:
    def __init__(self, couleur = None, nationalite = None):
        self.couleur = couleur
        self.nationalite = nationalite

class Voiture_FR(Voiture):
    def __init__(self):
        super().__init__()
        self.nationalite = "FR"