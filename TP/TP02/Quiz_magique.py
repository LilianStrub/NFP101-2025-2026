import random
rejouer = True
valide = False
meilleure_score = 0
nbr1, nbr2 = 0, 0
list_opertaions = ['+', '-', '*']

while rejouer == True:
    reponse = 0
    correct = 0
    while True:
        entree = input("\nCombien de questions dans le quiz magique ? ")
        
        # Si l'entrée est une chaine de caractères ou un nombre négatif
        if entree.isdigit():  # Vérifie que tous les caractères sont des chiffres
            nbr_questions = int(entree)
            break
        else:
            print("Erreur : veuillez entrer un nombre entier positif.")
    
    for i in range(1, nbr_questions + 1):
        nbr1 = random.randint(1, 10)
        nbr2 = random.randint(1, 10)
        operateur = list_opertaions[random.randint(0, 2)]
        
        while nbr1 < nbr2 or (nbr1 == 0 and nbr2 == 0): 
            nbr1 = random.randint(1, 10)
            nbr2 = random.randint(1, 10)
        
        while True:
            entree = input(f"\nQuestion {i} : {nbr1} {operateur} {nbr2} = ")
            
            # Si l'entrée est une chaine de caractères
            if entree.isdigit():  # Vérifie que tous les caractères sont des chiffres
                question = int(entree)
                break
            else:
                print("Erreur : veuillez entrer un nombre entier.")
            
        if (question == nbr1 * nbr2 and operateur == '*') or (question == nbr1 + nbr2 and operateur == '+') or (question == nbr1 - nbr2 and operateur == '-'):
            print("Correct !")
            correct += 1
        elif operateur == '+':
            print(f"Faux, la bonne réponse était {nbr1 + nbr2}.")
        elif operateur == '-':
            print(f"Faux, la bonne réponse était {nbr1 - nbr2}.")
        elif operateur == '*':
            print(f"Faux, la bonne réponse était {nbr1 * nbr2}.")
            
    print(f"\nVous avez obtenu {correct} bonnes réponses sur {nbr_questions}.")
    score = round((correct / nbr_questions) * 100, 1)
    print(f"Votre pourcentage de réussite est : {score} %")

    if score >= 80:
        print(f"Bravo !")
    elif score >= 50:
        print("Pas mal, continue à t'entraîner.")
    else:
        print("Il faut reviser encore.")
    if meilleure_score < score:
        meilleure_score = score
    
    while reponse not in [1, 3] or reponse == 2:
        reponse = int(input("\n1 - Refaire un quiz\n2 - Voir le meilleur score obtenu jusqu'à présent\n3 - Quitter\n\nVotre choix : "))
        if reponse == 1:
            rejouer = True
        elif reponse == 2:
            print(f"\nMeilleur score jusqu'à présent : {meilleure_score}%.")
        elif reponse == 3:
            rejouer = False
        else: 
            print("Choix invalide, Veillez choisir entre 1, 2 ou 3.")

print("\nMerci d'avoir joué au quiz magique ! Au revoir.")

