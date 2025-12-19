def somme(n):
    """
    Fonction qui permet de calculer la somme de n premiers entiers.
    :param n: entier
    :return: somme des n premiers entiers
    """
    try:
        if n < 0:
            raise ValueError("n doit être un entier positif.")
        else:
            somme = 0
            for i in range(1, n + 1):
                somme += i
            return somme
    
    except ValueError:
        print("Erreur : Veuillez saisir un entier valide.")
        return None

def sommeChoix(n):
    """
    Fonction qui permet de calculer et
    d'afficher la somme de n entiers saisis par l'utilisateur.
    :param n: entier
    :return: somme des n entiers saisis
    """
    try:
        if n < 0:
            raise ValueError("n doit être un entier positif.")
        else:
            somme = 0
            for i in range(n):
                valeur = int(input(f"Saisir l'entier {i + 1} : "))
                somme += valeur
            return somme

    except ValueError:
        print("Erreur : Veuillez saisir un entier valide.")
        return None
    
def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    if somme(n) is not None or sommeChoix(n) is not None:
        print(f"La somme des {n} premiers entiers est : {somme(n)}")
        print(f"La somme des {n} entiers saisis est : {sommeChoix(n)}")
    else:
        print("Le programme s'est terminé en raison d'une erreur de saisie.")


# Point d'entrée du programme
if __name__ == "__main__":
    main()