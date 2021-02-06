"""Generate openfisca variables of pension scheme."""


import ast as ast
import copy
import inflection
import json
import os
import pkg_resources
from pprint import pprint



france_pension_root =  pkg_resources.get_distribution("openfisca-france-pension").location
input_filename = os.path.join(
    france_pension_root,
    "openfisca_france_pension",
    "regimes",
    "regime.py"
    )

output_path = os.path.join(
    france_pension_root,
    "openfisca_france_pension",
    "scripts_ast"
    )


def modify_formula_function (node_body_element, regime_name):
    """Modifies the formula of Variable objects according to a regime ame

    Args:
        node_body_element ([type]): [description]
        regime_name (str): The regime name

    Returns:
        [type]: The modified formula
    """
    el = copy.deepcopy(node_body_element)
    if type(el)== ast.ClassDef :
        for i in range (0, len(el.body)):
            if type(el.body[i]) == ast.FunctionDef:
            #if type(el.body[i]) == ast.FunctionDef and "individu" in el.body[i].args:
            #if type(el.body[i]) == ast.FunctionDef and "formula" in el.body[i].name:
                print("found function: ", el.body[i].name)
                for j in range (0, len(el.body[i].body)):
                    if type(el.body[i].body[j]) == ast.Assign :
                        valeur = el.body[i].body[j].value
                        while type(valeur) != ast.Call and valeur != None:
                            valeur = valeur.value
                            if type(valeur)== ast.Attribute and valeur.attr == "regime_name":
                                print("found regime_name to replace: ", valeur.attr,"=>", regime_name)
                                valeur.attr = regime_name
                        if type(valeur) == ast.Call:
                            arguments = valeur.args
                            for arg in arguments:
                                if type(arg) == ast.Constant and str(arg.value).startswith("regime_name"):
                                    new_arg_value = arg.value.replace("regime_name", regime_name)
                                    print("found argument to modify:", str(arg.value), "=>", new_arg_value )
                                    arg.value = new_arg_value

    return el


if __name__ == "__main__":
    with open(input_filename, encoding='utf-8') as file:
        input_string = file.read()

    # parser le texte du fichier en structure logique de type AST
    input_ast_tree = ast.parse(input_string)

    # pour afficher un arbre AST faire une commande
    # print(ast.dump(input_ast_tree, indent=4))

    # créer un nouveau arbre AST vide qui va contenir le nouveau code
    output_ast_tree = ast.Module(body=[], type_ignores=[])


    ######################################################################################################
    # Créer un dictionnaire de l'heritage pour tous les régimes pour pouvoir recopier les classes heritées
    ######################################################################################################

    inheritance_dict = {}
    # pour chaque element du body de l'arbre ast
    for i in range(0, len(input_ast_tree.body)):
        node = input_ast_tree.body[i]
        # si cet element est une classe et son nom contien le mot Regime
        if type(node) == ast.ClassDef and "Regime" in node.name:
            # copier les classes internes
            inheritance_dict[node.name] = {}
            inheritance_dict[node.name]['variables'] = {}
            for el in node.body:
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
    regime_name = "regime"
    # Pour tous les Régimes (les elements du code de type class dont le nom contient le mot Regime) et si la classe n'est pas "abstraite"
    for node in input_ast_tree.body:
        if type(node) == ast.ClassDef and "Regime" in node.name :
            regime = copy.deepcopy(node)
            regime_name = str(inflection.underscore(node.name))
            # si la classe étend une autre classe
            extends = inheritance_dict[regime.name]['extends']
            print(regime.name, "extends", extends)
            if extends != "object" :
                # tant que la classe étend une autre (et ainsi de suite recursivement)
                while extends != "object":
                    superRegime = inheritance_dict[extends]
                    inheritedClasses = superRegime['variables']
                    for key, value in inheritedClasses.items():
                        # copier le contenu de la classe
                        el =  copy.deepcopy(value)
                        # modifier le nom de la classe en ajoutant le prefix avec le nom du regime
                        el.name = str(inflection.underscore(node.name) + "_" + el.name)
                        print("\nINHERITED class new name: ", key, "=>", el.name)
                        el = modify_formula_function (el, regime_name)
                        output_ast_tree.body.append(el)
                    extends = inheritance_dict[extends]['extends']
                # copier ses propres classes
                for j in range (0, len(regime.body)):
                    el = copy.deepcopy(regime.body[j])
                    if type(el)== ast.ClassDef:
                        new_class_name = str(inflection.underscore(node.name) + "_" + el.name)
                        print("\nOWN CLASS new name: ", el.name, "=>", new_class_name)
                        el.name = new_class_name
                        el = modify_formula_function (el, regime_name)
                        output_ast_tree.body.append(el)

                    # copier les attributs de la classe (pas copier si pas besoin)
                    #else:
                        #output_ast_tree.body.append(el)
        # copier les imports du fichier
        else :
            output_ast_tree.body.append(node)

    # pour afficher le nouveau arbre AST faire une commande
    # print(ast.dump(output_ast_tree, indent=4))

    # convertir la structure logique de l'arbre AST en code python formatté (type string)
    output_string = ast.unparse(output_ast_tree)

    output_filename = os.path.join(
        output_path,
        "result_file_" + regime_name + ".py",
        )
    # sauvegarder
    with open (output_filename, "w") as file:
        file.write(output_string)

    print("Result saved as ", output_filename)