def pgcd(a, b):
    """
    Fonction qui calcule le PGCD de deux entiers a et b
    en utilisant l'algorithme d'Euclide
    :param a: entier
    :param b: entier
    :return: PGCD de a et b
    """
    while b != 0:
        r = a % b
        a = b
        b = r
    return a

def main():
    """
    Fonction principale du programme
    """
    a = int(input("Saisir le premier entier a : "))
    b = int(input("Saisir le deuxième entier b : "))
    resultat = pgcd(a, b)
    print(f"Le PGCD de {a} et {b} est : {resultat}")

# Point d'entrée du programme
if __name__ == "__main__":
    main()