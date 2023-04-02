$(document).ready(function(){
    var max_propositions      = 5;
    var wrapper         = $("#inputsWrapper") ;
    var add_button      = $("#add_button");
    var checkbox_wrap   = $("#propositions");

    var x = wrapper.length;
    var counter = 0;

    $(add_button).click(function(e) {
        if (x<max_propositions) 
        {
            let html = '<div class="control block">Proposition '+x+' <input type="checkbox" id="prop'+x+'" name="prop[]" value="'+x+'"> cocher si la proposition est correcte<input class="input proposition" type="text" placeholder="Ajouter proposition" name="proposition[]" id="proposition'+x+'"><button class="delete is-large" id="remove_button" name="remove_button" type="button" value=""></button></div>'
            $(wrapper).append(html);
            var checkbox = document.createElement("INPUT");
            var p_checkbox = document.createElement("p");
            p_checkbox.setAttribute("id", "checkbox"+x);
            p_checkbox.appendChild(checkbox);
            checkbox.setAttribute("type", "checkbox");
            checkbox_wrap.append(p_checkbox);
            counter++;
            x++;
            //console.log(counter);
        }
    }) 

    $(document).on('click', '#remove_button', function() {
        if (x>1) {
            let e = document.getElementById("propositions").lastElementChild;
            if (e!=null)  e.remove();
            $(this).parent('div').remove();
            x--;
            counter--;
            //console.log(counter);
        }
        return false;
    });

    $(wrapper).on('input','input', function() {
        if (x>1) {
            let text = '<input type="checkbox">';
            let count = document.getElementById("propositions").children.length;
            console.log(count);
            document.getElementById("checkbox"+count).innerHTML = text + document.getElementById("proposition"+count).value;        
        }
    });

    $(document).on('keyup', '#enonce', function () {
        document.getElementById("enonce-output").innerHTML=document.getElementById("enonce").value;
    });

    $("#etiquettes").on('change', function() {
        var affiche= [];
        const myDiv = $("#etiquette-display");
        myDiv.empty();
        for (var option of document.getElementById("etiquettes")) {
            if (option.selected && (!affiche.includes(option.value))) {
                let html = '<button class="button is-info" type="button">'+option.value+'</button>';
                myDiv.append(html);
                affiche.push(option.value);
            }
        }
    });

    $("#questions").on('keyup', function () {
        var checked = $('input[type=checkbox]:checked');
        var int_checked = new Array();
        for (var check of checked) {
            int_checked.push(parseInt(check.getAttribute("id").slice(-1)));
        }
        console.log(int_checked);
    });

    $("#titre").on('change', function() {
        titre = $("#titre").val();
        form = $("#form");
        new_titre = titre.replace(" ", "-");
        form.attr("action", "/Home/pageDeQuestions/"+new_titre);
    });

});
/* C'est la fonction qui permet de rajouter et supprimer des propositions */

