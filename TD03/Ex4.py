liste = [7, 3, 18, 5, 13]

def triBulles(liste):
    n = len(liste)
    for i in range(n):
        for j in range(0, n-i-1):
            if liste[j] > liste[j+1]:
                liste[j], liste[j+1] = liste[j+1], liste[j]
                
triBulles(liste)
print(liste)  # Doit afficher [3, 5, 7, 13, 18]