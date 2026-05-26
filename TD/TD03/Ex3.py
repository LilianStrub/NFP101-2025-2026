liste = [8, 5, 3, 6, 4, 7]

def triInsertion(liste):
    for i in range(1, len(liste)):
        valeur_a_inserer = liste[i]
        j = i - 1
        while j >= 0 and liste[j] > valeur_a_inserer:
            liste[j + 1] = liste[j]
            j -= 1
        liste[j + 1] = valeur_a_inserer
        
triInsertion(liste)
print(liste)  # Doit afficher [3, 4, 5, 6, 7, 8]