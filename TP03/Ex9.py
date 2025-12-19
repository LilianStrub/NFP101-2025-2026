def convBinaire(n):
    """
    Fonction qui convertit un entier n en sa représentation binaire
    :param n: entier
    :return: chaîne de caractères représentant n en binaire
    """
    if n == 0:
        return "0"

    binaire = ""

    while n > 0:
        r = n % 2
        binaire = str(r) + binaire
        n = n // 2

    return binaire

def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    resultat = convBinaire(n)
    print(f"La représentation binaire de {n} est : {resultat}")
    
    # Vérification avec la fonction bin intégrée
    print(f"Vérification avec la fonction bin intégrée : {bin(n)[2:]}")

# Point d'entrée du programme
if __name__ == "__main__":
    main()