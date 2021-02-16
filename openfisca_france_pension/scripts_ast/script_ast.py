"""Generate openfisca variables of pension scheme."""

import ast as ast
import copy
import logging
import os
import pkg_resources
from pprint import pprint
import sys

log = logging.getLogger(__name__)


france_pension_root =  pkg_resources.get_distribution("openfisca-france-pension").location


def modify_formula_function(node_body_element, parameters_prefix, variable_prefix):
    """Modifies the formula of Variable objects according to a regime name.

    Args:
        node_body_element ([type]): [description]
        regime_name (str): The regime name

    Returns:
        [type]: The modified formula
    """
    el = copy.deepcopy(node_body_element)
    if type(el)== ast.ClassDef :
        for node in el.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('formula'):
                log.debug(f"found formula: {node.name}")
                for sub_node in node.body:
                    if isinstance(sub_node, ast.Assign):
                        valeur = sub_node.value
                        while not isinstance(valeur, ast.Call) and valeur is not None and hasattr(valeur, "value"):
                            valeur = valeur.value
                            if isinstance(valeur, ast.Attribute) and valeur.attr == "regime_name":
                                log.debug(f"found regime_name to replace: {valeur.attr} => {parameters_prefix}")
                                valeur.attr = parameters_prefix
                        if type(valeur) == ast.Call:
                            arguments = valeur.args
                            for arg in arguments:
                                if type(arg) == ast.Constant and str(arg.value).startswith("regime_name"):
                                    new_arg_value = arg.value.replace("regime_name", variable_prefix)
                                    log.debug(f"found argument variable to modify: {arg.value} => {new_arg_value}")
                                    arg.value = new_arg_value

    return el


def get_regime_attribute(regime_node, attribute):
    """Gets regime attribute.

    Args:
        regime_node (ast.ClassDef): regime node
        attribute (str): attrbute name

    Returns:
        [Any]: the attribute value
    """
    assert (
        isinstance(regime_node, ast.ClassDef)
        and "Regime" in regime_node.name
        and "Abstract" not in regime_node.name
        ), f"{regime_node.name} is not a valid regime"
    for sub_node in regime_node.body:
        if isinstance(sub_node, ast.Assign):
            for target in sub_node.targets:
                if target.id == attribute:
                    assert isinstance(sub_node.value, ast.Constant), f"{sub_node.value} is not a constant"
                    return sub_node.value.value

    return None

def create_regime_variables(input_string, output_filename):
    """Creates regime variables.

    Args:
        input_string (str): String to be processed by ast
        output_filename (path): Destination of created variables code
    """
    # parser le texte du fichier en structure logique de type AST
    input_ast_tree = ast.parse(input_string)

    # pour afficher un arbre AST faire une commande
    # print(ast.dump(input_ast_tree, indent=4))

    # créer un nouveau arbre AST vide qui va contenir le nouveau code
    output_ast_tree = ast.Module(body=[], type_ignores=[])

    # Créer un dictionnaire de l'heritage pour tous les régimes pour pouvoir recopier les classes heritées
    inheritance_dict = {}
    # pour chaque element du body de l'arbre ast
    for i in range(0, len(input_ast_tree.body)):
        node = input_ast_tree.body[i]
        # si cet element est une classe et son nom contien le mot Regime
        if type(node) == ast.ClassDef and "Regime" in node.name:
            # copier les classes internes (variables)
            inheritance_dict[node.name] = {}
            inheritance_dict[node.name]['variables'] = {}
            for el in node.body:
                if type(el)== ast.ClassDef:
                    inheritance_dict[node.name]['variables'][el.name]= copy.deepcopy(el)
            # identifier la classe superieure et la sauvegarder sous la cle "extends"
            inheritance_dict[node.name]['extends'] = node.bases[0].id

    # pour afficher le contenu du dictionnaire de l'heritage
    # pprint(inheritance_dict)

    # Remplir le nouveau arbre AST avec les classes applatties
    variable_prefix = "regime"
    # Pour tous les Régimes (les elements du code de type class dont le nom contient le mot Regime) et si la classe n'est pas "abstraite"
    for node in input_ast_tree.body:
        if type(node) == ast.ClassDef and "Regime" in node.name:
            if "Abstract" in node.name:
                continue
            regime = copy.deepcopy(node)

            variable_prefix = get_regime_attribute(regime, "variable_prefix")
            # si la classe étend une autre classe
            extends = inheritance_dict[regime.name]['extends']
            log.debug(regime.name, "extends", extends)
            if extends != "object" :
                # tant que la classe étend une autre (et ainsi de suite recursivement)
                while extends != "object":
                    superRegime = inheritance_dict[extends]
                    inheritedClasses = superRegime['variables']
                    for key, value in inheritedClasses.items():
                        # copier le contenu de la classe
                        el =  copy.deepcopy(value)
                        # modifier le nom de la classe en ajoutant le variable_prefix avec le nom du regime
                        parameters_prefix = get_regime_attribute(regime, "parameters_prefix")
                        variable_prefix = get_regime_attribute(regime, "variable_prefix")
                        el.name = variable_prefix + "_" + el.name
                        log.debug(f"\nINHERITED class new name: {key} => {el.name}")
                        el = modify_formula_function(el, parameters_prefix = parameters_prefix, variable_prefix = variable_prefix)
                        output_ast_tree.body.append(el)
                    extends = inheritance_dict[extends]['extends']
                # copier ses propres classes
                for j in range (0, len(regime.body)):
                    el = copy.deepcopy(regime.body[j])
                    if type(el)== ast.ClassDef:
                        parameters_prefix = get_regime_attribute(regime, "parameters_prefix")
                        variable_prefix = get_regime_attribute(regime, "variable_prefix")
                        new_class_name = variable_prefix + "_" + el.name
                        log.debug(f"\nOWN CLASS new name: {el.name} => {new_class_name}")
                        el.name = new_class_name
                        el = modify_formula_function(el, parameters_prefix = parameters_prefix, variable_prefix = variable_prefix)
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

    # sauvegarder
    with open (output_filename, "w") as file:
        file.write(output_string)

    print("Result saved as ", output_filename)


def main(verbose = False):
    regime_de_base = os.path.join(
        france_pension_root,
        "openfisca_france_pension",
        "regimes",
        "regime.py"
        )

    regime_general_cnav = os.path.join(
        france_pension_root,
        "openfisca_france_pension",
        "regimes",
        "regime_general_cnav.py"
        )


    input_file_names = [
        regime_de_base,
        regime_general_cnav,
        ]
    input_string = ""

    for input_filename in input_file_names:
        with open(input_filename, encoding='utf-8') as file:
            input_string += "\n" + file.read()

    output_filename = os.path.join(
        france_pension_root,
        "openfisca_france_pension",
        "variables",
        "regime_general_cnav.py"
        )

    logging.basicConfig(level = logging.DEBUG if verbose else logging.WARNING, stream = sys.stdout)
    create_regime_variables(input_string, output_filename)



if __name__ == "__main__":
    main(verbose = True)