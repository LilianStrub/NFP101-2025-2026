# Définition de la classe Voiture
class Voiture:
    def __init__(self, marque, couleur):
        """
        Constructeur de la classe Voiture.
        :param marque: La marque de la voiture (ex: Toyota)
        :param couleur: La couleur initiale de la voiture (ex: Bleu)
        """
        self.marque = marque
        self.couleur = couleur

    def afficher(self):
        """
        Affiche les informations de la voiture :
        marque, couleur, nombre de roues et dimensions si elles existent.
        """
        print(f"Marque : {self.marque}, Couleur : {self.couleur}")
        # Vérifie si l'objet possède l'attribut 'nombre_roues'
        if hasattr(self, "nombre_roues"):
            print(f"Nombre de roues : {self.nombre_roues}")
        # Vérifie si l'objet possède l'attribut 'dimensions'
        if hasattr(self, "dimensions"):
            print(f"Dimensions : {self.dimensions}")

    def changerCouleur(self, nouvelle_couleur):
        """
        Change la couleur actuelle de la voiture.
        :param nouvelle_couleur: nouvelle couleur à appliquer (ex: Rouge)
        """
        self.couleur = nouvelle_couleur

    def configurationBase(self, nombre_roues, dimensions):
        """
        Configure les attributs de base supplémentaires de la voiture.
        :param nombre_roues: nombre de roues de la voiture (ex: 4)
        :param dimensions: dimensions de la voiture (longueur, largeur, hauteur)
        """
        self.nombre_roues = nombre_roues
        self.dimensions = dimensions

# Fonction principale
def main():
    """
    Fonction principale du programme.
    Crée une voiture, change sa couleur et configure ses attributs de base.
    """
    # Création d'une voiture initiale avec marque et couleur
    voiture = Voiture("Toyota", "Bleu")
    print("Informations initiales de la voiture :")
    voiture.afficher()

    # 1) Changer la couleur de bleu à rouge
    voiture.changerCouleur("Rouge")
    print("\nAprès changement de couleur :")
    voiture.afficher()

    # 2) Initialiser les variables roues et taille
    roues = 4
    taille = (4.2, 1.8, 1.5)  # Dimensions : (longueur, largeur, hauteur)
    # Utiliser la méthode configurationBase pour ajouter ces valeurs à l'objet
    voiture.configurationBase(roues, taille)
    print("\nAprès configuration de la voiture :")
    voiture.afficher()

# Point d'entrée du programme
if __name__ == "__main__":
    main()