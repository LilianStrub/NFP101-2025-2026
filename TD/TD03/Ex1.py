liste = [8, 3, 12, 9, 5, 10, 6]

def rechSeq(liste, valeur):
    for i in range(len(liste)):
        if liste[i] == valeur:
            return True
    return False

print(rechSeq(liste, 5))  # Doit afficher True
print(rechSeq(liste, 7))  # Doit afficher False