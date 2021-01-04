import ast as ast
import json
import inflection

filename = "../regimes/regime.py"
with open(filename, encoding='utf-8') as f:
    code = f.read()
input_tree = ast.parse(code)
output_tree = ast.Module(body=[], type_ignores=[])
for i in range(0, len(input_tree.body)):
    node = input_tree.body[i]
    print(type(node))
    if type(node) == ast.ClassDef and "Regime" in node.name :
        for j in range (0, len(node.body)):
            el = node.body[j]
            print(type(el))
            if type(el)== ast.ClassDef:
                el.name = str(inflection.underscore(node.name) + "_" + el.name)
                print(el.name)
                output_tree.body.append(el)
            else:
                output_tree.body.append(el)
    else : 
        output_tree.body.append(node)

output_code = ast.unparse(output_tree)
with open ("result_classes_flattened.py", "w") as file:
    file.write(output_code)