def convHexa(n):
    """
    Fonction qui convertit un entier n en sa représentation hexadécimale
    :param n: entier
    :return: chaîne de caractères représentant n en hexadécimal
    """
    if n == 0:
        return "0"

    chiffres = "0123456789ABCDEF"
    hexa = ""

    while n > 0:
        r = n % 16
        hexa = chiffres[r] + hexa
        n = n // 16

    return hexa

def main():
    """
    Fonction principale du programme
    """
    n = int(input("Saisir un entier n : "))
    resultat = convHexa(n)
    print(f"La représentation hexadécimale de {n} est : {resultat}")
    
    # Vérification avec la fonction hex intégrée
    print(f"Vérification avec la fonction hex intégrée : {hex(n)[2:].upper()}")

# Point d'entrée du programme
if __name__ == "__main__":
    main()