def premier(n):
    """
    Fonction qui détermine si un entier n est un nombre premier
    :param n: entier
    :return: True si n est premier, False sinon
    """
    if n <= 1:
        return False

    for i in range(2, n):
        if n % i == 0:
            return False

    return True

def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    if premier(n):
        print(f"{n} est un nombre premier.")
    else:
        print(f"{n} n'est pas un nombre premier.")

# Point d'entrée du programme
if __name__ == "__main__":
    main()