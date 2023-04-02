import os, json, csv
from flask import Flask, redirect, render_template, request, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from form import nouvelleQuestion
from random import choice
import random
import math
import operator
from flask_socketio import SocketIO, send

from unidecode import unidecode
import base64
import io
from wordcloud import WordCloud




basedir = os.path.abspath(os.path.dirname(__file__))
user_file = os.path.join(basedir, 'static/js/users.json')
etiquette_file = os.path.join(basedir, 'static/txt/etiquettes.txt')
question_file = os.path.join(basedir, 'static/js/questions.json')
etudiants_file = os.path.join(basedir, 'static/js/etudiants.json')
questionDiffusée_file = os.path.join(basedir, 'static/js/questionDiffusée.json')




app = Flask(__name__)
app.secret_key = "any random string"
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':

#Je récupère les données du formulaire 
        name=request.form.get('name')
        email=request.form.get('email')
        password=request.form.get('password')

#J'ouvre le fichier users.json pour vérifier si l'adresse existe dejà, 
# si c'est le cas j'envoie un message à afficher
# Le fichier ne doit pas être vide pour ne pas générer d'erreur

        with open(user_file) as file:
            data = json.load(file)
            for user in data["users"]:
                if user["email"]==email:
                    flash('Email address already exists')
                    return render_template("signup.html")
            
#Si l'adresse n'existe pas dejà, je récupère les données de users.json, 
# je leur rajoute le dictionnaire user crée à partir des données récupérées 
# du formailaire et je rajoute les nouveaux données au fichier

        with open(user_file, 'w') as file:
            user = {"name" : name, "email" : email, "password" : generate_password_hash(password, method='sha256')}
            data["users"].append(user)
            json.dump(data, file, indent='\t')
    
        return redirect(url_for('login'))

    else:
        return render_template("signup.html")

