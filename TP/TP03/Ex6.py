def pgcd(a, b):
    """
    Fonction qui calcule le PGCD de deux entiers a et b
    en utilisant l'algorithme d'Euclide
    :param a: entier
    :param b: entier
    :return: PGCD de a et b
    """
    while b != 0:
        a, b = b, a % b
    return a

def ppcm(a, b):
    """
    Fonction qui calcule le PPCM de deux entiers a et b
    en utilisant le PGCD
    :param a: entier
    :param b: entier
    :return: PPCM de a et b
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // pgcd(a, b)

def main():
    """
    Fonction principale du programme
    """
    a = int(input("Saisir le premier entier a : "))
    b = int(input("Saisir le deuxième entier b : "))
    resultat = ppcm(a, b)
    print(f"Le PPCM de {a} et {b} est : {resultat}")

# Point d'entrée du programme
if __name__ == "__main__":
    main()