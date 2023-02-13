import os, json
from flask import Flask, redirect, render_template, request, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from form import nouvelleQuestion


basedir = os.path.abspath(os.path.dirname(__file__))
user_file = os.path.join(basedir, 'static/js/users.json')
etiquette_file = os.path.join(basedir, 'static/txt/etiquettes.txt')
question_file = os.path.join(basedir, 'static/js/questions.json')


app = Flask(__name__)
app.secret_key = "any random string"

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

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method=='POST':
        
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

#Je recupère le nom de l'utilisateur pour initier la session

        with open(user_file) as file:
            data = json.load(file)
            for user in data["users"]:
                if user["email"]==email:
                    session['username']=user["name"]

#Je vérifie si l'email et le mot de passe saisis existe dans users.json
# Sinon j'envoie un message à afficher

        with open (user_file) as file:
            data=json.load(file)
            for user in data["users"]:
                if user["email"]==email and check_password_hash(user["password"], password):
                    return redirect(url_for('home'))
        
        flash('Please check your login details and try again.')
        return  render_template("login.html")

        

    else :
        return render_template("login.html")
        
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
        dict = {"enonce" : enonce, "propositions" : propostions, "etiquettes" : etiquettes}
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

check_questions = []

@app.route('/Home/pageDeQuestions')
def pageQuestions():
#Je crée une page avec tout les questions pour en choisir et génerer une page de questions  
    form = nouvelleQuestion()
    form.etiquettes.choices=getEtiquettes()
    with open(question_file) as file:
        data=json.load(file)
        questions=data["questions"]
        
    nb_Questions=len(questions)

    if request.method == 'POST':
        checked = request.form.getlist("check")
        for i in range(len(checked)):
            if checked[i]=="on":
                check_questions.append(i)
        print(checked)

    return render_template("pageQuestions.html", questions=questions, nb_Questions=nb_Questions)  

@app.route('/Home/pageDeQuestions/<nom_page>')
def genererPage():
    print("goog")
    
app.run(host='0.0.0.0', port=81, debug=True)