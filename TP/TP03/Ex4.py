def termeSuite2(n):
    """
    Fonction qui permet de calculer et d'afficher le n-ième terme de la suite U
    :param n: entier
    :return: n-ième terme de la suite U
    """
    if n == 0:
        print("U0 =", 3)
        return
    if n == 1:
        print("U1 =", 1)
        return

    U0 = 3
    U1 = 1

    for i in range(2, n + 1):
        U = U1 + U0
        U0 = U1
        U1 = U

    print("U" + str(n), "=", U1)

def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    termeSuite2(n)

# Point d'entrée du programme
if __name__ == "__main__":
    main()