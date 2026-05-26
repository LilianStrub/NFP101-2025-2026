liste = [3, 5, 6, 8, 9, 12, 15, 19, 23, 51]

def rechDi(liste, valeur):
    debut = 0
    fin = len(liste) - 1
    while debut <= fin:
        milieu = (debut + fin) // 2
        if liste[milieu] == valeur:
            return True
        elif liste[milieu] < valeur:
            debut = milieu + 1
        else:
            fin = milieu - 1
    return False

print(rechDi(liste, 15))  # Doit afficher True
print(rechDi(liste, 7))  # Doit afficher False