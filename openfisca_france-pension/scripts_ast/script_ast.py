import ast as ast
import json
import inflection
import copy
from pprint import pprint

input_filename = "../regimes/regime.py"
output_filename = "result_output_with_modify_formula.py"

with open(input_filename, encoding='utf-8') as file: 
    input_string = file.read()

# parser le texte du fichier en structure logique de type AST
input_ast_tree = ast.parse(input_string)
# pour afficher un arbre AST faire une commande 
# print(ast.dump(input_ast_tree, indent=4))

# creer un nouveau arbre AST vide qui va contenir le nouveau code
output_ast_tree = ast.Module(body=[], type_ignores=[])

# Creer une fonction pour modifier les formules choisies

def modify_formula_function (node_body_element, regime_name):
    el = copy.deepcopy(node_body_element)
    if type(el)== ast.ClassDef and "decote" in el.name :
        for i in range (0, len(el.body)):
            if type(el.body[i]) == ast.FunctionDef and "formula" in el.body[i].name:
                el.body[i].body[1].value.value.value.attr = regime_name
                el.body[i].body[2].value.args[0].value = regime_name +"_"+ el.body[i].body[2].value.args[0].value
                # print(el.body[i].body[2].value.args[0].value)
    if type(el) == ast.ClassDef and "pension_brute" in el.name:
        for i in range (0, len(el.body)):
            if type(el.body[i]) == ast.FunctionDef and "formula" in el.body[i].name:
                for j in range (0, 3):
                    el.body[i].body[j].value.args[0].value = regime_name +"_"+ el.body[i].body[j].value.args[0].value
                    # print(el.body[i].body[j].value.args[0].value)
    if type(el) == ast.ClassDef and "cotisation_retraite" in el.name:
        for i in range (0, len(el.body)):
            if type(el.body[i]) == ast.FunctionDef and "formula" in el.body[i].name:
                el.body[i].body[0].value.args[0].value = regime_name +"_"+ el.body[i].body[0].value.args[0].value
    if type(el) == ast.ClassDef and "taux_de_liquidation" in el.name:
        for i in range (0, len(el.body)):
            if type(el.body[i]) == ast.FunctionDef and "formula" in el.body[i].name:
                for j in range (0, 2):
                    el.body[i].body[j].value.args[0].value = regime_name +"_"+ el.body[i].body[j].value.args[0].value
                    # print(el.body[i].body[j].value.args[0].value)
                
    return el

######################################################################################################
# Créer un dictionnaire de l'heritage pour tous les régimes pour pouvoir recopier les classes heritées
######################################################################################################

inheritance_dict={}
# pour chaque element du body de l'arbre ast
for i in range(0, len(input_ast_tree.body)):
    node = input_ast_tree.body[i]
    # si cet element est une classe et son nom contien le mot Regime
    if type(node) == ast.ClassDef and "Regime" in node.name:
        # copier les classes internes
        inheritance_dict[node.name] = {}
        inheritance_dict[node.name]['variables'] = {}
        for j in range (0, len(node.body)):
            el = node.body[j]
            if type(el)== ast.ClassDef:
                inheritance_dict[node.name]['variables'][el.name]= copy.deepcopy(el)
                # print("new variable added =", el.name, "\n", ast.dump(el))
        # identifier la classe superieure et la sauvegarder sous la cle "extends"
        inheritance_dict[node.name]['extends'] = node.bases[0].id

# pour afficher le contenu du dictionnaire de l'heritage
# pprint(inheritance_dict)

##############################################################################
# Remplir le nouveau arbre AST avec les classes applatties
##############################################################################

# Pour tous les Régimes (les elements du code de type class dont le nom contient le mot Regime) et si la classe n'est pas "abstraite"
for i in range(0, len(input_ast_tree.body)):
    node = input_ast_tree.body[i]
    if type(node) == ast.ClassDef and "Regime" in node.name :
        regime = copy.deepcopy(node)
        regime_name = str(inflection.underscore(node.name))
        # si la classe étend une autre classe
        extends = inheritance_dict[regime.name]['extends']
        print(regime.name, "extends", extends)
        if extends != "object" :
            # tanque la classe étend une autre (et ainsi de suite recursivement)
            while extends != "object":
                superRegime = inheritance_dict[extends]
                inheritedClasses = superRegime['variables']
                for key, value in inheritedClasses.items():
                    print("inherited class =", key)
                    # copier le contenu de la classe
                    el =  copy.deepcopy(value)
                    el = modify_formula_function (el, regime_name)
                    # modifier le nom de la classe en ajoutant le prefix avec le nom du regime
                    el.name = str(inflection.underscore(node.name) + "_" + el.name)
                    output_ast_tree.body.append(el)
                extends = inheritance_dict[extends]['extends']  
            # copier ses propres classes 
            for j in range (0, len(regime.body)):
                el = copy.deepcopy(regime.body[j])
                if type(el)== ast.ClassDef:
                    el = modify_formula_function (el, regime_name)
                    el.name = str(inflection.underscore(node.name) + "_" + el.name)
                    output_ast_tree.body.append(el)           
    # copier tous les autres element du code dans l'ordre d'apparution (dont les imports), sans les modifier
    # else : 
            #output_ast_tree.body.append(node)
            
# pour afficher le nouveau arbre AST faire une commande 
# print(ast.dump(output_ast_tree, indent=4))

# convertir la structure logique de l'arbre AST en code python formatté (type string)
output_string = ast.unparse(output_ast_tree)

# sauvegarder 
with open (output_filename, "w") as file:
    file.write(output_string)

print("Result saved as ", output_filename)