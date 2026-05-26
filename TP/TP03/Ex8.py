def factoriel(n):
    """
    Fonction qui calcule la factorielle d'un entier n
    :param n: entier
    :return: factorielle de n
    """
    if n < 0:
        return None 

    fact = 1
    for i in range(1, n + 1):
        fact = fact * i

    return fact

def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    resultat = factoriel(n)
    if resultat is not None:
        print(f"La factorielle de {n} est : {resultat}")
    else:
        print("Erreur : La factorielle n'est pas définie pour les entiers négatifs.")

# Point d'entrée du programme
if __name__ == "__main__":
    main()