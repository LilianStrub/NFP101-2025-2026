# Définition de la classe Voiture
class Voiture:
    def __init__(self, marque):
        """
        Constructeur de la classe Voiture.
        Initialisation de roues, couleur et taille à 0.
        :param marque: La marque de la voiture (ex: Toyota)
        """
        self.marque = marque
        self.couleur = 0   # initialisée à 0
        self.roues = 0     # initialisée à 0
        self.taille = 0    # initialisée à 0

    def afficher(self):
        """
        Affiche les informations de la voiture.
        """
        print(f"Marque : {self.marque}, Couleur : {self.couleur}, Roues : {self.roues}, Taille : {self.taille}")

    def changerCouleur(self, nouvelle_couleur):
        """
        Change la couleur de la voiture.
        :param nouvelle_couleur: La nouvelle couleur à appliquer (ex: Rouge)
        """
        self.couleur = nouvelle_couleur

    def configurationBase(self, nombre_roues=4, taille=200):
        """
        Configure les attributs de base de la voiture avec valeurs par défaut.
        Affiche la couleur actuelle.
        :param nombre_roues: Nombre de roues (par défaut 4)
        :param taille: Taille de la voiture (par défaut 200)
        """
        self.roues = nombre_roues
        self.taille = taille
        print(f"Couleur actuelle : {self.couleur}")
        print(f"Nombre de roues : {self.roues}, Taille : {self.taille}")

# Fonction principale
def main():
    # Création d'une voiture
    voiture = Voiture("Toyota")
    print("Informations initiales :")
    voiture.afficher()

    # Modifier la couleur via la méthode
    voiture.changerCouleur("Rouge")
    print("\nAprès changement de couleur :")
    voiture.afficher()

    # Appeler configurationBase sans arguments
    print("\nAppel de configurationBase sans arguments :")
    voiture.configurationBase()

# Point d'entrée
if __name__ == "__main__":
    main()
