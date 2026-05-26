terme1, terme2 = 1, 1
etage = int(input("Etage : "))
for i in range(1, etage - 1):
    somme = terme1 + terme2
    terme1 = terme2
    terme2 = somme
print(f"Série de Fibonnaci à l'étage {etage} : {somme}")
