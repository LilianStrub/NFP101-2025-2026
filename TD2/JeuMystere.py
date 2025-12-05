import random
        
def demander_limites():
    verif = False
    while verif == False:
        while True:
            entree = input("Entrez une borne minimale : ")
            if entree.isdigit():
                mini = int(entree)
                break
            else:
                print("Erreur : veuillez entrer un nombre entier positif.\n")
            
        while True:
            entree = input("Entrez une borne maximale : ")
            if entree.isdigit():
                maxi = int(entree)
                break
            else:
                print("Erreur : veuillez entrer un nombre entier positif.\n")
        
        if mini > maxi:
            print("La borne minimale ne peut pas être supérieure à la borne maximale.\n")
        else:
            verif = True
    return mini, maxi
    
def tirer_nombre_mystere(mini, maxi):
    return random.randint(mini, maxi)

def demander_proposition(mini, maxi):
    while True:
        entree = input(f"Quel est le nombre secret (entre {mini} et {maxi}) ? ")
        if entree.isdigit():
            proposition = int(entree)
            if mini <= proposition <= maxi:
                return proposition
            else:
                print(f"Veuillez entrer un nombre entre {mini} et {maxi}.\n")
        else:
            print("Erreur : veuillez entrer un nombre entier positif.\n")
            
def analyser_proposition(proposition, secret):
    if proposition < secret:
        return -1
    elif proposition > secret:
        return 1
    else:
        return 0
    
def jouer_une_partie():
    nbessais = 0
    mini, maxi = demander_limites()
    secret = tirer_nombre_mystere(mini, maxi)
    proposition = demander_proposition(mini, maxi)
    analyser_proposition(proposition, secret)
    nbessais += 1
    while analyser_proposition(proposition, secret) != 0:
        nbessais += 1
        if analyser_proposition(proposition, secret) == -1:
            print("Trop petit")
        else:
            print("Trop grand")
        proposition = demander_proposition(mini, maxi)
        analyser_proposition(proposition, secret)
    print("\nBravo !")
    print(f"Vous avez trouvé le nombre en {nbessais} essais.")
    
def demander_rejouer():
    reponse = ''
    while reponse not in ['o', 'n']:
        reponse = input("\nVoulez-vous rejouer ? (o/n) : ")
        if reponse.lower() == 'o':
            return True
        elif reponse.lower() == 'n':
            return False
        else:
            print("Veuillez répondre par 'o' pour oui ou 'n' pour non.\n")

if __name__ == "__main__":
    print("=== Bienvenue dans le jeu du Nombre Mystère ===\n")
    while True:
        jouer_une_partie()
        if not demander_rejouer():
            print("\nMerci d'avoir joué ! Au revoir.")
            break