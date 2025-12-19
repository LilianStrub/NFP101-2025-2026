def min_max(tab):
    """
    Procédure qui retourne le minimum et le maximum d'un tableau d'entiers
    :param tab: liste d'entiers
    :return: minimum et maximum du tableau
    """
    # On suppose que le tableau contient au moins un élément
    minimum = tab[0]
    maximum = tab[0]

    for i in range(1, len(tab)):
        if tab[i] < minimum:
            minimum = tab[i]
        if tab[i] > maximum:
            maximum = tab[i]

    return minimum, maximum

def main():
    """
    Fonction principale du programme
    """
    T = [5, -2, 10, 3, 0]

    mini, maxi = min_max(T)

    print("Minimum :", mini)
    print("Maximum :", maxi)

    # Vérification
    print("Vérification Python :", min(T), max(T))

# Point d'entrée du programme
if __name__ == "__main__":
    main()