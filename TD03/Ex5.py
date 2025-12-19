liste = [6, 9, 2, 8, 5, 4]

def triSelection(liste):
    n = len(liste)
    for i in range(n):
        min_index = i
        for j in range(i+1, n):
            if liste[j] < liste[min_index]:
                min_index = j
        liste[i], liste[min_index] = liste[min_index], liste[i]
        
triSelection(liste)
print(liste)  # Doit afficher [2, 4, 5, 6, 8, 9]