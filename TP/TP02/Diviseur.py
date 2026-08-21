entier = int(input("Entier : "))
diviseur = 0
print("Diviseurs propres sans repetition de", entier, ": ", end="")
for i in range(2, entier):
    if entier % i == 0:
        # Affichage sur une ligne sans retour à la ligne
        print(i, "", end="")
        diviseur += 1
if diviseur == 0:
    print("aucun !")
    print("Il est premier")
else:
    print(f"\n(soit {diviseur} diviseurs propres)")  # Retour à la ligne finale