"""Generate openfisca variables of pension scheme."""

import ast as ast
import copy
import logging
import os
import pkg_resources
import sys


from openfisca_france_pension.regimes.regime import AbstractRegime, AbstractRegimeDeBase

log = logging.getLogger(__name__)


france_pension_root = pkg_resources.get_distribution("openfisca-france-pension").location


class RewriteRegimeFormula(ast.NodeTransformer):
    parameters_prefix = None
    variable_prefix = None

    def __init__(self, parameters_prefix, variable_prefix):
        self.parameters_prefix = parameters_prefix
        self.variable_prefix = variable_prefix

    def visit_Attribute(self, node):
        node = self.generic_visit(node)
        if type(node.attr) == str and node.attr.startswith("regime_name"):
            new_attr = node.attr.replace("regime_name", self.parameters_prefix)
            log.debug(f"Found attribute to replace: {node.attr} => {new_attr}")
            node.attr = new_attr
        return node

    def visit_Constant(self, node):
        # Useless: node = self.generic_visit(node), because a constant has no
        # sub-tree to visit.
        if type(node.value) == str and node.value.startswith("regime_name"):
            new_value = node.value.replace("regime_name", self.variable_prefix)
            log.debug(f"Found parameter to replace: {node.value} => {new_value}")
            node.value = new_value
        return node


class RewriteRegimeVariableClass(ast.NodeTransformer):
    parameters_prefix = None
    variable_prefix = None

    def __init__(self, parameters_prefix, variable_prefix):
        self.parameters_prefix = parameters_prefix
        self.variable_prefix = variable_prefix

    def visit_ClassDef(self, node):
        node.name = self.variable_prefix + "_" + node.name
        node = self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        if node.name.startswith("formula"):
            log.debug(f"Found formula: {node.name}")
            node = RewriteRegimeFormula(self.parameters_prefix, self.variable_prefix).visit(node)
        else:
            node = self.generic_visit(node)
        return node


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
    for node in input_ast_tree.body:
        # si cet element est une classe et son nom contien le mot Regime
        if type(node) == ast.ClassDef and "Regime" in node.name:
            # copier les classes internes (variables)
            inheritance_dict[node.name] = {}
            inheritance_dict[node.name]['variables'] = {}
            for el in node.body:
                if type(el) == ast.ClassDef:
                    inheritance_dict[node.name]['variables'][el.name] = copy.deepcopy(el)
            # identifier la classe superieure et la sauvegarder sous la cle "extends"
            inheritance_dict[node.name]['extends'] = node.bases[0].id

    # pour afficher le contenu du dictionnaire de l'heritage
    # pprint(inheritance_dict)

    # Remplir le nouveau arbre AST avec les classes applatties
    # Pour tous les Régimes (les elements du code de type class dont le nom contient le mot Regime) et si la classe n'est pas "abstraite"
    for node in input_ast_tree.body:
        if type(node) == ast.ClassDef and "Regime" in node.name:
            if "Abstract" in node.name:
                continue
            regime = node
            parameters_prefix = get_regime_attribute(regime, "parameters_prefix")
            variable_prefix = get_regime_attribute(regime, "variable_prefix")
            # si la classe étend une autre classe
            extends = inheritance_dict[regime.name]['extends']
            # log.debug(regime.name, "extends", extends)
            if extends != "object":
                # tant que la classe étend une autre (et ainsi de suite recursivement)
                while extends != "object":
                    superRegime = inheritance_dict[extends]
                    inheritedClasses = superRegime['variables']
                    for key, value in inheritedClasses.items():
                        el = copy.deepcopy(value)
                        el = ast.fix_missing_locations(RewriteRegimeVariableClass(parameters_prefix, variable_prefix).visit(el))
                        output_ast_tree.body.append(el)
                    extends = inheritance_dict[extends]['extends']
                # copier ses propres classes
                for el in regime.body:
                    if type(el) == ast.ClassDef:
                        el = copy.deepcopy(el)
                        el = ast.fix_missing_locations(RewriteRegimeVariableClass(parameters_prefix, variable_prefix).visit(el))
                        output_ast_tree.body.append(el)
        else:
            output_ast_tree.body.append(node)

    # pour afficher le nouveau arbre AST faire une commande
    # print(ast.dump(output_ast_tree, indent=4))

    # convertir la structure logique de l'arbre AST en code python formatté (type string)
    output_string = ast.unparse(output_ast_tree)

    # sauvegarder
    with open(output_filename, "w") as file:
        file.write(output_string)

    log.info(f"Result saved as {output_filename}")


def main(verbose = False):
    regime_de_base = os.path.join(
        france_pension_root,
        "openfisca_france_pension",
        "regimes",
        "regime.py"
        )

    regimes_files_by_name = {
        name : {
            "input": os.path.join(
                france_pension_root,
                "openfisca_france_pension",
                "regimes",
                f"{name}.py"
                ),
            "output": os.path.join(
                france_pension_root,
                "openfisca_france_pension",
                "variables",
                f"{name}.py"
                )
            }
        for name in ['regime_general_cnav', 'fonction_publique']
        }

    # regime_general_cnav = os.path.join(
    #     france_pension_root,
    #     "openfisca_france_pension",
    #     "regimes",
    #     "regime_general_cnav.py"
    #     )

    # fonction_publique = os.path.join(
    #     france_pension_root,
    #     "openfisca_france_pension",
    #     "regimes",
    #     "fonction_publique.py"
    #     )

    for regime_name, regime_files in regimes_files_by_name.items():
        print(regime_name)
        print(regime_files)
        input_file_names = [
            regime_de_base,
            regime_files['input'],
            ]
        input_string = ""
        for input_filename in input_file_names:
            with open(input_filename, encoding='utf-8') as file:
                input_string += "\n" + file.read()

        logging.basicConfig(level = logging.DEBUG if verbose else logging.WARNING, stream = sys.stdout)
        create_regime_variables(input_string, regime_files['output'])


if __name__ == "__main__":
    main(verbose = True)
