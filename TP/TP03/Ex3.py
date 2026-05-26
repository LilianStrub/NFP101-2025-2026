def termeSuite(n):
    """
    Fonction qui permet de calculer et d'acher les n premiers termes de la suite U
    :param n: entier
    :return: n premiers termes de la suite U
    """
    U = 3
    print("U0 =", U)

    for i in range(1, n):
        U = 2 * U - 4
        print("U" + str(i), "=", U)

def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    termeSuite(n)

# Point d'entrée du programme
if __name__ == "__main__":
    main()