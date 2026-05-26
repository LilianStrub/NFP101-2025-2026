bille = 0
etage = int(input("Nombre d'étages de la pyramide : "))
for etage in range(1, etage+1):
    bille = bille + etage*etage
    print(f"Etage {etage} : {bille} billes")