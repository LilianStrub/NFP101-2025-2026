res = 0
chaine = input("Chaîne de caractères : ")

# Pour toutes les caractères de la chaine
for car in chaine:
    # Si le caractère est un 'z'
    if car == 'z':
        res += 1
print(f"Le nombre de 'z' dans la chaîne est : {res}")