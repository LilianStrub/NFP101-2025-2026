import random
        
def demander_limites():
    verif = False
    while verif == False:
        mini = int(input("Entrez une borne minimale : "))
        maxi = int(input("Entrez une borne maximale : "))
        if mini > maxi:
            print("La borne minimale ne peut pas être supérieure à la borne maximale.")
        else:
            verif = True
            return mini, maxi
    
def tirer_nombre_mystere(mini, maxi):
    return random.randint(mini, maxi)

def demander_proposition(mini, maxi):
    verif = False
    while verif == False:
        proposition = int(input(f"Quel est le nombre secret (entre {mini} et {maxi}) ? "))
        if mini <= proposition <= maxi:
            verif = True
            return proposition
        else:
            print(f"Veuillez entrer un nombre entre {mini} et {maxi}.")
            
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
    demander_rejouer()
    
def demander_rejouer():
    reponse = input("\nVoulez-vous rejouer ? (o/n) : ")
    if reponse.lower() == 'o':
        return True
    else:
        return False

if __name__ == "__main__":
    print("=== Bienvenue dans le jeu du Nombre Mystère ===\n")
    jouer_une_partie()