@app.route('/HomeEtudiant')
def homeEtudiant():
    return render_template('etudiant.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method=='POST':
        
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if email[0]=='e':
            with open(etudiants_file) as file : 
                data = json.load(file)
                for etudiant in data["Etudiants"]:
                    if etudiant["Numero Etudiant"]==email and  etudiant["Nom"]+etudiant["Prenom"]==password:
                        return redirect(url_for('homeEtudiant'))

#Je vérifie si l'email et le mot de passe saisis existe dans users.json
# Sinon j'envoie un message à afficher

        else:
            with open (user_file) as file:
                data=json.load(file)
                for user in data["users"]:
                    if user["email"]==email and check_password_hash(user["password"], password):
                        session['username']=user["name"]
                        return redirect(url_for('home'))
        
    flash('Please check your login details and try again.')
    return  render_template("login.html")

        
        
@app.route('/Home')
def home():

#Ne pas ouvrir l'url manuellement parce que ça va générer une erreur puisque
#la session ne s'initialise qu'après le login

    if 'username' in session:
        name=session['username']

#Je récupère les questions de questions.json et les envoie à la page html 
# Le fichier ne doit pas être vide pour ne pas générer d'erreur

    with open(question_file) as file:
        data=json.load(file)
        questions=data["questions"]
        
        nb_Questions=len(questions)
    
    return render_template("home.html", questions=questions, nb_Questions=nb_Questions, name=name)

@app.route('/Home/Question/<numQuestion>')
def getQuestions(numQuestion):
    with open(question_file) as file:
        data=json.load(file)
#J'affiche la question dont le numéro est passé à l'url
        question=data["questions"][int(numQuestion)-1]
    return render_template("getQuestion.html", numQuestion=str(numQuestion), question=question, )


@app.route('/logout')
def logout():
   session.pop('username', None)
   return redirect(url_for('login'))

def getEtiquettes():
#Je recupère les étiquettes du fichier etiquettes.txt
    choices=[]
    with open(os.path.join("static/txt", "etiquettes.txt")) as file:
        for line in file:
            choices.append(line)
    return choices

@app.route('/Home/nouvelleQuestion', methods=['POST', 'GET'])
def nouvelleQues():
    form = nouvelleQuestion()
#Je peuple les choix des etiquettes dynamiquement des étiquettes récupérés du fichier etiquettes.txt
    form.etiquettes.choices=getEtiquettes()
    if request.method=='POST':
        enonce=request.form['enonce']
        propostions=request.form.getlist('proposition[]')
        etiquettes=form.etiquettes.data
        alphabet = [ chr(i) for i in range(48,123) if i <= 57 or (i >= 65 and i <=90) or (i >= 97) ]
        identifiant = generate_id_formated(alphabet)

        #on supprime les caractères \r\n à la fin d'une étiquette
        for i in range(len(etiquettes)):
            etiquettes[i]=etiquettes[i][:-2]


        dict = {"enonce" : enonce, "propositions" : propostions, "etiquettes" : etiquettes, "identifiant" : identifiant}
#Je rajoute la nouvelle question au fichier json, il ne faut pas qu'il soit vide pour ne pas générer d'erreurs
        with open(question_file) as file:
            data = json.load(file)
            data["questions"].append(dict)

        with open(question_file, 'w') as file:
            json.dump(data, file, indent='\t')

        return redirect(url_for('home'))
    else :
        return render_template('nouvelleQuestion.html', form=form)

@app.route('/ajoutEtiquette', methods=['POST', 'GET'])
def ajoutEtiquette():
#J'ajoute l'etiquette recupéré à partir du formulaire au fichier etiquette.txt
    if request.method=='POST':
        etiquette=request.form['etiquette']
        with open(etiquette_file, 'a') as file:
            file.write(etiquette+"\n")
        return redirect(url_for('nouvelleQues'))
    else:
        render_template("nouvelleQuestion.html")

@app.route('/supprimerQuestion/<numQuestion>', methods=['POST', 'GET'])
def supprimerQuestion(numQuestion):
#Je supprime la question dont le numéro est passé dans l'url
    if request.method=='POST':
        with open(question_file) as file:
            data=json.load(file)
            del data["questions"][int(numQuestion)-1]

        with open(question_file, 'w') as file:
            json.dump(data, file, indent='\t')

        return redirect(url_for('home'))

    else :
        return redirect(url_for('home'))



@app.route('/Home/pageDeQuestions', methods=['POST', 'GET'])
def pageQuestions():
#Je crée une page avec tout les questions pour en choisir et génerer une page de questions  
    form = nouvelleQuestion()
    form.etiquettes.choices=getEtiquettes()


    listeTags=[]
    with open(etiquette_file) as tags:

        if request.method == "GET":
            for ligne in tags.readlines():
                listeTags.append(ligne[:-1])
        else:
            eti=request.form.getlist("etiquettes")
            for t in eti:
                listeTags.append(t[:-2])

                
    with open(question_file) as file:
        data=json.load(file)
    
    questions=[]

    for i in range(len(data["questions"])):
        for j in (data["questions"][i]["etiquettes"]):
            if j in listeTags:
                questions.append(data["questions"][i])
                break
        
    nb_Questions=len(questions)


    return render_template("pageQuestions.html", questions=questions, nb_Questions=nb_Questions, form=form)







dictIdProp = {}
idsNuageMot = {}



@app.route('/Home/nuageDeMot', methods=['POST', 'GET'])
def nuageDeMot():

    if request.method == 'GET':
        code = """Choisissez l'énoncé de votre question :<br><form method='POST'><textarea name='enonce'></textarea><br><button type='submit' formaction='/Home/nuageDeMot'>Proposer question en direct</button></form>"""
        return render_template('nuageDeMot.html',code=code)

    else :
        enonce=request.form['enonce']
        ident = generate_id_formated([ chr(i) for i in range(48,123) if i <= 57 or (i >= 65 and i <=90) or (i >= 97) ])
        dictIdProp[ident]={}
        idsNuageMot[ident] = enonce
        code = """<form method="POST">L'identifiant nécessaire aux élèves pour accéder à votre question est : <input type="hidden" name='id' value='""" + ident + """'>""" + ident + "</input><br><br><br> Les étudiants sont en train de répondre à la question :<br>" + enonce + "<br><button type='submit' formaction='/nuage'>Générer Nuage</button></form>"
        return render_template('nuageDeMot.html',code=code)

@app.route('/nuage', methods=['POST', 'GET'])
def nuage():
    if request.method=='POST':
        texte=""
        identifiant=request.form['id']
        for prop in dictIdProp[identifiant]:
            for i in range(dictIdProp[identifiant][prop]):
                texte += prop + " "

    wc = WordCloud(background_color='#00d1b2').generate(texte)
    wcImage=wc.to_image()
    img = io.BytesIO()
    wcImage.save(img, format='PNG')
    imgword='data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())

    return render_template('nuage.html', img=imgword)




@app.route('/Home/nuageDeMotEtudiant', methods=['POST', 'GET'])
def nuageDeMotEtudiant():
    if request.method == 'GET':
        return "{% extends 'base.html' %}Veuillez rentrer le code qu'un enseignant vous aura transmis<br><br><form method='POST'><input type='text' name='id' ><button type='submit' formaction='/Home/nuageDeMotEtudiant'>Envoyer</button>"
    else :
        ident=request.form['id']
        if ident in idsNuageMot:
            code = idsNuageMot[ident] + "<br><br><input id='reponse' type='text'><br><br>" + """<button onclick="socket.emit('envoieInfo',recupReponse(), '""" + ident + """')">Envoyer</button>"""
            code += "<script>function recupReponse() { return document.getElementById('reponse').value;}</script>"
            return render_template('nuageDeMot.html', code=code)
        else :
            return "Identifiant incorrect"
        

listePrefixe=['a','bi','cis','co','di','dys','en','em','epi','ex','geo','in','im','il','ir','iso','mal']

@socketio.on('envoieInfo')
def handle_info(info,identifiant):

    propDejaExistant=False
    prefixeDifferent=False
    info=info.lower()
    info=unidecode(info)

    for proposition in dictIdProp[identifiant]:
        proposition=proposition.lower()
        proposition=unidecode(proposition)

        if len(info)<= 3:
            if info == proposition :
                propDejaExistant=True
                dictIdProp[identifiant][info] += 1

        for prefixe in listePrefixe :
            if (((proposition.startswith(prefixe)) and (not info.startswith(prefixe)))) or (((not proposition.startswith(prefixe)) and (info.startswith(prefixe)))):
                prefixeDifferent=True

        if not prefixeDifferent :
            if dist(info, len(info), proposition, len(proposition)) <= 3:
                propDejaExistant=True
                dictIdProp[identifiant][proposition] += 1

    if not propDejaExistant:
        dictIdProp[identifiant][info] = 1
    print(dictIdProp)



def dist(X, m, Y, n):
 
    if m == 0:
        return n
 
    if n == 0:
        return m
 
    cost = 0 if (X[m - 1] == Y[n - 1]) else 1
 
    return min(dist(X, m - 1, Y, n) + 1,
            dist(X, m, Y, n - 1) + 1,
            dist(X, m - 1, Y, n - 1) + cost)
 


@app.route('/Home/genererControle', methods=['POST', 'GET'])
def pageGenerationControle():
    if request.method=='POST':
        dictionnaireEtiquettes={}
        DE={}
        identification=""

        if request.form['typeControle'] == 'anonymat':
            compteurA=13
            identification="Veuillez inscrire votre numéro étudiant de manière à ce qu'il n'y ai qu'une seule case cochée par colonne<br><br>"
            for i in range(10):
                identification += str(i)
                for j in range(6):
                    identification += ' <input type="checkbox">'
                identification += '<br>'


        elif request.form['typeControle'] == 'etudiant':
            compteurA=4
            identification="Veuillez renseigner les informations suivantes :<br><br>Nom :<br>Prénom :<br>Numéro étudiant :"

        with open(etiquette_file) as tags:

            comptePossibilites=1
            with open(question_file) as fileQ:
                toutesQuestions=json.load(fileQ)['questions']


            for etiquetteActuelle in (tags.readlines()):
                listeBufferEti=[]
                
                for ex in toutesQuestions:
                    if (etiquetteActuelle[:-1]) in ex['etiquettes']:
                        
                        listeBufferEti.append(ex)
                comptePossibilites = comptePossibilites * math.comb(len(listeBufferEti),int(request.form.getlist((etiquetteActuelle[:-1]))[1]))
                print(comptePossibilites,math.comb(len(listeBufferEti),int(request.form.getlist((etiquetteActuelle[:-1]))[1])))
                for truc in listeBufferEti:
                    toutesQuestions.remove(truc)

            if comptePossibilites < int(request.form['nbCopie']):

                return "Vous avez demandé trop de questions pour faire tant de copies différentes"


        

        nbDeCopie=request.form["nbCopie"]
        Lcontrole=[]
        compteCopie=0

        while compteCopie!=int(nbDeCopie):
            nbQ=0
            while nbQ!=int(request.form["nbQuestion"]):
                nbQ=0
                with open(etiquette_file) as tags:
                    for ligne in (tags.readlines()):
                        DE[ligne[:-1]]=request.form.getlist(ligne[:-1])

                        NombreAlea=random.randint(int(DE[ligne[:-1]][0]),int(DE[ligne[:-1]][1]))
                        dictionnaireEtiquettes[ligne[:-1]]=NombreAlea
                        nbQ+=NombreAlea


            Lcopie=[]
            for key in dictionnaireEtiquettes:
                listeQuestEtiq=[]

                
                with open(question_file) as file:
                    data=json.load(file)
                    for question in data["questions"]:
                        for etiq in question["etiquettes"]:
                            if etiq==key:
                                
                                listeQuestEtiq.append(question)
                                
                compteur=0
                while compteur<int(dictionnaireEtiquettes[key]):
                    listeAjout=listeQuestEtiq[random.randint(0,len(listeQuestEtiq)-1)]
                    Lcopie.append(listeAjout)
                    listeQuestEtiq.remove(listeAjout)
                    data["questions"].remove(listeAjout)
                    compteur+=1
            if Lcopie not in Lcontrole:
                melange=request.form["typequestion"]

                if melange=="alea":
                    random.shuffle(Lcopie)
                
                Lcontrole.append(Lcopie)
                compteCopie+=1

          
        return render_template("afficherControle.html",Lcontrole=Lcontrole,identification=identification,compteur=compteurA)

    with open(question_file) as file:
        data=json.load(file)


    questionParTag=''

    with open(etiquette_file) as tags:
        for ligne in (tags.readlines()):

            compteurQuestionEtiquette=0
            for e in data['questions']:
                if ligne[:-1] in e['etiquettes']:
                    compteurQuestionEtiquette +=1
            if(compteurQuestionEtiquette>0):
                questionParTag += ligne + """ entre <input type='number' width='30' name='""" + ligne[:-1] + """' value='0' max='""" + str(compteurQuestionEtiquette) + """' min='0'> et <input type='number' name='""" + ligne[:-1] + """' value='0' max='""" + str(compteurQuestionEtiquette) + """' min='0'> maximum = """ + str(compteurQuestionEtiquette) + """<br><br>"""
            else:
                questionParTag += """<input type='hidden' name='""" + ligne[:-1] + """' value='0' max='0' min='0'>"""+"""<input type='hidden' name='""" + ligne[:-1] + """' value='0' max='0' min='0'>"""

    return render_template("pageControle.html",questionParTag=questionParTag)




@app.route('/Home/pageDeQuestions/<nom_page>', methods=['POST', 'GET'])
def genererPage(nom_page):
    if request.method == 'POST':
        check_questions = []
        titre = request.form["titre"]
        checked = request.form.getlist("check")

        for i in range(len(checked)):

            with open(question_file) as file:
                data=json.load(file)
                questions=data["questions"]
        
            check_questions.append(questions[int(checked[i])-1])

        nbQuestions = len(check_questions)

        return render_template("getPage.html", titre=titre, nbQuestions=nbQuestions, questions=check_questions)






#Boizux Jatigt

@app.route('/Home/compteEtudiants')
def compteEtudiants():
    return render_template("compteEtudiant.html")

@app.route('/Home/compteEtudiants/creer', methods=["POST","GET"])
def inscrireEtudiant():

    if request.method == "POST":
        if 'file' not in request.files: # verifie si le post du formulaire renvoyer un fichier
            return redirect(url_for("home"))
        
        fichierCSV=request.files["file"]
        

        #if fichierCSV.filename == '':  # verifie si un fichier avec un nom a etait selectionner
        #    return render_template("home.html",message="fichier non selectionner")

        filename = secure_filename(fichierCSV.filename)#fonction qui verifie si le fichier n'essaye pas de modifier un fichier system

        with open(filename,"r") as file:

            csvreader = csv.reader(file)

            for row in csvreader: 
                dict = {"Nom": row[0], "Prenom": row[1], "Numero Etudiant": row[2]}

                with open(etudiants_file) as f:
                      data=json.load(f)
                      existe=False
                      for etudiant in data["Etudiants"]:
                        if row[2] == etudiant["Numero Etudiant"]:
                            existe=True
                      if existe==False:
                        data["Etudiants"].append(dict)
                      with open(etudiants_file, 'w') as f:
                        json.dump(data,f,indent='\t')
  
        return redirect(url_for('home'))    

# fonction de génération
def generate_id(n, alphabet):
    id = ''
    for i in range(n):
        id += choice( alphabet )
        
    return id

# fonction génération id formaté
def generate_id_formated(alphabet):
    id = ''
    for i in range(2):
        for j in range(5):
            id += choice( alphabet )
    return id
 
@app.route('/Home/Question/DiffuserQuestion<numQuestion>', methods=['POST', 'GET'])
def diffuserquestion(numQuestion):
    if request.method=='POST':

        questions = []
        with open(questionDiffusée_file) as file:
            questions=json.load(file)
            

        with open(question_file) as file:
            databis=json.load(file)
            dict = databis["questions"][int(numQuestion)-1]
            
        questions.append(dict)

        with open(questionDiffusée_file, 'w') as file:
            json.dump(questions,file,indent='\t')


        return render_template("getQuestionDiffusée.html", question = dict, numQuestion= str(numQuestion))

                

    return redirect(url_for('home'))

        
@app.route('/supprimerQuestionDiffusée/<idQuestion>', methods=['POST', 'GET'])
def supprimerQuestionDiffusée(idQuestion):
#Je supprime la question diffusée dont le numéro est passé dans l'url
    if request.method=='POST':
        with open(questionDiffusée_file) as file:
            data=json.load(file)
            del data[len(data)-1]

        with open(questionDiffusée_file, 'w') as file:
            json.dump(data, file, indent='\t')

        return redirect(url_for('home'))

    else :
        return redirect(url_for('home'))





@app.route('/Home/listeQuestions', methods=['POST', 'GET'])
def listeQuestions():

    formulaire = nouvelleQuestion()
    formulaire.etiquettes.choices=getEtiquettes()

    listeTags=[]
    with open(etiquette_file) as tags:

        if request.method == "GET":
            for ligne in tags.readlines():
                listeTags.append(ligne[:-1])
        else:
            eti=request.form.getlist("etiquettes")
            for t in eti:
                listeTags.append(t[:-2])

    with open(question_file) as file:
        data=json.load(file)

    codeQuestionHtml = ""
    for i in range(len(data["questions"])):
        for j in (data["questions"][i]["etiquettes"]):
            if j in listeTags:
                codeQuestionHtml = codeQuestionHtml + "<a href='/Home/Question/" + str(i+1) + "'>Question" + str(i+1) + "</a><br>"
                break

    return render_template("listeQuestions.html", balisesQuestions=codeQuestionHtml, form=formulaire)


          

@socketio.on('maj')
def handle_maj(msg):
    socketio.emit("MiseAJour",msg)



if __name__=="__main__":
    socketio.run(app)      


    
#app.run(host='0.0.0.0', port=81, debug=True)
