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

# Fonction principale du programme
def main():
    """
    Fonction principale du programme
    """
    # Création du premier objet 'voiture1' avec marque et couleur
    voiture1 = Voiture("Toyota", "Rouge")
    # Affichage des informations de voiture1
    voiture1.afficher()

    # Création du deuxième objet 'voiture2'
    # On reprend la marque de voiture1 mais on change la couleur
    voiture2 = Voiture(voiture1.marque, "Bleu")
    # Affichage des informations de voiture2
    voiture2.afficher()

# Point d'entrée du programme
if __name__ == "__main__":
    main()