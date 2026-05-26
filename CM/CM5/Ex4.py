# Définition de la classe Voiture
class Voiture:
    def __init__(self, marque, couleur):
        # Attribut 'marque' : la marque de la voiture
        self.marque = marque
        # Attribut 'couleur' : la couleur de la voiture
        self.couleur = couleur

    # Méthode pour afficher les informations de la voiture
    def afficher(self):
        print(f"Marque : {self.marque}, Couleur : {self.couleur}")

    # Méthode pour changer la couleur de la voiture
    def changerCouleur(self, nouvelle_couleur):
        """
        Change la couleur actuelle de la voiture
        :param nouvelle_couleur: nouvelle couleur à appliquer
        """
        self.couleur = nouvelle_couleur

    # Méthode pour configurer les attributs de base supplémentaires
    def configurationBase(self, nombre_roues, dimensions):
        """
        Ajoute le nombre de roues et les dimensions à l'objet voiture
        :param nombre_roues: entier, nombre de roues de la voiture
        :param dimensions: tuple ou liste (longueur, largeur, hauteur)
        """
        self.nombre_roues = nombre_roues
        self.dimensions = dimensions

# Fonction principale
def main():
    # Création du premier objet Voiture
    voiture1 = Voiture("Toyota", "Rouge")
    print("Informations de la première voiture :")
    voiture1.afficher()

    # Création du deuxième objet en reprenant la marque mais en changeant la couleur
    voiture2 = Voiture(voiture1.marque, "Bleu")
    print("\nInformations de la deuxième voiture :")
    voiture2.afficher()

# Point d'entrée du programme
if __name__ == "__main__":
    main()