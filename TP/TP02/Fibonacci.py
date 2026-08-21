n = int(input("Nombre de termes : "))
terme1, terme2 = 0, 1

# Affiche la série des n premiers termes de Fibonacci : 0, 1, 1, 2, 3, 5, 8, ...
print(f"Série de Fibonacci pour {n} termes : ", end="")
for i in range(n):
    print(terme1, end=" ")
    terme1, terme2 = terme2, terme1 + terme2
print()
